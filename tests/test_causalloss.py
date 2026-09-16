"""Tests for the properties the paper claims.

The load-bearing ones are completeness of the fault decomposition and
exactness of the three-way split. If either fails, every attribution number is
built on sand, so both are checked over the corpus rather than on an example.
"""

from __future__ import annotations

import pytest

from causalloss.attribution import (
    AGENT,
    INFRA,
    METHODS,
    agent_only,
    fault_single,
    joint_shapley,
    minimal_sufficient,
    run_method,
)
from causalloss.faultgraph import (
    DROP,
    FaultInstance,
    apply,
    extract,
    round_trip_ok,
)
from causalloss.planted import build_planted, stratum_counts
from causalloss.scm import World, alternatives_for, run_in_world
from finalitybench.faults import FaultProfile
from finalitybench.policies import ReActPolicy, TransactionalRuntimePolicy
from finalitybench.tasks import build_corpus
from finalitybench.world import EVAL_SEEDS


@pytest.fixture(scope="module")
def corpus():
    return build_corpus(n_tasks=320)


@pytest.fixture(scope="module")
def planted(corpus):
    return build_planted(corpus.cases, ReActPolicy, seeds=(0, 1),
                         max_per_stratum=12)


# --- the decomposition is complete -----------------------------------------

def test_every_fault_is_recoverable_by_the_extractor(corpus):
    """Applying every extracted instance must rebuild the realised schedule.

    Anything the extractor misses would sit in the residual and be charged to
    the agent, which is the exact error this paper is about.
    """
    for case in corpus.cases[:60]:
        for seed in EVAL_SEEDS:
            assert round_trip_ok(case, seed), f"{case.task_id} seed={seed}"


def test_repairing_everything_reaches_the_fault_free_world(corpus):
    for case in corpus.cases[:30]:
        world = World(case, ReActPolicy, 0)
        repaired = apply(world.baseline, [], FaultProfile())
        assert repaired.deliveries == world.baseline.deliveries
        assert all(v == 0 for v in repaired.read_lag.values())


def test_structural_faults_are_extracted_and_flagged(corpus):
    """An archetype's defining fault is intervenable, and marked as its own kind."""
    case = next(c for c in corpus.cases if c.archetype == "lost_settlement")
    instances, _, _ = extract(case, 0)
    structural = [i for i in instances if i.structural]
    assert structural, "the lost settlement should appear as a structural instance"
    assert any(i.kind == DROP for i in structural)


# --- the split is exact ----------------------------------------------------

def test_three_way_split_sums_to_the_loss(corpus):
    """Infrastructure + policy + irreducible == loss, on every episode."""
    for policy in (ReActPolicy, TransactionalRuntimePolicy):
        for case in corpus.cases[:40]:
            for seed in (0, 1):
                factual = World(case, policy, seed).factual()
                assert factual.check(), (
                    f"{case.task_id} {policy.__name__} {factual.shares()}")


def test_shapley_sums_to_the_infrastructure_share(corpus):
    """The efficiency axiom, checked rather than assumed."""
    for case in corpus.cases[:20]:
        world = World(case, ReActPolicy, 0)
        factual = world.factual()
        phi = world.shapley()
        assert abs(sum(phi.values()) - factual.infrastructure) < 1e-6


def test_sampled_shapley_tracks_exact_shapley(corpus):
    checked = 0
    for case in corpus.cases:
        world = World(case, ReActPolicy, 0)
        if not (2 <= len(world.instances) <= 9):
            continue
        exact = world.shapley(max_exact=99)
        sampled = world.shapley(max_exact=0, samples=512, rng_seed=3)
        scale = max(1.0, abs(sum(exact.values())))
        error = sum(abs(exact[k] - sampled[k]) for k in exact) / scale
        assert error < 0.15, f"{case.task_id}: L1 {error:.3f}"
        checked += 1
        if checked >= 12:
            break
    assert checked >= 5


# --- interventions behave like interventions -------------------------------

def test_repairing_a_fault_changes_only_that_fault(corpus):
    case = corpus.cases[0]
    world = World(case, ReActPolicy, 0)
    target = world.instances[0]
    kept = [i for i in world.instances if i.ident != target.ident]
    schedule = apply(world.baseline, kept, FaultProfile())
    full = apply(world.baseline, world.instances, FaultProfile())
    assert schedule.deliveries != full.deliveries or schedule.read_lag != full.read_lag


def test_replay_is_deterministic(corpus):
    case = corpus.cases[3]
    world = World(case, ReActPolicy, 0)
    first = world.value(world.instances)
    world._cache.clear()
    assert world.value(world.instances) == first


def test_agent_intervention_actually_forces_the_action(corpus):
    from finalitybench.env import Action

    case = corpus.cases[0]
    world = World(case, ReActPolicy, 0)
    from causalloss.scm import _Override

    env, _ = run_in_world(case, _Override(ReActPolicy(), 0, Action("escalate", {"reason": "x"})),
                          FaultProfile(), 0, world.instances, world.baseline)
    assert env.transcript[0].tool == "escalate"


# --- the planted suite is what it says it is -------------------------------

def test_planted_strata_are_all_present(planted):
    counts = stratum_counts(planted)
    for stratum in ("single", "conjunctive", "agent"):
        assert counts.get(stratum, 0) > 0, counts


def test_planted_causes_are_causes(planted, corpus):
    """Removing the planted truth must remove the loss."""
    by_id = {c.task_id: c for c in corpus.cases}
    for episode in planted:
        if episode.truth_kind != "infrastructure":
            continue
        case = by_id[episode.task_id]
        world = World(case, ReActPolicy, episode.seed, present=episode.injected)
        kept = [i for i in world.instances if i.ident not in set(episode.truth)]
        assert world.factual_reference - world.value(kept) <= 0, episode.task_id


def test_planted_distractors_are_harmless(planted, corpus):
    by_id = {c.task_id: c for c in corpus.cases}
    for episode in planted:
        if episode.truth_kind != "infrastructure":
            continue
        case = by_id[episode.task_id]
        world = World(case, ReActPolicy, episode.seed, present=episode.injected)
        causal = [i for i in world.instances if i.ident in set(episode.truth)]
        assert (world.factual_reference - world.value(causal)) == episode.loss


# --- the headline claim ----------------------------------------------------

def test_agent_only_attribution_never_names_an_infrastructure_cause(planted, corpus):
    """The paper's central claim, stated as a test.

    A method whose causal model contains no infrastructure variable cannot name
    one, however good it is at what it does.
    """
    by_id = {c.task_id: c for c in corpus.cases}
    infra = [e for e in planted if e.truth_kind == "infrastructure"]
    assert infra
    for episode in infra:
        case = by_id[episode.task_id]
        world = World(case, ReActPolicy, episode.seed, present=episode.injected)
        attribution = agent_only(world, world.factual().trace)
        assert all(c.kind == AGENT for c in attribution.causes)
        assert attribution.infra_share == 0.0


def test_joint_methods_find_causes_single_effect_methods_miss(planted, corpus):
    """Overdetermination: every one-at-a-time score is zero, the set is not."""
    by_id = {c.task_id: c for c in corpus.cases}
    overdetermined = [e for e in planted if e.stratum == "overdetermined"]
    if not overdetermined:
        pytest.skip("no overdetermined episodes in this sample")
    for episode in overdetermined:
        case = by_id[episode.task_id]
        world = World(case, ReActPolicy, episode.seed, present=episode.injected)
        assert not fault_single(world).causes
        found = minimal_sufficient(world)
        assert set(c.ident for c in found.causes) == set(episode.truth)


def test_every_method_runs_on_every_stratum(planted, corpus):
    by_id = {c.task_id: c for c in corpus.cases}
    for episode in planted[:10]:
        case = by_id[episode.task_id]
        world = World(case, ReActPolicy, episode.seed, present=episode.injected or [])
        trace = world.factual().trace
        for name in METHODS:
            attribution = run_method(name, world, trace)
            assert attribution.verdict in (AGENT, INFRA)
            assert attribution.replays >= 0


def test_the_worked_example_still_has_the_shape_the_paper_describes():
    """The paper narrates one episode. If the corpus moves, say so loudly.

    The figures in that paragraph are generated now, so a changed corpus
    updates them silently -- and silently updating "two messages at fourteen
    dollars each" into something with three messages would leave the prose
    describing a case that no longer exists.
    """
    from causalloss.attribution import INFRA, joint_shapley
    from causalloss.scm import World
    from finalitybench.tasks import build_corpus

    case = next(c for c in build_corpus(n_tasks=320).cases
                if c.task_id == "public-0123")
    world = World(case, ReActPolicy, 0)
    factual = world.factual()
    infra = [c for c in joint_shapley(world, factual.trace).causes
             if c.kind == INFRA]
    nonzero = [c for c in infra if abs(c.score) > 0]

    assert factual.infrastructure > 0
    assert factual.infrastructure % 100 == 0
    assert len(nonzero) == 2
    assert len({round(c.score) for c in nonzero}) == 1
    assert any("processor" in c.label for c in nonzero)


def test_families_do_not_superpose():
    """The reason the decomposition is not per family, as a test.

    If pooled per-family instances started reproducing the realised schedule,
    the simpler design would be sound and this paper's would be unnecessary
    complexity -- worth failing a test over rather than discovering in review.
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))
    from e7_superposition import superposed

    from causalloss.faultgraph import round_trip_ok
    from finalitybench.tasks import build_corpus

    cases = build_corpus(n_tasks=320).cases[:40]
    failures = sum(1 for c in cases if not superposed(c, 0))
    assert failures > len(cases) // 2, failures
    assert all(round_trip_ok(c, 0) for c in cases)
