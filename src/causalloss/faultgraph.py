"""Individual fault instances, and an operator that undoes one of them.

Attribution needs a cause you can point at. "Delay was enabled" is a knob, not
a cause; "the settlement message to the processor was dropped" is a cause. This
module decomposes a realised fault schedule into named instances and provides a
constructive way to rebuild the schedule with any subset removed.

Instances are read off by diffing the *realised* schedule against the
fault-free one, so the decomposition is complete by construction: every way the
two schedules differ is some instance, and repairing all of them returns the
fault-free schedule exactly.

An earlier version decomposed per family instead, building each
``only:<family>`` schedule and diffing that against the baseline. It failed
round-trip on 149 of 240 episodes, and the reason is worth recording because it
is a property of the environment rather than a coding slip: FinalityBench's
fault families are drawn independently but do not *act* independently.
Duplicate copies are placed relative to a delivery's already-delayed time, a
partial commit propagates to copies that only exist when duplication fired, and
whether a reorder swap is eligible at all depends on times delay has already
moved. Families that compose cannot be attributed by superposition.

So the family label here is an annotation on an instance, not its definition. An
instance is "this message arrived 106 ticks late"; the label says which
mechanisms produced that, and reports both when delay and reorder both touched
the same delivery. :func:`round_trip_ok` still checks completeness, and the test
suite asserts it over the corpus -- anything the extractor misses would sit in
the residual and be silently charged to the agent, which is the exact error this
paper is about.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from ._p1 import ensure_p1

ensure_p1()

from finalitybench.faults import (  # noqa: E402
    Delivery,
    FaultProfile,
    apply_forced,
    PARTIAL_COMMIT,
    PROFILE_FAMILIES,
    Schedule,
    SYSTEMS,
    build_schedule,
)
from finalitybench.world import Case, build_log, schedule_seed_for  # noqa: E402

DROP = "drop"
DELAY = "delay"
REORDER = "reorder"
DUPLICATE = "duplicate"
PARTIAL = "partial"
STALE = "stale"

#: The order instances are applied in. Delay moves a delivery, reorder then
#: exchanges times, so reorder must come second or a swap would be computed
#: against the wrong times.
APPLY_ORDER = (DROP, DELAY, REORDER, DUPLICATE, PARTIAL, STALE)

Key = tuple[int, str, int]  # (event_seq, system, copy)


@dataclass(frozen=True)
class FaultInstance:
    """One thing the infrastructure did, nameable and individually undoable."""

    kind: str
    system: str
    event_seq: int = -1
    detail: dict[str, Any] = field(default_factory=dict, compare=False)

    @property
    def structural(self) -> bool:
        """Is this the fault that defines the archetype, rather than a drawn one?"""
        return bool(self.detail.get("structural", False))

    @property
    def ident(self) -> str:
        if self.kind == STALE:
            return f"{self.kind}:{self.system}"
        return f"{self.kind}:{self.system}:{self.event_seq}"

    def describe(self) -> str:
        """Plain English, for a figure axis or an error message."""
        if self.kind == DROP:
            return f"message about event {self.event_seq} never reached the {self.system}"
        if self.kind == DELAY:
            return (f"message about event {self.event_seq} reached the {self.system} "
                    f"{self.detail.get('ticks', '?')} ticks late")
        if self.kind == DUPLICATE:
            return f"the {self.system} was told about event {self.event_seq} more than once"
        if self.kind == PARTIAL:
            return f"the {self.system} posted only half of event {self.event_seq}"
        if self.kind == REORDER:
            return (f"message about event {self.event_seq} arrived at the {self.system} "
                    f"out of order, {abs(self.detail.get('ticks', 0))} ticks off")
        return f"the {self.system} answered reads {self.detail.get('lag', '?')} ticks stale"

    def as_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "system": self.system, "event_seq": self.event_seq,
                "ident": self.ident, "structural": self.structural,
                "detail": dict(self.detail)}


def _index(schedule: Schedule) -> dict[Key, Delivery]:
    return {(d.event_seq, d.system, d.copy): d for d in schedule.deliveries}


def extract(case: Case, seed: int, profile: FaultProfile | None = None
            ) -> tuple[list[FaultInstance], Schedule, Schedule]:
    """Decompose the realised schedule into individually repairable instances.

    Returns the instances, the fault-free baseline, and the realised schedule.
    """
    profile = profile or FaultProfile()
    log = build_log(case)
    sched_seed = schedule_seed_for(case.schedule_seed, seed)

    baseline = build_schedule(log, FaultProfile.none(), sched_seed)
    realised = apply_forced(build_schedule(log, profile, sched_seed), log, case.forced)

    # The baseline is fault-free *and* forced-free, so an archetype's defining
    # fault -- the settlement the processor never hears about, the ledger entry
    # posted twice -- also shows up as an instance and can be intervened on.
    # Those are marked ``structural`` because they define the task rather than
    # being drawn, and the results report them separately.
    structural = {
        key for key in _index(apply_forced(baseline, log, case.forced))
        if key not in _index(baseline)
    } | {
        key for key in _index(baseline)
        if key not in _index(apply_forced(baseline, log, case.forced))
    }

    # Which mechanism moved a delivery is settled by a but-for test taken in
    # context: remove one family from the full profile and see whether that
    # delivery still arrives when it did. Asking each family *alone* gives the
    # wrong answer, because reorder is almost never eligible on its own -- the
    # swaps it makes only become possible once delay has moved arrivals close
    # together.
    movers: dict[Key, set[str]] = {}
    real_times = {k: d.at_t for k, d in _index(realised).items()}
    for family in ("delay", "reorder"):
        if not profile.enabled(family):
            continue
        without = _index(apply_forced(
            build_schedule(log, FaultProfile.all_but(family), sched_seed), log, case.forced))
        for key, at_t in real_times.items():
            other = without.get(key)
            if other is None or other.at_t != at_t:
                movers.setdefault(key, set()).add(family)

    base_idx = _index(baseline)
    real_idx = _index(realised)
    instances: list[FaultInstance] = []

    # Deliveries the baseline has and the realisation does not.
    for key, delivery in base_idx.items():
        if key not in real_idx:
            instances.append(FaultInstance(
                DROP, key[1], key[0],
                {"at_t": delivery.at_t, "structural": key in structural}))

    # Extra copies the realisation grew.
    copies: dict[tuple[int, str], list[tuple[int, int, str]]] = {}
    for key, delivery in real_idx.items():
        if key[2] > 0:
            copies.setdefault((key[0], key[1]), []).append(
                (key[2], delivery.at_t, delivery.mutation))
    for (seq, system), entries in copies.items():
        instances.append(FaultInstance(
            DUPLICATE, system, seq,
            {"copies": sorted(entries),
             "structural": any((seq, system, c) in structural for c, _, _ in entries)}))

    # Deliveries present in both but moved or mutated.
    for key, delivery in real_idx.items():
        if key[2] > 0:
            continue
        base = base_idx.get(key)
        if base is None:
            continue
        if delivery.at_t != base.at_t:
            labels = sorted(movers.get(key, set())) or ["delay"]
            instances.append(FaultInstance(
                DELAY if labels == ["delay"] else REORDER, key[1], key[0],
                {"ticks": delivery.at_t - base.at_t, "at_t": delivery.at_t,
                 "base_t": base.at_t, "mechanisms": labels},
            ))
        if delivery.mutation and not base.mutation:
            instances.append(FaultInstance(PARTIAL, key[1], key[0],
                                           {"mutation": delivery.mutation}))

    for system, lag in realised.read_lag.items():
        if lag > 0:
            instances.append(FaultInstance(STALE, system, detail={"lag": lag}))

    instances.sort(key=lambda i: i.ident)
    return instances, baseline, realised


def apply(baseline: Schedule, instances: Iterable[FaultInstance],
          profile: FaultProfile) -> Schedule:
    """Rebuild a schedule from the fault-free baseline plus the given instances.

    Applying every extracted instance reproduces the realised schedule;
    applying none returns the fault-free one. Any subset in between is a
    well-formed counterfactual world.
    """
    chosen = list(instances)
    by_kind: dict[str, list[FaultInstance]] = {k: [] for k in APPLY_ORDER}
    for inst in chosen:
        by_kind[inst.kind].append(inst)

    deliveries = {(d.event_seq, d.system, d.copy): d for d in baseline.deliveries}
    read_lag = {s: 0 for s in SYSTEMS}

    for inst in by_kind[DROP]:
        deliveries.pop((inst.event_seq, inst.system, 0), None)

    # Delay and reorder are both "this delivery arrived at another time"; the
    # kinds differ only in the mechanism the label records.
    for inst in by_kind[DELAY] + by_kind[REORDER]:
        key = (inst.event_seq, inst.system, 0)
        if key in deliveries:
            d = deliveries[key]
            deliveries[key] = Delivery(d.event_seq, d.system, inst.detail["at_t"],
                                       d.copy, d.mutation)

    for inst in by_kind[DUPLICATE]:
        for copy, at_t, mutation in inst.detail["copies"]:
            deliveries[(inst.event_seq, inst.system, copy)] = Delivery(
                inst.event_seq, inst.system, at_t, copy, mutation)

    for inst in by_kind[PARTIAL]:
        key = (inst.event_seq, inst.system, 0)
        if key in deliveries:
            d = deliveries[key]
            deliveries[key] = Delivery(d.event_seq, d.system, d.at_t, d.copy,
                                       inst.detail["mutation"])

    for inst in by_kind[STALE]:
        read_lag[inst.system] = inst.detail["lag"]

    ordered = sorted(deliveries.values(),
                     key=lambda d: (d.at_t, d.system, d.event_seq, d.copy))
    return Schedule(ordered, read_lag, profile, {})


def _canonical(schedule: Schedule) -> tuple:
    return (
        tuple(sorted((d.event_seq, d.system, d.at_t, d.copy, d.mutation)
                     for d in schedule.deliveries)),
        tuple(sorted(schedule.read_lag.items())),
    )


def round_trip_ok(case: Case, seed: int, profile: FaultProfile | None = None) -> bool:
    """Does applying every extracted instance reproduce the realised schedule?

    The decomposition is only meaningful if it is complete. Anything the
    extractor misses would sit in the residual and be silently attributed to
    the agent, which is the exact error this paper is about.
    """
    profile = profile or FaultProfile()
    instances, baseline, realised = extract(case, seed, profile)
    return _canonical(apply(baseline, instances, profile)) == _canonical(realised)


def stale_lag_of(instances: Iterable[FaultInstance], system: str) -> int:
    for inst in instances:
        if inst.kind == STALE and inst.system == system:
            return int(inst.detail.get("lag", 0))
    return 0
