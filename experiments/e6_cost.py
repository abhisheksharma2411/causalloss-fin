"""E6 -- what each method costs, measured honestly.

Replay counts are taken on a fresh world per method. Sharing one cache across
methods makes whichever runs last look almost free, which is an artefact of the
measurement rather than a property of the method.
"""

from __future__ import annotations

import time

from _common import banner, policy_factory, provenance, save

from causalloss.attribution import METHODS, run_method
from causalloss.scm import World
from finalitybench.tasks import build_corpus

N_EPISODES = 60


def main() -> None:
    banner("E6 cost per attribution")
    corpus = build_corpus(n_tasks=320)
    factory = policy_factory("react")

    stats = {m: {"replays": 0, "seconds": 0.0, "n": 0} for m in METHODS}
    for case in corpus.cases[:N_EPISODES]:
        # One shared world only to obtain the trace; each method then gets a
        # cold one, so no method inherits another's cached replays.
        seed_world = World(case, factory, 0)
        trace = seed_world.factual().trace
        n_instances = len(seed_world.instances)
        for name in METHODS:
            world = World(case, factory, 0)
            before, start = world.replays, time.perf_counter()
            run_method(name, world, trace)
            stats[name]["replays"] += world.replays - before
            stats[name]["seconds"] += time.perf_counter() - start
            stats[name]["n"] += 1

    rows = [{
        "method": name,
        "replays_per_episode": r["replays"] / max(1, r["n"]),
        "ms_per_episode": 1000 * r["seconds"] / max(1, r["n"]),
    } for name, r in stats.items()]
    rows.sort(key=lambda r: r["replays_per_episode"])

    save("e6_cost", {"provenance": provenance(experiment="e6_cost"),
                     "n_episodes": N_EPISODES, "rows": rows})
    hdr = f"{'method':20s}{'replays/episode':>17s}{'ms/episode':>12s}"
    print(hdr); print("-" * len(hdr))
    for r in rows:
        print(f"{r['method']:20s}{r['replays_per_episode']:17.1f}{r['ms_per_episode']:12.1f}")


if __name__ == "__main__":
    main()
