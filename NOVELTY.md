# Novelty

Every paper below was fetched and its authors, date and scope checked, rather
than recalled.

## The claim

Published counterfactual attribution for agent failures intervenes on the
agent's own steps. We are not aware of prior work that intervenes jointly on
agent decisions **and** on individual infrastructure faults, with ground truth
for both, and splits responsibility in money.

We do not claim to have invented counterfactual attribution for agents,
Shapley allocation, or minimal sufficient causes. Each is prior work and each
is cited. The contribution is the variable set and what including it reveals.

## Against the closest work

**Causal Agent Replay** (arXiv:2606.08275, Shah, Jun 2026) is the paper this
one is in conversation with. It models a run as a structural causal model,
applies a `do` operation to a step, re-executes forward under the same policy,
and reports the shift in the outcome distribution — with confidence intervals,
a point-of-commitment rule for the run-forward confound, Shapley credit
splitting, and ground-truth validation. It is a good method and our agent-only
baseline is it, reduced to essentials and if anything strengthened by exact
rather than sampled replay.

Its causal model contains agent steps and no environment variable. We verified
this against the paper. The consequence in an environment where messages are
dropped is not that the method performs badly; it is that the method answers a
different question, and this paper measures the difference: 0% identification
of infrastructure causes, 100% misattribution of infrastructure episodes, and
$0 of $82,488 in available loss recovered by repairing what it names.

**CausalFlow** (arXiv:2605.25338, Bonagiri, Borkar, Anderias, Rafatirad,
Homayoun, May 2026) computes step-level causal responsibility scores and
synthesises minimally edited repairs that flip the outcome. Repair is a real
advance over pure diagnosis. It repairs *agent steps*; where the fix is "make
the settlement message arrive", there is no step to edit.

**REFLECT** (arXiv:2606.09071, Lin, Wang, Kwok, Guo, Nale, Fleming, Cheng, Jun
2026) targets silent failures — the agent finishes and the answer is wrong with
no error signal — by diagnosing candidate steps, replaying with
diagnosis-specific patches, and using the verified outcome flip as contrastive
evidence. The patch-and-verify loop is close in spirit to our repair validation
(E4). The patches are applied to the agent's trace.

**Actual causality.** The structural-model account (Halpern, *Actual
Causality*, MIT Press 2016; Chockler and Halpern, JAIR 2004) is where minimal
sufficient causes and degree of responsibility come from, and overdetermination
is its standard hard case. We use the machinery rather than extend it: our
minimal sufficient set is the smallest set of messages whose joint repair
removes the loss.

**Shapley for root-cause analysis.** The value itself is Shapley (1953). Kelen,
Petreczky, Kersch and Benczúr (arXiv:2310.09961, Oct 2023) show that the
*asymmetric* variant produces counter-intuitive attributions outside a
restricted model class, which is why we use the standard symmetric value. Our
use is narrow: the infrastructure share comes from an exact identity, and
Shapley only divides it across messages, so the efficiency axiom is a check on
the implementation rather than a modelling assumption.

**FinalityBench** (this author, 2026) is the environment, consumed as a
released artifact rather than reimplemented.

## What is genuinely modest

The three-way split is a telescoping identity, not a theorem. Its value is that
it has no residual — and that matters mainly because a residual is where
unattributed loss would pile up, and unattributed loss in an agent-analysis tool
reads as the agent's fault.

The environment is one benchmark. The finding that agent-only attribution
misfiles infrastructure loss is, in a sense, true by construction: a model
without a variable cannot use it. What is not true by construction, and what
required measurement, is *how much* it costs, that repairing the named cause
recovers none of it, and that a quarter of episodes interact so that
one-at-a-time repair is wrong in principle rather than merely imprecise.

The negative infrastructure share for the optimistic policy was not predicted
and is not offered as a general result. It is reported because it is what the
data says.
