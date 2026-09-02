"""Attribution methods, from cheap heuristics to joint intervention.

Every method takes an episode and returns a ranked list of candidate causes
with scores, plus a verdict on whether the loss belongs to the agent or to the
infrastructure. They are graded against causes that were planted, not derived,
so no method is being scored against its own definition of truth.

The comparison that matters is ``AgentOnly`` against ``JointShapley``.
``AgentOnly`` is the shape of published counterfactual attribution for agent
failures -- intervene on the agent's steps, re-run forward, rank by the shift
in outcome. It is a good method. It also has no variable in its model except
the agent's choices, so when a dropped message is what actually cost the money,
the best it can do is name the step that acted on the missing information. The
experiments measure how often that happens and what it costs in allocation
error.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from ._p1 import ensure_p1
from .faultgraph import FaultInstance
from .scm import World, alternatives_for

ensure_p1()

from finalitybench.env import Action  # noqa: E402

AGENT = "agent"
INFRA = "infrastructure"


@dataclass
class Cause:
    ident: str
    kind: str            # AGENT or INFRA
    score: float         # cents of loss attributed
    label: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"ident": self.ident, "kind": self.kind,
                "score": round(self.score, 2), "label": self.label}


@dataclass
class Attribution:
    method: str
    causes: list[Cause]
    agent_share: float
    infra_share: float
    replays: int
    detail: dict[str, Any] = field(default_factory=dict)

    @property
    def top(self) -> Cause | None:
        return self.causes[0] if self.causes else None

    @property
    def verdict(self) -> str:
        """Which side the method thinks is mostly responsible."""
        if not self.causes:
            return AGENT if self.agent_share >= self.infra_share else INFRA
        return AGENT if self.agent_share > self.infra_share else INFRA

    def top_k(self, k: int) -> list[str]:
        return [c.ident for c in self.causes[:k]]

    def as_dict(self) -> dict[str, Any]:
        return {"method": self.method, "verdict": self.verdict,
                "agent_share": round(self.agent_share, 2),
                "infra_share": round(self.infra_share, 2),
                "replays": self.replays,
                "causes": [c.as_dict() for c in self.causes[:8]],
                "detail": dict(self.detail)}


# --- heuristics ------------------------------------------------------------

def last_action(world: World, trace: Sequence[dict[str, Any]]) -> Attribution:
    """Blame the last irreversible step. Cheap, and usually wrong.

    The step that executes a harmful action is rarely the step that decided on
    it, which is the observation that motivates intervention-based attribution
    in the first place.
    """
    irreversible = {"ship", "refund", "retry_capture", "write_off"}
    idx = next((i for i in range(len(trace) - 1, -1, -1)
                if trace[i]["tool"] in irreversible), None)
    if idx is None:
        idx = max(0, len(trace) - 1)
    loss = world.factual_reference - world.value(world.instances)
    return Attribution(
        "last_action",
        [Cause(f"step:{idx}", AGENT, float(loss), trace[idx]["tool"] if trace else "none")],
        agent_share=float(loss), infra_share=0.0, replays=0,
    )


def first_divergence(world: World, trace: Sequence[dict[str, Any]]) -> Attribution:
    """Blame the earliest message that arrived late or not at all.

    A reasonable operations reflex: find the first thing that looks wrong and
    call it the cause. It ignores whether that message mattered.
    """
    loss = world.factual_reference - world.value(world.instances)
    ordered = sorted(world.instances,
                     key=lambda i: (i.detail.get("at_t", i.detail.get("base_t", 0)), i.ident))
    if not ordered:
        return Attribution("first_divergence", [], agent_share=float(loss),
                           infra_share=0.0, replays=0)
    first = ordered[0]
    return Attribution(
        "first_divergence",
        [Cause(first.ident, INFRA, float(loss), first.describe())],
        agent_share=0.0, infra_share=float(loss), replays=0,
    )


# --- agent-only intervention (the published shape) -------------------------

def agent_only(world: World, trace: Sequence[dict[str, Any]],
               max_steps: int = 10) -> Attribution:
    """Intervene on agent steps only, and rank them by loss avoided.

    This is the method under comparison. It cannot name an infrastructure cause
    because its causal model contains no infrastructure variable, so every
    dollar it explains is charged to a step the agent took.
    """
    before = world.replays
    alts = alternatives_for(world.case)
    causes: list[Cause] = []
    for step in range(min(len(trace), max_steps)):
        gain, action = world.agent_effect(step, alts)
        if gain > 0:
            causes.append(Cause(f"step:{step}", AGENT, float(gain),
                                f"{trace[step]['tool']} -> {action.tool if action else '?'}"))
    causes.sort(key=lambda c: -c.score)
    total = float(world.factual_reference - world.value(world.instances))
    explained = causes[0].score if causes else 0.0
    return Attribution("agent_only", causes,
                       agent_share=float(min(explained, total)) if causes else total,
                       infra_share=0.0, replays=world.replays - before)


# --- fault-side methods ----------------------------------------------------

def fault_single(world: World) -> Attribution:
    """Repair each message on its own and rank by loss avoided.

    Scores every cause at zero whenever two faults are jointly but not
    individually sufficient, which is the failure mode the paired stratum is
    built to expose.
    """
    before = world.replays
    causes = []
    for inst in world.instances:
        effect = world.repair_effect(inst)
        if effect != 0:
            causes.append(Cause(inst.ident, INFRA, float(effect), inst.describe()))
    causes.sort(key=lambda c: -c.score)
    infra = float(world.value([]) - world.value(world.instances))
    return Attribution("fault_single", causes,
                       agent_share=0.0, infra_share=infra,
                       replays=world.replays - before)


def minimal_sufficient(world: World, max_size: int = 3) -> Attribution:
    """The smallest set of messages whose joint repair removes the loss.

    A but-for cause taken as a set rather than a singleton, in the spirit of
    the Halpern-Pearl treatment of actual causation: no member is a cause on
    its own, and together they are.
    """
    import itertools

    before = world.replays
    clean = world.value([])
    factual = world.value(world.instances)
    if clean == factual:
        return Attribution("minimal_sufficient", [], agent_share=0.0,
                           infra_share=0.0, replays=world.replays - before)

    items = world.instances
    for size in range(1, min(max_size, len(items)) + 1):
        for combo in itertools.combinations(items, size):
            kept = [i for i in items if i.ident not in {c.ident for c in combo}]
            if world.value(kept) >= clean:
                gain = float(clean - factual) / size
                return Attribution(
                    "minimal_sufficient",
                    [Cause(c.ident, INFRA, gain, c.describe()) for c in combo],
                    agent_share=0.0, infra_share=float(clean - factual),
                    replays=world.replays - before,
                    detail={"set_size": size},
                )
    return Attribution("minimal_sufficient", [], agent_share=0.0,
                       infra_share=float(clean - factual),
                       replays=world.replays - before, detail={"set_size": 0})


# --- joint methods (this paper) -------------------------------------------

def joint_greedy(world: World, trace: Sequence[dict[str, Any]]) -> Attribution:
    """Rank agent steps and messages together by individual effect."""
    before = world.replays
    faults = fault_single(world)
    agent = agent_only(world, trace)
    causes = sorted(faults.causes + agent.causes, key=lambda c: -c.score)
    return Attribution("joint_greedy", causes,
                       agent_share=agent.agent_share, infra_share=faults.infra_share,
                       replays=world.replays - before)


def joint_shapley(world: World, trace: Sequence[dict[str, Any]],
                  max_exact: int = 12, samples: int = 256) -> Attribution:
    """Shapley over messages, plus step-level regret, on an exact split.

    The agent and infrastructure shares are not estimated: they come from the
    telescoping decomposition in :mod:`scm`, so they sum to the loss by
    construction. Shapley then distributes the infrastructure share across
    individual messages in a way that survives the joint-but-not-individual
    case, and the step effects say which decision to fix.
    """
    before = world.replays
    factual = world.factual()
    phi = world.shapley(max_exact=max_exact, samples=samples)
    causes = [Cause(ident, INFRA, value,
                    next((i.describe() for i in world.instances if i.ident == ident), ""))
              for ident, value in phi.items() if abs(value) > 1e-9]

    agent = agent_only(world, trace)

    # Shapley values sum to the infrastructure share and step regrets do not
    # live on that scale, so ranking the two together compares numbers that
    # mean different things -- an agent step scored at the whole loss outranks
    # two messages that split it. The exact decomposition already says which
    # side is responsible; that decides the order, and the scores rank within
    # each side.
    causes.sort(key=lambda c: -c.score)
    agent_causes = sorted(agent.causes, key=lambda c: -c.score)
    if factual.infrastructure >= factual.policy_gap + factual.irreducible:
        causes = causes + agent_causes
    else:
        causes = agent_causes + causes
    return Attribution(
        "joint_shapley", causes,
        agent_share=float(factual.policy_gap + factual.irreducible),
        infra_share=float(factual.infrastructure),
        replays=world.replays - before,
        detail={"shapley_sum": round(sum(phi.values()), 2),
                "infrastructure": factual.infrastructure,
                "decomposition_exact": factual.check()},
    )


METHODS: dict[str, Callable[..., Attribution]] = {
    "last_action": last_action,
    "first_divergence": first_divergence,
    "agent_only": agent_only,
    "fault_single": fault_single,
    "minimal_sufficient": minimal_sufficient,
    "joint_greedy": joint_greedy,
    "joint_shapley": joint_shapley,
}

#: Methods that take the agent's trace as well as the world.
NEEDS_TRACE = {"last_action", "first_divergence", "agent_only", "joint_greedy",
               "joint_shapley"}


def run_method(name: str, world: World, trace: Sequence[dict[str, Any]]) -> Attribution:
    fn = METHODS[name]
    return fn(world, trace) if name in NEEDS_TRACE else fn(world)
