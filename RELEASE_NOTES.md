# CausalLoss-Fin v1.0.2

A causal layer over FinalityBench that answers "was this the agent's fault or
the system's?" — exactly, and cheaply.

- **Joint intervention** on agent decisions and on individual dropped, delayed,
  duplicated, reordered and half-committed messages.
- **An exact three-way split** of any policy's loss into an infrastructure
  effect, a policy differential against the best implementable policy, and a
  reference-policy residual, with nothing left unattributed. Verified on
  3,852/3,852 episodes.
- **Shapley allocation** across individual messages, satisfying efficiency so
  the allocations sum to the infrastructure effect. The allocations are signed:
  a message whose repair would have increased the loss carries a negative one.
- **Minimal sufficient causes** — the smallest set of messages whose joint
  repair removes the loss. Exact on every stratum at 2.3 replays per episode.
- **Planted ground truth** in four strata, including overdetermination, with
  distractors verified harmless alongside the causal set.

## Headline

Agent-only intervention — the shape of published attribution for agent failures
— identifies 0% of infrastructure causes, misfiles 100% of infrastructure
episodes, charges $114,383.40 to the agent, and recovers $0 of $82,488 when its
recommendation is acted on. It is not a bad method; its causal model contains
no variable for the environment, so no infrastructure cause is expressible in
its output. That part is a proposition about the method and needs no corpus.
What the corpus measures is the size of the consequence.

## What changed since v1.0.1

Two external review passes. The substantive corrections:

**Shapley allocations are signed.** v1.0.1 called them shares and claimed
non-negativity in the additive case. Additivity of the value function does not
bound the sign, and a fault that helped the policy carries a negative
allocation. Corrected in the paper and in this file.

**One claim was false as arithmetic.** "The best accuracy-per-replay belongs to
minimal sufficient sets" does not hold as a ratio: first divergence gets 67.0
verdict points per replay against 43.5. The paper now claims what is true, that
minimal sufficient repair is the cheapest method exact on every planted
stratum, and concedes the ratio.

**The opening claim was too broad.** AgenticRAG-FP (arXiv:2608.20627) does
inject certified faults into retrieval hops, so it is untrue that prior
counterfactual attribution intervenes only on agent decisions. It is now cited
and differentiated: it measures whether the injected hop is recovered, not how
much of a realised cost each fault accounts for. Causely, DCFA and MP-Bench are
placed likewise, and FinalityBench is cited as arXiv:2609.04706.

**Scope is disclosed in the abstract**, not only in the limitations: the
subjects are deterministic programmatic policies, not language-model agents.

**Cost is counted in replays.** Wall-clock timings moved threefold between runs
that changed no code, so printing them let `make reproduce` rewrite the paper.

**The comparison baseline is named for what it is**, a CAR-shaped agent-only
baseline reproducing those methods' variable scope, not the systems themselves.

Intervals now state their level and replicate count. `make reproduce` ends in
the provenance and prose-number gates. `__version__` had still reported 1.0.0.

## What changed in v1.0.1

**Terminology.** The three telescoping terms are no longer called "shares".
Two of them go negative — the infrastructure effect when faults help a policy
on net, the policy differential whenever the subject beats the reference on a
task — and a share that can be negative is not a share. `Factual.shares()` is
now `Factual.terms()`, with `shares()` kept as an alias so the v1.0.0 API does
not break.

**Uncertainty on prevalence claims.** Rates of non-additivity and
overdetermination are estimates from a generated population and now carry
intervals, bootstrapped over tasks rather than episodes because episodes from
one task share its amount, archetype and fault draw: non-additive 27.8%
[23.3, 32.3], overdetermined 5.6% [3.1, 8.7], over 219 tasks. The telescoping
identity is algebra and is reported without an interval.

**The search cap does not bind.** The minimal-sufficient search stops at three
messages, which would make perfect recovery conditional on the cases that fit
inside it. Over 320 episodes the largest set found holds two and the cap binds
on none.

**A claim that was not reproducible is now measured.** The paper had said an
abandoned per-family decomposition failed to reproduce the realised schedule on
"149 of 240" episodes, a figure carried from a commit message that no results
file contained. E7 reconstructs that design: it fails on 199 of 240, 82.9%,
while the current decomposition reproduces all 240.

**Provenance is enforced.** `scripts/check_provenance.py` fails if any result
file comes from a dirty tree or if results span more than one revision.
Dirtiness is computed over inputs, excluding `results/`, `figures/` and
`paper/`, which a run writes itself.

**Prose numbers are linted.** `scripts/check_prose_numbers.py` reports any
numeric literal in the paper that neither a results file nor the claim list
supports. Deliberate constants are recorded in
`paper/prose_numbers_allowed.json` with a reason.

No language model was evaluated; the policies are deterministic procedures.
See `BLOCKERS.md`.

MIT licensed. Consumes FinalityBench v1.0.0.
