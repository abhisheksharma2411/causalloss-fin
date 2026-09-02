# CausalLoss-Fin v1.0.0

A causal layer over FinalityBench that answers "was this the agent's fault or
the system's?" — exactly, and cheaply.

- **Joint intervention** on agent decisions and on individual dropped, delayed,
  duplicated, reordered and half-committed messages.
- **An exact three-way split** of any policy's loss into infrastructure, policy
  and irreducible shares. No residual term. Verified on 3,852/3,852 episodes.
- **Shapley allocation** across individual messages, summing to the
  infrastructure share by the efficiency axiom.
- **Minimal sufficient causes** — the smallest set of messages whose joint
  repair removes the loss. Exact on every stratum at 2.3 replays per episode.
- **Planted ground truth** in four strata, including overdetermination, with
  distractors verified harmless alongside the causal set.

## Headline

Agent-only intervention — the shape of published attribution for agent failures
— identifies 0% of infrastructure causes, misfiles 100% of infrastructure
episodes, charges $114,383.40 to the agent, and recovers $0 of $82,488 when its
recommendation is acted on. It is not a bad method; its causal model contains
no variable for the environment.

No language model was evaluated; the policies are deterministic procedures.
See `BLOCKERS.md`.

MIT licensed. Consumes FinalityBench v1.0.0.
