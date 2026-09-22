# CausalLoss-Fin v1.0.1

A causal layer over FinalityBench that answers "was this the agent's fault or
the system's?" — exactly, and cheaply.

- **Joint intervention** on agent decisions and on individual dropped, delayed,
  duplicated, reordered and half-committed messages.
- **An exact three-way split** of any policy's loss into an infrastructure
  effect, a policy differential against the best implementable policy, and a
  reference-policy residual, with nothing left unattributed. Verified on
  3,852/3,852 episodes.
- **Shapley allocation** across individual messages, summing to the
  infrastructure effect by the efficiency axiom. These are shares; the three
  terms above are not, because two of them go negative.
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

## What changed since v1.0.0

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
