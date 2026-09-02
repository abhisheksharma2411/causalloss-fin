"""Run every experiment in order and report how long each took."""

from __future__ import annotations

import importlib
import time

from _common import banner, provenance, save

ORDER = ("e1_attribution", "e2_allocation", "e3_shapley", "e4_repair",
         "e5_landscape", "e6_cost")


def main() -> None:
    timings = {}
    for name in ORDER:
        start = time.time()
        importlib.import_module(name).main()
        timings[name] = round(time.time() - start, 2)
    banner("all experiments complete")
    for name, seconds in timings.items():
        print(f"  {name:20s} {seconds:8.2f}s")
    save("run_all", {"provenance": provenance(experiment="run_all"),
                     "timings_seconds": timings})


if __name__ == "__main__":
    main()
