"""E1 -- can each method name the cause that was actually planted?

Graded on episodes whose cause is definitional rather than derived. Reports
top-1 accuracy, exact-set recovery on the paired stratum, and whether the
method's verdict (agent or infrastructure) matches the truth.
"""

from __future__ import annotations

from _common import banner, policy_factory, provenance, save

from causalloss.attribution import AGENT, INFRA, METHODS, run_method
from causalloss.planted import build_planted, stratum_counts
from causalloss.scm import World
from finalitybench.tasks import build_corpus

PER_STRATUM = 60


def main() -> None:
    banner("E1 attribution accuracy on planted causes")
    corpus = build_corpus(n_tasks=320)
    # Pooled over three policies rather than one. Overdetermination is rare in
    # any single policy's traces -- two messages that are each independently
    # enough to sink the same episode -- and pooling also keeps the conclusion
    # from being a property of one procedure's quirks.
    subjects = ("react", "rule_based", "optimistic")
    episodes = []
    for subject in subjects:
        episodes.extend(build_planted(
            corpus.cases, policy_factory(subject), seeds=(0, 1, 2, 3, 4),
            max_per_stratum=PER_STRATUM))
    print(f"  planted episodes: {stratum_counts(episodes)} over {len(subjects)} policies")
    by_id = {c.task_id: c for c in corpus.cases}

    rows: dict[str, dict] = {
        m: {"method": m, "top1": {}, "setmatch": {}, "verdict": {}, "n": {},
            "replays": 0} for m in METHODS
    }

    for episode in episodes:
        case = by_id[episode.task_id]
        factory = policy_factory(episode.policy_name)
        world = World(case, factory, episode.seed, present=episode.injected or [])
        factual = world.factual()
        truth = set(episode.truth)
        stratum = episode.stratum

        for name in METHODS:
            attribution = run_method(name, world, factual.trace)
            record = rows[name]
            record["n"][stratum] = record["n"].get(stratum, 0) + 1
            record["replays"] += attribution.replays

            if stratum == "agent":
                hit = attribution.verdict == AGENT
                sethit = hit
            else:
                hit = bool(attribution.top_k(1)) and attribution.top_k(1)[0] in truth
                sethit = set(attribution.top_k(len(truth))) == truth
            record["top1"][stratum] = record["top1"].get(stratum, 0) + int(hit)
            record["setmatch"][stratum] = record["setmatch"].get(stratum, 0) + int(sethit)
            expected = AGENT if episode.truth_kind == "agent" else INFRA
            record["verdict"][stratum] = record["verdict"].get(stratum, 0) + int(
                attribution.verdict == expected)

    strata = ("single", "conjunctive", "overdetermined", "agent")
    table = []
    for name, record in rows.items():
        entry = {"method": name, "replays_total": record["replays"]}
        for stratum in strata:
            n = record["n"].get(stratum, 0) or 1
            entry[f"top1_{stratum}"] = record["top1"].get(stratum, 0) / n
            entry[f"set_{stratum}"] = record["setmatch"].get(stratum, 0) / n
            entry[f"verdict_{stratum}"] = record["verdict"].get(stratum, 0) / n
        entry["verdict_overall"] = sum(
            record["verdict"].get(s, 0) for s in strata) / max(1, sum(
                record["n"].get(s, 0) for s in strata))
        table.append(entry)

    save("e1_attribution", {
        "provenance": provenance(experiment="e1_attribution"),
        "corpus": corpus.stats(), "policies": list(subjects),
        "n_episodes": len(episodes), "strata": stratum_counts(episodes),
        "rows": table,
    })

    hdr = (f"{'method':20s}{'single':>9s}{'conjunct':>10s}{'overdet':>9s}"
           f"{'set:overdet':>13s}{'agent':>8s}{'verdict':>9s}{'replays':>9s}")
    print(hdr); print("-" * len(hdr))
    for e in table:
        print(f"{e['method']:20s}{e['top1_single']:9.1%}{e['top1_conjunctive']:10.1%}"
              f"{e['top1_overdetermined']:9.1%}{e['set_overdetermined']:13.1%}"
              f"{e['top1_agent']:8.1%}{e['verdict_overall']:9.1%}{e['replays_total']:9d}")


if __name__ == "__main__":
    main()
