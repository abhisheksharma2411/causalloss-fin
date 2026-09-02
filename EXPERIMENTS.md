# Experiment log

Every iteration, including the ones that came back wrong. Results carry the
FinalityBench revision they ran against.

---

## Round 1 — the fault decomposition did not round-trip

**Ran.** Decompose each realised delivery schedule per fault family, by
building the `only:<family>` schedule and diffing it against the fault-free
one. Check that re-applying every extracted instance reproduces the realised
schedule.

**Result.** 91 of 240 episodes round-tripped. 149 failed.

**Diagnosis.** A property of the environment, not a coding slip. FinalityBench
draws its fault families independently but they do not *act* independently:
duplicate copies are placed relative to a delivery's already-delayed arrival, a
half-commit propagates to copies that exist only because duplication fired, and
whether a reorder swap is eligible depends on times delay has already moved.
Families that compose cannot be attributed by superposition.

**Change.** Decompose by diffing the *realised* schedule against the fault-free
one directly, which is complete by construction. The family label became an
annotation on an instance rather than its definition.

**Outcome.** 600 of 600 round-trip. Mean 7.1 instances per episode.

---

## Round 2 — reorder appeared never to fire

**Observed.** Zero instances were labelled `reorder`, though the benchmark
reports it firing 0.68 times per episode.

**Diagnosis.** Labels were assigned by asking each family *in isolation*
whether it moved a delivery. Reorder alone almost never fires: with no delays,
baseline arrival times are far apart and few pairs fall inside the swap window.

**Change.** Label by a but-for test taken *in context* — remove the family from
the full profile and ask whether the delivery still arrives when it did.

**Outcome.** 142 reorder-labelled instances appeared, about a fifth of moved
deliveries. This also confirms the composition finding from Round 1 from a
second direction: reorder's effect exists only in combination with delay.

---

## Round 3 — structural faults were invisible

**Observed.** For a `lost_settlement` task the dropped settlement — the fault
that defines the archetype — was not an extractable instance, because it was
applied to both the baseline and the realised schedule and cancelled in the
diff.

**Change.** Diff against a baseline that is both fault-free and forced-free, so
archetype-defining faults appear as instances flagged `structural`. They are
now intervenable, which matters: "would repairing the lost settlement have
helped" is exactly the question a reader wants asked.

---

## Round 4 — the planted suite was too easy, and one stratum was mislabelled

**Ran.** E1 against a first planted suite: one causal fault per episode (or
two), and nothing else present.

**Result.**

| method | top-1 single | top-1 pair |
|---|---:|---:|
| first_divergence | 100% | 100% |
| fault_single | 100% | 100% |
| joint_shapley | 100% | 0% |

**Diagnoses.** Three separate problems.

1. **No distractors.** With only the causal faults present, "name the earliest
   message" is a winning strategy because there is nothing else to name. A dumb
   heuristic scored 100%.
2. **The "pair" stratum was conjunctive, not overdetermined.** Two faults,
   neither harmful alone, harmful together — each is *necessary given the
   other*, so repairing either fixes it and one-at-a-time scoring handles the
   case fine. The stratum did not test what it was built to test.
3. **`joint_shapley` ranked incommensurable numbers.** Shapley values sum to
   the infrastructure share; step regrets do not live on that scale. A single
   agent step scored at the whole loss outranked two messages splitting it, so
   the method lost every pair.

**Changes.** Distractors, verified harmless *in the presence of* the causal set.
A fourth stratum, `overdetermined`: two faults, either sufficient alone, so
every one-at-a-time score is zero. And `joint_shapley` now ranks within
whichever side the exact identity says is responsible.

---

## Round 5 — final results

**E1, attribution accuracy** (545 planted episodes, 3 policies):

| method | single | conjunctive | overdetermined | agent | verdict |
|---|---:|---:|---:|---:|---:|
| last action | 0% | 0% | 0% | 100% | 33.0% |
| first divergence | 7% | 14% | 53% | 0% | 67.0% |
| **agent-only** | **0%** | **0%** | **0%** | 100% | **33.0%** |
| single-fault repair | 100% | 100% | **0%** | 100% | 100% |
| minimal sufficient | 100% | 100% | **100%** | 100% | 100% |
| joint Shapley | 100% | 100% | **100%** | 100% | 100% |

Agent-only's 33.0% verdict accuracy is the base rate of episodes in which the
agent is genuinely at fault. Single-fault repair's 0% on overdetermination is
arithmetic, not noise.

**E2, allocation.** Agent-only misfiles 100% of infrastructure episodes and
charges $114,383.40 to the agent. Every fault-intervening method reaches zero
allocation error — which is *by construction* once the identity is available,
and is reported as such rather than as an achievement.

**E3, interactions.** 27.8% of episodes with infrastructure loss do not
decompose additively; mean interaction gap $76.73. 5.6% are fully
overdetermined. Sampled Shapley sits within 1.88% (L1) of exact.

**E4, repair validation.** Of $82,488.60 available: minimal sufficient sets and
joint Shapley recover 100%, single-fault repair 82.4%, agent-only **0.0%**.

**E5, the landscape** (no planting, 3,852 episodes, decomposition exact on all):

| policy | mean loss | infrastructure | policy | irreducible |
|---|---:|---:|---:|---:|
| optimistic | $166.60 | **−6.8%** | 88.0% | 18.8% |
| rule-based | $213.63 | 75.1% | 10.2% | 14.7% |
| ReAct | $134.15 | 59.3% | 17.3% | 23.4% |
| finality gate | $31.37 | 0.0% | 0.0% | 100.0% |

The negative infrastructure share was not predicted. Faults help a policy that
ships on the first sign of payment, because the message it does not receive is
the one it would have acted on.

**E6, cost** (fresh world per method, so no method inherits another's cache):
minimal sufficient 2.3 replays/episode, agent-only 70.5, joint Shapley 280.1.
The cheapest exact method is also the most accurate.

---

## Reproduction

`make reproduce` runs the suite from a clean tree: FinalityBench fetched or
resolved, 15 tests, six experiments, three figures, five tables, and the paper.
No number in the paper is typed by hand.
