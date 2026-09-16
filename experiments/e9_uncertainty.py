"""E9 -- intervals for the prevalence claims, and whether the search cap binds.

Two kinds of number appear in this paper and only one of them needs an
interval. The telescoping identity is algebra: it holds on every episode or the
test suite fails, and quoting a confidence interval around it would be
meaningless. Claims about how often a phenomenon occurs in a generated
population are different. ``Interaction is a quarter of the episodes'' is an
estimate from a sample, and a reader deciding whether to believe it needs to
know how much the sample constrains it.

The unit is the task. Several episodes come from one sampled task and share its
amount, its archetype and its fault draw, so resampling episodes would treat
correlated evidence as independent and give intervals that are too narrow.
A replicate draws tasks with replacement and takes every episode belonging to a
drawn task.

The population is exactly E3's, three policies over the same episodes, so the
point estimates here reproduce the ones the paper quotes and only the
uncertainty around them is new. A different population would give an interval
around a number the paper does not state.

The second question is whether the minimal-sufficient search ever ran out of
room. It looks for a repair set of at most three messages, and a cap that binds
would mean perfect recovery was measured only on the episodes easy enough to
fit inside it. If no episode needs the cap, the recovery figure is about the
method; if some do, the figure is conditional and the paper has to say so.
"""

from __future__ import annotations

import random

from _common import banner, policy_factory, provenance, save

from causalloss.attribution import minimal_sufficient
from causalloss.scm import World
from finalitybench.tasks import build_corpus

N_TASKS = 320
SEED = 0
REPLICATES = 2000
ALPHA = 0.05
MAX_EPISODES = 200
SEARCH_CAP = 3
#: The same three subjects E3 measures, in the same order.
POLICIES = ("react", "rule_based", "optimistic")


def clustered_interval(groups: list[list[bool]], rng: random.Random) -> dict:
    """Percentile bootstrap over groups, not over the observations in them."""
    flat = [x for g in groups for x in g]
    point = sum(flat) / len(flat) if flat else 0.0
    draws = []
    for _ in range(REPLICATES):
        picked = [groups[rng.randrange(len(groups))] for _ in range(len(groups))]
        obs = [x for g in picked for x in g]
        if obs:
            draws.append(sum(obs) / len(obs))
    draws.sort()
    lo = draws[int(ALPHA / 2 * len(draws))]
    hi = draws[int((1 - ALPHA / 2) * len(draws)) - 1]
    return {"point": point, "low": lo, "high": hi,
            "groups": len(groups), "observations": len(flat),
            "replicates": REPLICATES}


def main() -> None:
    banner("E9 clustered intervals and the search cap")
    corpus = build_corpus(n_tasks=N_TASKS)
    rng = random.Random(SEED)

    by_task_additive: dict[str, list[bool]] = {}
    by_task_overdet: dict[str, list[bool]] = {}
    cap_binds = 0
    sizes: list[int] = []
    searched = 0

    for subject in POLICIES:
        factory = policy_factory(subject)
        seen = 0
        for case in corpus.cases:
            if seen >= MAX_EPISODES:
                break
            world = World(case, factory, SEED)
            factual = world.factual()
            if factual.infrastructure == 0:
                continue
            seen += 1
            searched += 1

            # Same definitions as E3, so the point estimates agree and only
            # the uncertainty around them is new.
            singles = sum(world.repair_effect(i) for i in world.instances)
            total = factual.infrastructure
            by_task_additive.setdefault(case.task_id, []).append(singles == total)
            by_task_overdet.setdefault(case.task_id, []).append(
                singles == 0 and total > 0)

            att = minimal_sufficient(world, max_size=SEARCH_CAP)
            if att.causes:
                sizes.append(len(att.causes))
            else:
                # No set of at most SEARCH_CAP messages removed the loss.
                cap_binds += 1

    additive = clustered_interval(list(by_task_additive.values()), rng)
    overdet = clustered_interval(list(by_task_overdet.values()), rng)

    save("e9_uncertainty", {
        "provenance": provenance(),
        "config": {"n_tasks": N_TASKS, "seed": SEED, "replicates": REPLICATES,
                   "alpha": ALPHA, "max_episodes": MAX_EPISODES,
                   "search_cap": SEARCH_CAP, "unit": "task"},
        "additive_rate": additive,
        "non_additive_rate": {"point": 1 - additive["point"],
                              "low": 1 - additive["high"],
                              "high": 1 - additive["low"],
                              "groups": additive["groups"],
                              "observations": additive["observations"]},
        "overdetermined_rate": overdet,
        "search_cap": {
            "cap": SEARCH_CAP,
            "episodes_searched": searched,
            "episodes_where_the_cap_bound": cap_binds,
            "largest_repair_set_found": max(sizes) if sizes else 0,
            "cap_never_bound": cap_binds == 0,
            "size_histogram": {str(n): sizes.count(n)
                               for n in sorted(set(sizes))},
        },
    })


if __name__ == "__main__":
    main()
