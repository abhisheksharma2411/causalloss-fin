"""E8 -- the worked example, emitted rather than transcribed.

The paper walks one episode: an order of a stated value, a settlement message
that never reaches the processor, a stated loss, and a Shapley split between
exactly two messages with the rest at zero. Every one of those figures was
typed in by hand, so re-running the corpus would leave them behind without any
of them turning red.

The episode is named rather than searched for, because the prose tells its
story and a rule picking "the first case that looks like this" would silently
swap in a different story with different words needed around it. What the rule
does instead is check: the case has to still have the shape the paper
describes -- the dropped message, two non-zero infrastructure shares, a
whole-dollar loss -- and the run fails loudly if it does not. So the narrative
stays a choice and the numbers stop being one.
"""

from __future__ import annotations

from _common import banner, policy_factory, provenance, save

from causalloss.attribution import INFRA, agent_only, joint_shapley
from causalloss.scm import World
from finalitybench.tasks import build_corpus

N_TASKS = 320
SEED = 0
POLICY = "react"
#: The episode the prose describes. Changing this means rewriting the prose.
TASK_ID = "public-0123"


def main() -> None:
    banner("E8 worked example")
    corpus = build_corpus(n_tasks=N_TASKS)
    matches = [c for c in corpus.cases if c.task_id == TASK_ID]
    if not matches:
        raise SystemExit(
            f"{TASK_ID} is not in the corpus any more. The worked example "
            f"describes a case that no longer exists; pick a new one and "
            f"rewrite the paragraph rather than leaving the prose as it is.")

    case = matches[0]
    world = World(case, policy_factory(POLICY), SEED)
    factual = world.factual()
    shap = joint_shapley(world, factual.trace)
    agent = agent_only(world, factual.trace)

    # Only the infrastructure causes are messages; Shapley also scores the
    # agent's alternative action at every step, and counting those was how an
    # earlier version of this script matched the wrong episode.
    infra = [c for c in shap.causes if c.kind == INFRA]
    nonzero = [c for c in infra if abs(c.score) > 0]

    shape = {
        "loss is a whole number of dollars": factual.infrastructure % 100 == 0,
        "exactly two messages carry the credit": len(nonzero) == 2,
        "they carry it equally": len({round(c.score) for c in nonzero}) == 1,
        "a message to the processor is among them": any(
            "processor" in c.label for c in nonzero),
        "the loss is attributed to infrastructure": factual.infrastructure > 0,
    }
    broken = sorted(k for k, ok in shape.items() if not ok)
    if broken:
        raise SystemExit(
            f"{TASK_ID} no longer has the shape the paper describes: {broken}. "
            f"Rewrite the worked example rather than publishing the old words "
            f"over new numbers.")

    save("e8_worked_example", {
        "provenance": provenance(),
        "config": {"n_tasks": N_TASKS, "seed": SEED, "policy": POLICY,
                   "task_id": TASK_ID},
        "shape_checks": shape,
        "episode": {
            "task_id": case.task_id,
            "archetype": case.archetype,
            "order_cents": case.amount,
            "infrastructure_cents": factual.infrastructure,
            "n_instances": len(world.instances),
            "shapley_infra_causes": len(infra),
            "shapley_nonzero": [
                {"cause": c.label, "cents": c.score} for c in nonzero],
            "share_each_cents": round(nonzero[0].score),
            #: Instances that received nothing. The paper's "the other five".
            "instances_given_nothing": len(world.instances) - len(nonzero),
            "agent_only_top_cents": agent.causes[0].score if agent.causes else 0,
            "agent_only_top_cause": agent.causes[0].label if agent.causes else "",
            "agent_only_top_step": agent.causes[0].ident if agent.causes else "",
        },
    })


if __name__ == "__main__":
    main()
