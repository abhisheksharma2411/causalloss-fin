"""E5 -- across the whole corpus, where does the money actually go?

The three-way decomposition applied to every task and every policy, with no
planting. This is the practical payoff: for a given policy, how much of its
loss is the environment's doing, how much is its own, and how much would
survive any policy that cannot see finality.
"""

from __future__ import annotations

from _common import banner, policy_factory, provenance, save

from causalloss.scm import World
from finalitybench.faults import FaultProfile
from finalitybench.tasks import build_corpus
from finalitybench.world import EVAL_SEEDS

SUBJECTS = ("optimistic", "rule_based", "react", "transactional")


def main() -> None:
    banner("E5 responsibility across the corpus")
    corpus = build_corpus(n_tasks=320)
    profile = FaultProfile()
    seeds = EVAL_SEEDS[:3]

    rows, by_archetype = [], {}
    exact_checks = 0
    exact_ok = 0

    for subject in SUBJECTS:
        factory = policy_factory(subject)
        totals = {"infrastructure": 0, "policy": 0, "irreducible": 0, "total": 0}
        n = 0
        for case in corpus.cases:
            for seed in seeds:
                world = World(case, factory, seed, profile)
                factual = world.factual()
                exact_checks += 1
                exact_ok += int(factual.check())
                shares = factual.shares()
                for key in totals:
                    totals[key] += shares[key]
                n += 1
                bucket = by_archetype.setdefault(
                    (subject, case.archetype),
                    {"infrastructure": 0, "policy": 0, "irreducible": 0, "total": 0, "n": 0})
                for key in ("infrastructure", "policy", "irreducible", "total"):
                    bucket[key] += shares[key]
                bucket["n"] += 1

        denom = max(1, totals["total"])
        rows.append({
            "policy": subject, "n_episodes": n,
            "mean_loss": totals["total"] / n,
            "infrastructure": totals["infrastructure"], "policy_gap": totals["policy"],
            "irreducible": totals["irreducible"], "total": totals["total"],
            "infrastructure_share": totals["infrastructure"] / denom,
            "policy_share": totals["policy"] / denom,
            "irreducible_share": totals["irreducible"] / denom,
        })

    archetype_rows = [
        {"policy": k[0], "archetype": k[1], "n": v["n"],
         "infrastructure": v["infrastructure"], "policy_gap": v["policy"],
         "irreducible": v["irreducible"], "total": v["total"],
         "infrastructure_share": v["infrastructure"] / max(1, v["total"])}
        for k, v in sorted(by_archetype.items())
    ]

    save("e5_landscape", {
        "provenance": provenance(experiment="e5_landscape"),
        "seeds": list(seeds), "policies": list(SUBJECTS),
        "decomposition_exact": f"{exact_ok}/{exact_checks}",
        "rows": rows, "by_archetype": archetype_rows,
    })

    print(f"  decomposition exact on {exact_ok}/{exact_checks} episodes")
    hdr = f"{'policy':16s}{'mean loss':>11s}{'infra':>9s}{'policy':>9s}{'irreducible':>13s}"
    print(hdr); print("-" * len(hdr))
    for r in rows:
        print(f"{r['policy']:16s}{r['mean_loss']/100:11.2f}{r['infrastructure_share']:9.1%}"
              f"{r['policy_share']:9.1%}{r['irreducible_share']:13.1%}")


if __name__ == "__main__":
    main()
