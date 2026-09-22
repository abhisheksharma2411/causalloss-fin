# Blockers

## 1. No language model endpoint — unresolved, and it shapes what this paper can claim

**What was blocked.** The specification asks for an LLM-as-judge baseline
alongside the trace heuristics and the intervention methods. No model API
credentials were available, the same wall the companion benchmark hit. No
attempt was made to find one: a sandbox correctly refused an environment scan
for credentials during the previous paper, and hunting for keys is not
something a research harness should do.

**What was done instead.** The LLM-as-judge arm is unrun and stated as unrun.
Two non-causal heuristics stand in as the cheap baselines — last-action and
first-divergence — and they play the role an LLM judge would: fast, plausible,
and wrong in a specific direction. External context is available and cited
rather than invented: Causal Agent Replay reports state-of-the-art step-level
accuracy for LLM-judge attribution at around 14% on the Who&When benchmark, so
the omitted baseline is one that published work already finds weak.

**What it costs.** The paper cannot say how an LLM judge would perform *in this
environment*. Given that such a judge reads traces rather than intervening, it
would share agent-only attribution's structural blind spot — there is no
infrastructure variable in a trace summary either — but that is an inference,
not a measurement, and it is not claimed as one.

**A second consequence, and it is real.** The policies whose failures are
attributed are deterministic procedures rather than stochastic agents. That
*sharpens* the causal analysis: interventions are exact single replays rather
than Monte Carlo estimates, so the three-way split needs no confidence interval
and overdetermination is detected exactly. It also narrows external validity,
because our agent-step intervention substitutes an action where the published
methods resample one, and those coincide only under determinism. This is stated
in the limitations rather than being left for a reader to notice.

## 2. Zenodo deposit — resolved 2026-09-22

Concept DOI **10.5281/zenodo.22893020**. The webhook path did work; it had
simply never been enabled for this repository, so the v1.0.0 release fired
nothing. See `PUBLISH.md` for the order that works.

## Not blockers

**FinalityBench (P1)** was available as a sibling checkout and is consumed
rather than reimplemented. `make setup` clones the released tag when no sibling
is present, and every result file records the exact revision it ran against.

**LaTeX** was available; the paper builds with zero undefined references.
