"""E4 -- does acting on the attribution actually help?

An attribution is only worth anything if repairing what it names removes the
loss. Each method nominates a top cause; the experiment repairs exactly that
one thing and measures how much of the loss goes away. Naming a cause that
cannot be repaired -- or one whose repair changes nothing -- is scored as the
zero it is.
"""

from __future__ import annotations

from _common import banner, policy_factory, provenance, save

from causalloss.attribution import METHODS, run_method
from causalloss.planted import build_planted, stratum_counts
from causalloss.scm import World
from finalitybench.tasks import build_corpus

PER_STRATUM = 40


def main() -> None:
    banner("E4 counterfactual repair validation")
    corpus = build_corpus(n_tasks=320)
    subjects = ("react", "rule_based", "optimistic")
    episodes = []
    for subject in subjects:
        episodes.extend(build_planted(corpus.cases, policy_factory(subject),
                                      seeds=(0, 1, 2), max_per_stratum=PER_STRATUM))
    episodes = [e for e in episodes if e.truth_kind == "infrastructure"]
    print(f"  {len(episodes)} infrastructure episodes {stratum_counts(episodes)}")
    by_id = {c.task_id: c for c in corpus.cases}

    stats = {m: {"recovered": 0.0, "total": 0.0, "full": 0, "n": 0} for m in METHODS}

    for episode in episodes:
        case = by_id[episode.task_id]
        world = World(case, policy_factory(episode.policy_name), episode.seed,
                      present=episode.injected or [])
        factual = world.factual()
        loss = episode.loss
        if loss <= 0:
            continue

        for name in METHODS:
            attribution = run_method(name, world, factual.trace)
            named = [c.ident for c in attribution.causes[:len(episode.truth)]]
            keep = [i for i in world.instances if i.ident not in set(named)]
            after = world.factual_reference - world.value(keep)
            recovered = max(0, loss - after)
            record = stats[name]
            record["recovered"] += recovered
            record["total"] += loss
            record["full"] += int(after <= 0)
            record["n"] += 1

    rows = [{
        "method": name,
        "loss_recovered_share": r["recovered"] / max(1.0, r["total"]),
        "fully_fixed_rate": r["full"] / max(1, r["n"]),
        "dollars_recovered": r["recovered"],
        "dollars_available": r["total"],
        "n": r["n"],
    } for name, r in stats.items()]
    rows.sort(key=lambda r: -r["loss_recovered_share"])

    save("e4_repair", {
        "provenance": provenance(experiment="e4_repair"),
        "policies": list(subjects), "n_episodes": len(episodes), "rows": rows,
    })
    hdr = f"{'method':20s}{'loss recovered':>16s}{'fully fixed':>13s}{'$ recovered':>13s}"
    print(hdr); print("-" * len(hdr))
    for r in rows:
        print(f"{r['method']:20s}{r['loss_recovered_share']:16.1%}"
              f"{r['fully_fixed_rate']:13.1%}{r['dollars_recovered']/100:13.2f}")


if __name__ == "__main__":
    main()
