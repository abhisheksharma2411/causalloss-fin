# Review

## Claim to evidence

| # | Claim | Evidence | Status |
|---|---|---|---|
| 1 | The fault decomposition is complete | `tests::test_every_fault_is_recoverable_by_the_extractor`, 300 episodes × 5 seeds round-trip | measured |
| 2 | The three-way split is exact | `tests::test_three_way_split_sums_to_the_loss`; E5 reports 3,852/3,852 | measured |
| 3 | Shapley sums to the infrastructure share | `tests::test_shapley_sums_to_the_infrastructure_share` (efficiency axiom) | measured |
| 4 | Sampled Shapley tracks exact | E3: 1.88% L1 over 299 episodes; asserted in tests | measured |
| 5 | Agent-only attribution never names an infrastructure cause | `tests::test_agent_only_attribution_never_names_an_infrastructure_cause`; E1: 0% on all three infra strata | measured, and true by construction |
| 6 | It misfiles 100% of infrastructure episodes, $114,383.40 | E2 | measured |
| 7 | Repairing what it names recovers 0.0% of $82,488.60 | E4 | measured |
| 8 | Single-effect scoring fails on overdetermination | E1: 0%; `tests::test_joint_methods_find_causes_single_effect_methods_miss` | measured (arithmetic) |
| 9 | Minimal sufficient sets are exact on all four strata | E1: 100% × 4 | measured |
| 10 | 27.8% of episodes are non-additive | E3 | measured |
| 11 | Minimal sufficient is cheapest *and* exact (2.3 replays) | E6, fresh world per method | measured |
| 12 | The optimistic policy's infrastructure share is −6.8% | E5 | measured, unexplained |
| 13 | The finality gate's loss is 100% irreducible | E5 | measured; agrees with P1 by a different route |
| 14 | FinalityBench's fault families compose rather than superpose | Round-trip failure 149/240 under per-family decomposition, then 600/600 after the fix | measured |
| 15 | How an LLM judge would perform here | — | **not claimed** |
| 16 | That these conclusions hold for stochastic agents | — | **not claimed** |

## Reviewer red-team

**"This is CAR applied to finance."** The specification's own red-team warning,
and the right question. The answer is the variable set: CAR intervenes on agent
steps, we intervene on agent steps *and* individual messages, and the paper's
results are all about what the second set buys. Without it the paper should be
merged into the benchmark; with it, E1/E2/E4 measure a gap that agent-only
methods cannot close by being executed better.

**"You built the environment, so of course your method wins."** The strongest
version of this objection. Three answers. The ground truth is planted rather
than derived, so no method is scored against its own definition of a cause.
Distractors were added precisely because the first suite was trivially winnable,
and adding them broke a heuristic that had been scoring 100%. And the headline
gap is not a tuning outcome — a causal model without an infrastructure variable
cannot name an infrastructure cause in *any* environment where one exists.

**"Zero allocation error for four methods looks like a rigged metric."** It is,
in the sense that once fault interventions are available the agent/infrastructure
split follows from an identity. The paper says so in the same paragraph as the
table rather than claiming it as a win. The discriminating measurement is which
*message*, not which side.

**"Overdetermination is 6% of episodes — is this a real problem?"** The
frequency is small and the sample (70 episodes pooled over three policies) is
small with it. What is not small is that on those episodes single-effect
scoring returns zero for every candidate, so it does not degrade gracefully; it
returns nothing at all.

**"Deterministic policies are not agents."** Correct, and it is the largest
limitation. It is stated in the abstract, the introduction and the limitations,
along with the specific technical consequence: substitution and resampling
interventions coincide only under determinism.

## MVP versus flagship

| MVP requirement | Delivered |
|---|---|
| typed causal model | yes, stated formally in §V-A |
| 300 P1 traces | 3,852 episodes in E5; 545 planted |
| 3 fault families | **6**, decomposed to 7.4 individual messages/episode |
| vs a CAR-style baseline | yes, and it is the paper's central comparison |

Flagship items delivered: interaction allocations (Shapley), compound faults
(conjunctive and overdetermined strata), repair validation (E4), and a reusable
library. Not delivered: uncertainty intervals (unnecessary — replay is exact),
thousands of traces beyond the corpus, and any LLM baseline.

## Readiness

**Release the artifact: yes.** Complete, tested, reproducible, and the fault
decomposition is reusable by anyone doing counterfactual work on this benchmark.

**Submit the paper: yes, with the scope it states.** cs.AI primary, cross-list
cs.SE and cs.LG.

**The honest caveat.** A reviewer who reads "agent failures" and expects a
language model will hold the deterministic policies against it. The right next
step is to run the comparison with a stochastic agent, where our substitution
intervention and CAR's resampling intervention genuinely differ — that is the
one experiment that would materially strengthen the claim, and it needs a model
endpoint.
