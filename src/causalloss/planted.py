"""Episodes whose cause is known by construction, not by any attribution method.

Validating an attribution method against causes that the method itself derived
proves nothing. These episodes are built the other way round: start from a
(case, policy) the policy solves cleanly, inject a known set of faults, and
check that the loss appears. The injected set is then the cause by definition --
it is the only thing that differs from a world in which nothing went wrong.

Three strata, because they test different things:

``single``         one fault causes the loss. Any method that can name a fault
                   at all should find it.
``conjunctive``    two faults, neither harmful alone, harmful together. Each is
                   necessary given the other, so repairing either one fixes the
                   episode -- single-effect scoring handles this case, and it is
                   included to show that it does.
``overdetermined`` two faults, *either* sufficient on its own. Repairing one
                   changes nothing because the other still causes the loss, so
                   every cause scores zero under one-at-a-time repair. This is
                   the case that separates interaction-aware allocation from
                   single-effect scoring, and it is the classical
                   overdetermination problem in actual causation.
``agent``          no faults, and the policy still loses money. The cause is the
                   policy. A method that only knows how to blame the environment
                   has nothing to say, and one that only knows how to blame the
                   agent gets these right for the wrong reason.

Every episode also carries **distractor faults**: instances that are present and
demonstrably harmless. Without them the task is trivial -- an early version
planted only the causal faults, and a heuristic that simply named the earliest
message in the schedule scored 100%, because there was nothing else to name.
Distractors are verified harmless in the presence of the causal set, not merely
harmless alone.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from ._p1 import ensure_p1
from .faultgraph import FaultInstance, extract
from .scm import World, run_in_world

ensure_p1()

from finalitybench.faults import FaultProfile  # noqa: E402
from finalitybench.policies import Policy  # noqa: E402
from finalitybench.world import Case  # noqa: E402


@dataclass
class PlantedEpisode:
    """One episode with a known cause."""

    task_id: str
    archetype: str
    stratum: str                       # single | pair | agent
    policy_name: str
    seed: int
    injected: list[FaultInstance]      # the faults actually present
    truth: list[str]                   # idents of the causes; empty for `agent`
    truth_kind: str                    # infrastructure | agent
    loss: int
    clean_loss: int
    candidates: list[FaultInstance] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id, "archetype": self.archetype,
            "stratum": self.stratum, "policy": self.policy_name, "seed": self.seed,
            "truth": list(self.truth), "truth_kind": self.truth_kind,
            "loss": self.loss, "clean_loss": self.clean_loss,
            "n_candidates": len(self.candidates),
            "injected": [i.as_dict() for i in self.injected],
        }


def _harmless(world: World, reference: int, causal: Sequence[FaultInstance],
              pool: Sequence[FaultInstance], want: int) -> list[FaultInstance]:
    """Instances that change nothing, checked alongside the causal set.

    Harmless *on its own* is not good enough: a message that does no damage in
    isolation can still change the outcome once another one has gone missing.
    """
    causal_loss = reference - world.value(list(causal))
    chosen: list[FaultInstance] = []
    for inst in pool:
        if any(inst.ident == c.ident for c in causal):
            continue
        trial = list(causal) + chosen + [inst]
        if reference - world.value(trial) == causal_loss:
            chosen.append(inst)
        if len(chosen) >= want:
            break
    return chosen


def build_planted(
    cases: Sequence[Case],
    policy_factory: Callable[[], Policy],
    *,
    seeds: Sequence[int] = (0, 1, 2),
    profile: FaultProfile | None = None,
    max_per_stratum: int = 60,
    distractors: int = 4,
    rng_seed: int = 11,
) -> list[PlantedEpisode]:
    """Construct episodes whose cause is definitional."""
    profile = profile or FaultProfile()
    rng = random.Random(rng_seed)
    out: list[PlantedEpisode] = []
    strata = ("single", "conjunctive", "overdetermined", "agent")
    counts = {s: 0 for s in strata}

    for case in cases:
        if all(counts[s] >= max_per_stratum for s in strata):
            break
        for seed in seeds:
            world = World(case, policy_factory, seed, profile)
            reference = world.factual_reference
            clean_loss = reference - world.value([])
            pool = list(world.instances)
            name = policy_factory().name

            if clean_loss > 0:
                if counts["agent"] < max_per_stratum:
                    # Faults that do nothing, so the episode still looks messy.
                    noise = _harmless(world, reference, [], pool, distractors)
                    out.append(PlantedEpisode(
                        case.task_id, case.archetype, "agent", name, seed,
                        injected=noise, truth=[], truth_kind="agent",
                        loss=reference - world.value(noise), clean_loss=clean_loss,
                        candidates=noise))
                    counts["agent"] += 1
                continue

            if not pool:
                continue

            harmful = [i for i in pool if reference - world.value([i]) > 0]
            benign = [i for i in pool if reference - world.value([i]) == 0]

            # overdetermined: two faults, either one enough on its own.
            if counts["overdetermined"] < max_per_stratum and len(harmful) >= 2:
                found = None
                for a, b in itertools.combinations(harmful, 2):
                    both = reference - world.value([a, b])
                    if both > 0 and both == reference - world.value([a]) \
                            and both == reference - world.value([b]):
                        found = (a, b)
                        break
                if found is not None:
                    a, b = found
                    noise = _harmless(world, reference, [a, b], benign, distractors)
                    out.append(PlantedEpisode(
                        case.task_id, case.archetype, "overdetermined", name, seed,
                        injected=[a, b] + noise, truth=[a.ident, b.ident],
                        truth_kind="infrastructure",
                        loss=reference - world.value([a, b] + noise), clean_loss=0,
                        candidates=[a, b] + noise))
                    counts["overdetermined"] += 1
                    continue

            # conjunctive: neither alone, both together.
            if counts["conjunctive"] < max_per_stratum and len(benign) >= 2:
                found = None
                for a, b in itertools.combinations(benign, 2):
                    if reference - world.value([a, b]) > 0:
                        found = (a, b)
                        break
                if found is not None:
                    a, b = found
                    rest = [i for i in benign if i.ident not in {a.ident, b.ident}]
                    noise = _harmless(world, reference, [a, b], rest, distractors)
                    out.append(PlantedEpisode(
                        case.task_id, case.archetype, "conjunctive", name, seed,
                        injected=[a, b] + noise, truth=[a.ident, b.ident],
                        truth_kind="infrastructure",
                        loss=reference - world.value([a, b] + noise), clean_loss=0,
                        candidates=[a, b] + noise))
                    counts["conjunctive"] += 1
                    continue

            # single: one fault, plus harmless company.
            if counts["single"] < max_per_stratum and harmful:
                chosen = rng.choice(harmful)
                noise = _harmless(world, reference, [chosen], benign, distractors)
                out.append(PlantedEpisode(
                    case.task_id, case.archetype, "single", name, seed,
                    injected=[chosen] + noise, truth=[chosen.ident],
                    truth_kind="infrastructure",
                    loss=reference - world.value([chosen] + noise), clean_loss=0,
                    candidates=[chosen] + noise))
                counts["single"] += 1
    return out


def stratum_counts(episodes: Sequence[PlantedEpisode]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for e in episodes:
        counts[e.stratum] = counts.get(e.stratum, 0) + 1
    return dict(sorted(counts.items()))
