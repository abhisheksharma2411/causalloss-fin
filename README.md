# CausalLoss-Fin

When a financial agent loses money, **whose fault was it — the agent's, or the
infrastructure it ran on?**

Published counterfactual attribution for agent failures will answer that
question with a step number. It will do so even when the answer is that a
settlement message was dropped and the agent never had a chance, because those
methods intervene on the agent's own steps and their causal models contain no
variable for the environment. Every dollar they explain gets charged to a
decision.

This is a causal layer over [FinalityBench](https://github.com/abhisheksharma2411/finalitybench)
that intervenes on **both**.

```
        do(A_k := a')                              do(f_i := absent)
   replace a decision, run forward            repair one dropped/delayed/
   under the same policy                      duplicated message, replay

                        \                    /
                         \                  /
                    exact three-way split of the loss

   L(pi,w)  =  [L(pi,w) - L(pi,w0)]  +  [L(pi,w0) - L(pi*,w0)]  +  L(pi*,w0)
                 infrastructure             policy                irreducible
```

The terms telescope, so there is no residual — which matters, because a residual
is where unattributed loss piles up, and unattributed loss in an agent-analysis
tool reads as the agent's fault. Verified exact on 3,852 of 3,852 episodes.

## The headline

545 episodes whose causes are **planted, not derived**, across three policies:

| method | single | conjunctive | overdetermined | agent | loss recovered by repairing it |
|---|---:|---:|---:|---:|---:|
| last action | 0% | 0% | 0% | 100% | 0.0% |
| **agent-only intervention** | **0%** | **0%** | **0%** | 100% | **0.0%** |
| single-fault repair | 100% | 100% | **0%** | 100% | 82.4% |
| **minimal sufficient set** | **100%** | **100%** | **100%** | **100%** | **100.0%** |
| **joint Shapley** | **100%** | **100%** | **100%** | **100%** | **100.0%** |

Agent-only intervention misfiles **100%** of infrastructure episodes and charges
**$114,383.40** of infrastructure-caused loss to the agent. Repairing what it
names recovers **$0 of $82,488**.

It is not a bad method. It answers a different question correctly.

## Two findings worth the space

**Interactions are not a corner case.** 27.8% of episodes with infrastructure
loss do not decompose additively, and on 5.6% every single-repair score is zero
while the total is not. Scoring messages one at a time is wrong there in
principle, not merely imprecise.

**The infrastructure effect can be negative.** A policy that ships on the first
sign of payment has an infrastructure effect of **−6.8%**: faults help it, on
net, because the message it does not receive is the one it would have acted on.
A method that can only add blame to the agent cannot represent that at all.

## Quick start

```bash
make setup          # virtualenv; fetches FinalityBench if no sibling checkout
make test           # 15 tests, incl. decomposition completeness over the corpus
make experiments    # E1-E6
make paper          # figures, tables, PDF
make reproduce      # all of it, from a clean tree
```

## Using it

```python
from causalloss.scm import World
from finalitybench.policies import ReActPolicy

world = World(case, ReActPolicy, seed=0)
factual = world.factual()

factual.terms()       # {'infrastructure': .., 'policy': .., 'irreducible': .., 'total': ..}
factual.check()       # True: the three terms sum to the loss, exactly
world.shapley()       # {message ident -> cents}, summing to the infrastructure effect
world.repair_effect(world.instances[0])   # loss avoided by un-dropping one message
```

## Layout

| path | what |
|---|---|
| `src/causalloss/_p1.py` | resolves FinalityBench; never substitutes a stand-in |
| `src/causalloss/faultgraph.py` | decompose a schedule into repairable messages |
| `src/causalloss/scm.py` | interventions, the three-way split, Shapley |
| `src/causalloss/attribution.py` | seven methods behind one interface |
| `src/causalloss/planted.py` | ground truth in four strata, with distractors |
| `experiments/` | E1–E6 |

## Documents

- [NOVELTY.md](NOVELTY.md) — what is new, against which verified prior work
- [EXPERIMENTS.md](EXPERIMENTS.md) — every iteration, including four that came back wrong
- [ASSUMPTIONS.md](ASSUMPTIONS.md) — choices made without asking
- [BLOCKERS.md](BLOCKERS.md) — no LLM-as-judge arm, and what that costs
- [REVIEW.md](REVIEW.md) — claim-to-evidence matrix and readiness decision

## Citation

See [CITATION.cff](CITATION.cff). MIT licensed. Consumes FinalityBench v1.0.0.
