"""E3 -- interactions, and whether the sampled Shapley values can be trusted.

Two questions. How often does the loss fail to decompose additively, so that
scoring causes one at a time is not merely imprecise but wrong? And when a
world has too many messages for exact Shapley, how far off is the sampled
estimate?
"""

from __future__ import annotations

from _common import banner, policy_factory, provenance, save

from causalloss.scm import World
from finalitybench.tasks import build_corpus

MAX_EPISODES = 200


def main() -> None:
    banner("E3 interaction structure and Shapley accuracy")
    corpus = build_corpus(n_tasks=320)
    rows, sizes = [], []
    agreement = []

    for subject in ("react", "rule_based", "optimistic"):
        factory = policy_factory(subject)
        seen = 0
        for case in corpus.cases:
            if seen >= MAX_EPISODES:
                break
            world = World(case, factory, 0)
            factual = world.factual()
            if factual.infrastructure == 0:
                continue
            seen += 1
            sizes.append(len(world.instances))

            singles = sum(world.repair_effect(i) for i in world.instances)
            total = factual.infrastructure
            # Additive if repairing each message on its own accounts for the
            # whole infrastructure share. It usually does not.
            gap = singles - total
            rows.append({
                "task_id": case.task_id, "archetype": case.archetype,
                "policy": subject, "n_instances": len(world.instances),
                "infrastructure": total, "sum_single_effects": singles,
                "interaction_gap": gap,
                "additive": gap == 0,
                "overdetermined": singles == 0 and total > 0,
            })

            if len(world.instances) <= 10:
                exact = world.shapley(max_exact=99)
                sampled = world.shapley(max_exact=0, samples=256, rng_seed=1)
                denom = max(1.0, abs(total))
                err = sum(abs(exact[k] - sampled.get(k, 0.0)) for k in exact) / denom
                agreement.append(err)

    additive = sum(1 for r in rows if r["additive"])
    overdet = sum(1 for r in rows if r["overdetermined"])
    payload = {
        "provenance": provenance(experiment="e3_shapley"),
        "n_episodes": len(rows),
        "mean_instances": sum(sizes) / max(1, len(sizes)),
        "max_instances": max(sizes) if sizes else 0,
        "additive_rate": additive / max(1, len(rows)),
        "overdetermined_rate": overdet / max(1, len(rows)),
        "mean_interaction_gap": sum(r["interaction_gap"] for r in rows) / max(1, len(rows)),
        "shapley_sampled_vs_exact_l1": sum(agreement) / max(1, len(agreement)),
        "shapley_compared_on": len(agreement),
        "rows": rows[:400],
    }
    save("e3_shapley", payload)
    print(f"  episodes with infrastructure loss : {len(rows)}")
    print(f"  additively decomposable           : {payload['additive_rate']:.1%}")
    print(f"  fully overdetermined (singles = 0): {payload['overdetermined_rate']:.1%}")
    print(f"  mean interaction gap              : ${payload['mean_interaction_gap']/100:.2f}")
    print(f"  sampled-vs-exact Shapley L1 error : {payload['shapley_sampled_vs_exact_l1']:.3%}"
          f" over {payload['shapley_compared_on']} episodes")


if __name__ == "__main__":
    main()
