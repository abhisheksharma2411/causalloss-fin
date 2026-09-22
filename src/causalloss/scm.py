"""The causal model: replay a FinalityBench episode in a counterfactual world.

Two kinds of intervention are available, and having both is the point of this
paper. Prior counterfactual attribution for agent failures intervenes on the
agent's own steps only; in an environment where the infrastructure is itself a
causal agent, such a method has no variable to blame except the agent.

    do(fault instance absent)   rebuild the delivery schedule without it and
                                re-run the same policy on the same case
    do(A_k = a')                replace the agent's k-th action and let the
                                policy carry on from there

Both are exact rather than sampled. A FinalityBench episode is a pure function
of (case, seed, policy, schedule), so common random numbers come for free: two
worlds that differ in one repaired message differ in nothing else.

**The decomposition.** Writing ``w`` for the factual world, ``w0`` for the same
case with every fault repaired, and ``pi*`` for the best policy that uses no
privileged information, a policy's loss splits exactly three ways:

    L(pi, w) = [L(pi,w) - L(pi,w0)]  +  [L(pi,w0) - L(pi*,w0)]  +  L(pi*,w0)
                 infrastructure            policy                  irreducible

The terms telescope, so there is no residual to hide a modelling error in. The
first term is what the faults cost this policy and is distributed over
individual messages by Shapley value; the second is what a better policy would
have saved in a clean world; the third is what nobody without an oracle can
avoid -- on this corpus, almost entirely the cases whose outcome lands after
the ship-by deadline.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Sequence

from ._p1 import ensure_p1
from .faultgraph import FaultInstance, apply, extract

ensure_p1()

from finalitybench.config import STEP_BUDGET  # noqa: E402
from finalitybench.env import Action, Environment  # noqa: E402
from finalitybench.faults import FaultProfile  # noqa: E402
from finalitybench.outcome import Position  # noqa: E402
from finalitybench.policies import FinalityOracle, Policy, TransactionalRuntimePolicy  # noqa: E402
from finalitybench.projections import SystemViews  # noqa: E402
from finalitybench.world import Case  # noqa: E402


class _Override(Policy):
    """Run ``inner``, but force a chosen action at one step.

    This is the ``do`` operator on an agent decision. After the forced step the
    inner policy continues on its own, seeing the consequences of the
    substitution -- which is what makes it an intervention on the run rather
    than a rewrite of the whole trajectory.
    """

    def __init__(self, inner: Policy, step: int, action: Action) -> None:
        self._inner = inner
        self._step = step
        self._action = action
        self.name = f"{inner.name}@{step}"

    def reset(self, case: Case | None = None) -> None:
        self._inner.reset(case)
        self._k = 0

    def act(self, obs: dict[str, Any]) -> Action:
        chosen = self._action if self._k == self._step else self._inner.act(obs)
        self._k += 1
        return chosen


def run_in_world(case: Case, policy: Policy, profile: FaultProfile, seed: int,
                 instances: Iterable[FaultInstance], baseline) -> tuple[Environment, Position]:
    """Run one episode with the delivery schedule rebuilt from ``instances``."""
    env = Environment(case, profile=profile, seed=seed)
    env.schedule = apply(baseline, instances, profile)
    env.views = SystemViews(env.log, env.schedule)
    policy.reset(case)
    while not env.done and env.steps < STEP_BUDGET:
        env.step(policy.act(env.observe()))
    return env, env.finalize()


@dataclass
class Factual:
    """The episode as it actually happened, plus everything needed to replay it."""

    case: Case
    seed: int
    policy_name: str
    profile: FaultProfile
    instances: list[FaultInstance]
    baseline: Any
    reference_value: int
    factual_value: int
    clean_value: int
    best_clean_value: int
    trace: list[dict[str, Any]] = field(default_factory=list)

    @property
    def loss(self) -> int:
        """Excess loss against the finality-oracle reference, in cents."""
        return self.reference_value - self.factual_value

    @property
    def infrastructure(self) -> int:
        """What the faults cost this policy: L(pi,w) - L(pi,w0)."""
        return self.clean_value - self.factual_value

    @property
    def policy_gap(self) -> int:
        """What a better policy would have saved in a clean world."""
        return self.best_clean_value - self.clean_value

    @property
    def irreducible(self) -> int:
        """What no unprivileged policy avoids on this task."""
        return self.reference_value - self.best_clean_value

    def check(self) -> bool:
        """The three terms must sum to the loss. Telescoping, so exactly."""
        return self.infrastructure + self.policy_gap + self.irreducible == self.loss

    def terms(self) -> dict[str, int]:
        """The signed decomposition: infrastructure effect, policy differential,
        reference-policy residual, and the loss they sum to.

        Not called ``shares`` because two of the three go negative -- the
        infrastructure effect when faults help a policy on net, the policy
        differential whenever the subject beats the best implementable policy
        on a task -- and a share that can be negative is not a share. The word
        is kept for :meth:`World.shapley`, which divides the infrastructure
        effect into parts that do sum to it.
        """
        return {"infrastructure": self.infrastructure, "policy": self.policy_gap,
                "irreducible": self.irreducible, "total": self.loss}

    def shares(self) -> dict[str, int]:
        """Deprecated alias for :meth:`terms`, kept for the v1.0.0 API."""
        return self.terms()


class World:
    """A cached replay engine for one (case, seed, policy).

    Every attribution method below asks the same small set of counterfactual
    questions, so the answers are memoised. Shapley in particular revisits
    coalitions constantly, and without the cache an exact computation over
    thirteen instances would re-run the same episode thousands of times.
    """

    def __init__(self, case: Case, policy_factory: Callable[[], Policy], seed: int,
                 profile: FaultProfile | None = None,
                 reference_factory: Callable[[], Policy] | None = None,
                 best_factory: Callable[[], Policy] | None = None,
                 present: Sequence[FaultInstance] | None = None) -> None:
        self.case = case
        self.seed = seed
        self.profile = profile or FaultProfile()
        self._make = policy_factory
        self._make_ref = reference_factory or FinalityOracle
        self._make_best = best_factory or TransactionalRuntimePolicy
        extracted, self.baseline, _ = extract(case, seed, self.profile)
        # ``present`` restricts the world to a chosen subset of faults, which
        # is how a planted episode is replayed: the injected set is everything
        # that went wrong, so it is also everything there is to blame.
        self.instances = list(extracted if present is None else present)
        self._cache: dict[tuple, int] = {}
        self.replays = 0
        #: Terminal position of the privileged reference in the factual world.
        #: Excess loss is measured against this and it is held fixed across
        #: every counterfactual, so a repaired message moves the policy's
        #: position and nothing else.
        self.factual_reference = self.value(self.instances, self._make_ref(), tag="ref")

    # -- primitive queries -------------------------------------------------

    def value(self, keep: Sequence[FaultInstance] | None = None,
              policy: Policy | None = None, tag: str = "") -> int:
        """Terminal position with only ``keep`` faults present."""
        kept = self.instances if keep is None else list(keep)
        key = (tuple(sorted(i.ident for i in kept)), tag)
        if key in self._cache:
            return self._cache[key]
        _, position = run_in_world(self.case, policy or self._make(), self.profile,
                                   self.seed, kept, self.baseline)
        self.replays += 1
        self._cache[key] = position.value
        return position.value

    def factual(self) -> Factual:
        env, position = run_in_world(self.case, self._make(), self.profile, self.seed,
                                     self.instances, self.baseline)
        self.replays += 1
        reference = self.value(self.instances, self._make_ref(), tag="ref")
        clean = self.value([], tag="")
        best_clean = self.value([], self._make_best(), tag="best")
        return Factual(
            case=self.case, seed=self.seed, policy_name=self._make().name,
            profile=self.profile, instances=self.instances, baseline=self.baseline,
            reference_value=reference, factual_value=position.value,
            clean_value=clean, best_clean_value=best_clean,
            trace=[r.as_dict() for r in env.transcript],
        )

    # -- interventions -----------------------------------------------------

    def repair_effect(self, inst: FaultInstance) -> int:
        """Loss avoided by repairing one message, holding everything else fixed."""
        kept = [i for i in self.instances if i.ident != inst.ident]
        return self.value(kept) - self.value(self.instances)

    def agent_effect(self, step: int, alternatives: Sequence[Action]) -> tuple[int, Action | None]:
        """Loss avoided by the best alternative action at ``step``.

        Reported as a regret rather than a distribution shift: the policies here
        are deterministic, so resampling under the same policy -- the usual
        move -- changes nothing at all.
        """
        factual = self.value(self.instances)
        best, best_action = 0, None
        for alternative in alternatives:
            env, position = run_in_world(
                self.case, _Override(self._make(), step, alternative),
                self.profile, self.seed, self.instances, self.baseline)
            self.replays += 1
            gain = position.value - factual
            if gain > best:
                best, best_action = gain, alternative
        return best, best_action

    # -- Shapley over fault instances --------------------------------------

    def shapley(self, max_exact: int = 12, samples: int = 512,
                rng_seed: int = 0) -> dict[str, float]:
        """Distribute the infrastructure share across individual messages.

        The value of a coalition is the loss its members jointly cause:
        ``v(S) = value(no faults) - value(S)``. With ``v({}) = 0`` the Shapley
        values sum to ``v(all)``, which is exactly the infrastructure term of
        the decomposition -- so the split is complete by the efficiency axiom
        rather than by construction.

        Exact below ``max_exact`` instances, permutation-sampled above it.
        E3 reports how far the sampled values sit from the exact ones.
        """
        import random

        items = self.instances
        n = len(items)
        if n == 0:
            return {}
        clean = self.value([])

        def v(subset: Sequence[FaultInstance]) -> int:
            return clean - self.value(subset)

        phi = {i.ident: 0.0 for i in items}
        if n <= max_exact:
            for size in range(n):
                weight = 1.0
                for combo in itertools.combinations(range(n), size):
                    subset = [items[j] for j in combo]
                    base = v(subset)
                    for j in range(n):
                        if j in combo:
                            continue
                        marginal = v(subset + [items[j]]) - base
                        phi[items[j].ident] += marginal * _shapley_weight(n, size)
            return phi

        rng = random.Random(rng_seed)
        order = list(range(n))
        for _ in range(samples):
            rng.shuffle(order)
            running: list[FaultInstance] = []
            base = 0
            for j in order:
                running.append(items[j])
                nxt = v(running)
                phi[items[j].ident] += (nxt - base) / samples
                base = nxt
        return phi


def _shapley_weight(n: int, size: int) -> float:
    from math import factorial

    return factorial(size) * factorial(n - size - 1) / factorial(n)


#: The alternative actions considered at each agent step. Kept small and
#: meaningful: these are the dispositions an operator would recognise, not an
#: enumeration of the whole action space.
def alternatives_for(case: Case) -> list[Action]:
    return [
        Action("ship"),
        Action("close"),
        Action("escalate", {"reason": "counterfactual"}),
        Action("wait", {"ticks": 120}),
        Action("probe_processor", {"ref": case.pending_ref}),
        Action("retry_capture", {"idem_key": case.pending_ref}),
        Action("refund", {"amount": case.amount}),
    ]
