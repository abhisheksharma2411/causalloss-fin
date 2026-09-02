# Assumptions

Choices made without asking, with the reasoning.

## The causal model

1. **The reference position is held fixed across counterfactuals.** Excess loss
   is measured against the privileged finality reference computed in the
   factual world. Recomputing it in each counterfactual would mix two effects
   in one number; holding it fixed means a repaired message moves the policy's
   position and nothing else.

2. **A step's effect is the regret of its best alternative**, not a shift in an
   outcome distribution. The published methods resample under the same policy;
   with deterministic policies that changes nothing at all, so substitution is
   the only intervention available. The two coincide only under determinism,
   which is recorded as a limitation rather than glossed.

3. **Alternatives at a step are a fixed menu of seven dispositions** an operator
   would recognise, not the whole action space. A better alternative outside
   the menu would raise a step's measured effect, which would make agent-only
   attribution look *better*, not worse — so the choice does not flatter this
   paper's conclusion.

4. **The best implementable policy defines the irreducible share.** We use the
   benchmark's strongest unprivileged policy. A stronger one would move loss
   from the irreducible column into the policy column for every subject.

## The fault decomposition

5. **An instance is a difference between the realised and the fault-free
   schedule**, not a per-family contribution. Per-family decomposition was
   tried first and failed round-trip on 149 of 240 episodes, because the
   families compose: duplicates are placed relative to already-delayed times, a
   half-commit propagates to copies that only exist when duplication fired, and
   reorder eligibility depends on times delay has moved. The family label is
   therefore an annotation, assigned by a but-for test taken in context.

6. **An archetype's defining fault is intervenable**, flagged `structural`
   rather than baked into the background. Whether the settlement the processor
   never heard about "counts" as a cause is a judgement call; making it
   available and labelled lets a reader take the other view.

7. **Reordering is under-attributed in isolation and correctly attributed in
   context.** Asked alone, reorder appears never to fire, because its swaps only
   become eligible once delay has bunched arrivals together. The in-context
   but-for test recovers it.

## The planted suite

8. **Distractors are verified harmless in the presence of the causal set**, not
   merely harmless alone. Without distractors the task is trivial: an earlier
   version planted only causal faults and a name-the-earliest-message heuristic
   scored 100%.

9. **Overdetermination is defined strictly** — two faults, each producing
   exactly the same loss alone as together. This is rare (about 6% of episodes
   with infrastructure loss), so the stratum is small and pooled across three
   policies. The claim that single-effect scoring fails there is arithmetic;
   the rate at which that costs anything in practice rests on a small sample.

10. **Episodes are pooled across three policies** rather than drawn from one.
    Attribution conclusions should not be a property of one procedure's quirks,
    and pooling is also the only way to get a usable overdetermined sample.

## Scope

11. **One environment.** All faults are delivery-level, so infrastructure harms
    an agent only by corrupting what it can see. An environment where
    infrastructure moves money directly would need a wider variable set.

12. **Exact Shapley below thirteen instances, sampled above.** Episodes carry
    7.4 instances on average and at most 13, so most are exact; E3 reports the
    sampled estimate's agreement with the exact one rather than assuming it.
