# Peer review — CausalLoss-Fin

Adversarial review run 2026-09-03, after an external review of the companion
paper found three errors this project's self-assessment had missed. Every claim
below was checked against the artifact, not against the prose.

**Recommendation: major revision.** The central comparison is sound and the
decomposition is genuinely exact, but two claims are stated more strongly than
the evidence supports and the statistical treatment is absent.

---

## Major

### 1. The "policy" share is not non-negative, and the paper implies it is

The three-way split is presented as an attribution: infrastructure, policy,
irreducible. The policy term is `L(pi,w0) - L(pi*,w0)`, and `pi*` is the
benchmark's best implementable policy, not a per-task optimum. On **46 of 480
episodes (9.6%)** that term is negative, reaching **-$1,442.60**: the subject
policy beat the reference on that task.

A negative "policy share" is not meaningless — it says this policy did better
than the strong baseline here — but the paper never says the term can go
negative, and a reader will take a three-way split of a loss to be a partition
into non-negative parts. This is the same defect the external reviewer found in
the companion paper's "excess loss", which also admits negative values.

**Fix:** rename the term (*policy differential* rather than *policy share*),
state its sign convention, report how often it is negative, and either report a
per-task optimum or stop describing `pi*` as a bound.

### 2. No uncertainty is reported anywhere

545 planted episodes and 3,852 landscape episodes are not independent
observations. They are the same 321 tasks under 5 correlated fault seeds and 3
policies, with twin pairs adding further dependence. Every headline number —
0% identification, 100% misattribution, 27.8% non-additive — is a point
estimate with no interval.

**Fix:** hierarchical bootstrap over tasks then seeds; paired bootstrap for
method comparisons. The 5.6% overdetermination rate especially needs an
interval, since the stratum it supports has only 70 episodes.

### 3. The headline is true by construction, and that belongs in the abstract

"Agent-only intervention identifies 0% of infrastructure causes" follows from
the method having no infrastructure variable. The paper says this in
Section VII-A and the test suite asserts it, but the abstract presents it as an
empirical finding. What is genuinely measured is the *magnitude*: $114,383.40
misfiled, $0 of $82,488.60 recovered, and the 27.8% non-additivity that makes
one-at-a-time repair wrong in principle.

**Fix:** state the structural claim as structural in the abstract, and let the
measured quantities carry the empirical weight.

---

## Moderate

### 4. Result provenance is broken

Every result file records `git: unversioned`. The experiments ran before the
repository's first commit, so there was no HEAD to name. A reader cannot map a
result to a revision, which is the entire purpose of recording one.

### 5. The minimal-sufficient search cap is unexamined

`minimal_sufficient` searches sets up to size 3 and returns nothing beyond it.
Checked over 51 episodes with infrastructure loss it never returned empty and
never needed size 3 — so the cap does not bind on this corpus. That is a good
result and it is not in the paper. As written, a reader cannot tell whether the
method's perfect score depends on the cap.

### 6. The overdetermined stratum is small

70 episodes pooled across three policies, from a phenomenon occurring in 5.6%
of episodes. The claim that single-effect scoring returns zero there is
arithmetic and does not need a large sample. The claim about how often that
matters in practice does.

---

## Minor

- `first_divergence` scores 52.9% on overdetermined episodes, above chance,
  and the paper does not explain why. Worth one sentence: with two causal
  faults among roughly six, naming the earliest is not a bad guess.
- The seven-action alternative menu is stated as a limitation but its effect
  direction is only asserted. It is worth noting explicitly that a richer menu
  would raise agent-only's measured effect, so the choice does not flatter this
  paper's conclusion.
- Style: the abstract packs eight quantities into one paragraph, and the
  discussion uses slogan headings. Both are patterns flagged in the companion
  review.

## What holds up

The decomposition is exact on 3,852 of 3,852 episodes and the test suite checks
it rather than assuming it. Shapley sums to the infrastructure share by the
efficiency axiom, verified. The planted suite uses distractors verified harmless
alongside the causal set, which was added specifically because an earlier
version was trivially winnable. The three compared methods were each read and
their scope confirmed from the source papers rather than from summaries.
