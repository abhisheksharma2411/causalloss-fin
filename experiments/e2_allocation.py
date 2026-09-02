"""E2 -- who gets the bill?

Attribution is not only about naming a step; it is about how much of the money
each side is charged. This experiment compares each method's agent/infrastructure
split against the planted truth, and measures the specific failure this paper is
about: a method whose causal model contains no infrastructure variable must
charge infrastructure-caused loss to the agent, and here that is quantified in
dollars rather than asserted.
"""

from __future__ import annotations

from _common import banner, policy_factory, provenance, save

from causalloss.attribution import AGENT, INFRA, METHODS, run_method
from causalloss.planted import build_planted, stratum_counts
from causalloss.scm import World
from finalitybench.tasks import build_corpus

PER_STRATUM = 60


def main() -> None:
    banner("E2 agent-versus-infrastructure allocation")
    corpus = build_corpus(n_tasks=320)
    subjects = ("react", "rule_based", "optimistic")
    episodes = []
    for subject in subjects:
        episodes.extend(build_planted(corpus.cases, policy_factory(subject),
                                      seeds=(0, 1, 2, 3, 4),
                                      max_per_stratum=PER_STRATUM))
    print(f"  {len(episodes)} episodes {stratum_counts(episodes)}")
    by_id = {c.task_id: c for c in corpus.cases}

    stats = {m: {"err": [], "misattributed": 0, "infra_n": 0,
                 "charged_to_agent": 0, "true_infra_dollars": 0}
             for m in METHODS}

    for episode in episodes:
        case = by_id[episode.task_id]
        world = World(case, policy_factory(episode.policy_name), episode.seed,
                      present=episode.injected or [])
        factual = world.factual()
        loss = max(1, episode.loss)
        # Truth: the whole loss belongs to whichever side planted it.
        true_infra = float(episode.loss) if episode.truth_kind == "infrastructure" else 0.0

        for name in METHODS:
            attribution = run_method(name, world, factual.trace)
            record = stats[name]
            predicted = attribution.infra_share
            record["err"].append(abs(predicted - true_infra) / loss)
            if episode.truth_kind == "infrastructure":
                record["infra_n"] += 1
                record["true_infra_dollars"] += episode.loss
                if attribution.verdict == AGENT:
                    record["misattributed"] += 1
                    record["charged_to_agent"] += episode.loss

    rows = []
    for name, record in stats.items():
        n_infra = max(1, record["infra_n"])
        rows.append({
            "method": name,
            "mean_allocation_error": sum(record["err"]) / len(record["err"]),
            "misattribution_rate": record["misattributed"] / n_infra,
            "dollars_wrongly_charged_to_agent": record["charged_to_agent"],
            "true_infrastructure_dollars": record["true_infra_dollars"],
            "share_of_infra_dollars_misfiled":
                record["charged_to_agent"] / max(1, record["true_infra_dollars"]),
        })
    rows.sort(key=lambda r: r["mean_allocation_error"])

    save("e2_allocation", {
        "provenance": provenance(experiment="e2_allocation"),
        "policies": list(subjects), "n_episodes": len(episodes),
        "strata": stratum_counts(episodes), "rows": rows,
    })

    hdr = f"{'method':20s}{'alloc err':>11s}{'misattr':>10s}{'$ to agent':>12s}{'share':>8s}"
    print(hdr); print("-" * len(hdr))
    for r in rows:
        print(f"{r['method']:20s}{r['mean_allocation_error']:11.1%}"
              f"{r['misattribution_rate']:10.1%}"
              f"{r['dollars_wrongly_charged_to_agent']/100:12.2f}"
              f"{r['share_of_infra_dollars_misfiled']:8.1%}")


if __name__ == "__main__":
    main()
