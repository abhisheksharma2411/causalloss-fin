"""E7 -- why the family label annotates an instance instead of defining it.

The decomposition here diffs the realised schedule against the fault-free one
and calls every difference an instance. The obvious alternative is to
decompose per family: build the schedule with only one family enabled, diff
that against the baseline, and call the differences that family's instances.
It is simpler, it gives every instance a family by construction, and it was
the first thing we wrote.

It does not work, and the paper said so with a number that lived only in the
commit message it came from. This reconstructs it.

Superposition is the assumption under test: that the realised schedule is the
baseline plus each family's contribution, computed independently. FinalityBench
draws its families independently and they do not act independently -- a
duplicate is placed relative to a delivery's already-delayed arrival, a partial
commit propagates to copies that exist only because duplication fired, and
whether a reorder swap is eligible depends on times delay has already moved. So
the per-family instances, applied together, should fail to reproduce the
realised schedule on a substantial share of episodes, and the current
decomposition should reproduce it on all of them.

Both halves matter. A per-family failure rate near zero would mean the
simpler design was fine and this paper's is unnecessary complexity.
"""

from __future__ import annotations

from _common import banner, provenance, save

from causalloss.faultgraph import apply, extract, round_trip_ok, _canonical
from finalitybench.faults import PROFILE_FAMILIES, FaultProfile
from finalitybench.tasks import build_corpus

N_TASKS = 320
SEEDS = (0, 1, 2)
MAX_EPISODES = 240


def superposed(case, seed: int) -> bool:
    """Do per-family instances, applied together, give the realised schedule?

    Each family is extracted from a world where only that family fires, which
    is what decomposing by family means. The instances are then pooled and
    applied to the fault-free baseline, and the result compared against the
    schedule the full profile actually produced.
    """
    full = FaultProfile()
    _, baseline, realised = extract(case, seed, full)

    pooled = []
    for family in PROFILE_FAMILIES:
        only = FaultProfile.only(family)
        if not full.enabled(family):
            continue
        instances, _, _ = extract(case, seed, only)
        pooled.extend(instances)

    return _canonical(apply(baseline, pooled, full)) == _canonical(realised)


def main() -> None:
    banner("E7 superposition of fault families")
    corpus = build_corpus(n_tasks=N_TASKS)

    episodes = 0
    per_family_ok = 0
    current_ok = 0
    failures = []

    for seed in SEEDS:
        for case in corpus.cases:
            if episodes >= MAX_EPISODES:
                break
            episodes += 1
            ok_now = round_trip_ok(case, seed)
            current_ok += int(ok_now)
            ok_super = superposed(case, seed)
            per_family_ok += int(ok_super)
            if not ok_super:
                failures.append({"task_id": case.task_id, "seed": seed,
                                 "archetype": case.archetype})
        if episodes >= MAX_EPISODES:
            break

    save("e7_superposition", {
        "provenance": provenance(),
        "config": {"n_tasks": N_TASKS, "seeds": list(SEEDS),
                   "max_episodes": MAX_EPISODES,
                   "families": sorted(PROFILE_FAMILIES)},
        "failures": failures[:40],
        "headline": {
            "episodes": episodes,
            "per_family_reproduced": per_family_ok,
            "per_family_failed": episodes - per_family_ok,
            "per_family_failure_rate": (episodes - per_family_ok) / episodes,
            "current_decomposition_reproduced": current_ok,
            "current_decomposition_failed": episodes - current_ok,
            "note": ("the per-family decomposition assumes the families "
                     "superpose; the current one diffs against the fault-free "
                     "schedule and makes no such assumption"),
        },
    })


if __name__ == "__main__":
    main()
