"""Regenerate every figure from results/. No number is typed in here."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUT = ROOT / "figures"

INK, ACCENT, MUTED, GOOD = "#1b1b1b", "#b3411b", "#8a8a8a", "#1f5f8b"
plt.rcParams.update({
    "font.size": 8.5, "axes.edgecolor": INK, "axes.labelcolor": INK,
    "text.color": INK, "xtick.color": INK, "ytick.color": INK,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 200, "savefig.bbox": "tight",
})

ORDER = ["last_action", "first_divergence", "agent_only", "fault_single",
         "joint_greedy", "minimal_sufficient", "joint_shapley"]
LABEL = {
    "last_action": "last action", "first_divergence": "first divergence",
    "agent_only": "agent-only intervention", "fault_single": "single-fault repair",
    "joint_greedy": "joint, greedy", "minimal_sufficient": "minimal sufficient set",
    "joint_shapley": "joint Shapley",
}
OURS = {"minimal_sufficient", "joint_shapley", "joint_greedy"}


def load(name):
    return json.loads((RESULTS / f"{name}.json").read_text())


def fig1_accuracy():
    d = load("e1_attribution")
    rows = {r["method"]: r for r in d["rows"]}
    strata = [("single", "single cause"), ("conjunctive", "conjunctive pair"),
              ("overdetermined", "overdetermined pair"), ("agent", "agent at fault")]
    names = [n for n in ORDER if n in rows]

    fig, axes = plt.subplots(1, 4, figsize=(7.4, 2.5), sharey=True)
    for ax, (key, title) in zip(axes, strata):
        values = [rows[n][f"top1_{key}"] * 100 for n in names]
        colors = [GOOD if n in OURS else (ACCENT if n == "agent_only" else MUTED)
                  for n in names]
        ax.barh(range(len(names)), values, color=colors, height=0.65)
        ax.set_title(title, loc="left", fontsize=8.5)
        ax.set_xlim(0, 105)
        ax.set_xlabel("top-1 (%)")
    axes[0].set_yticks(range(len(names)), [LABEL[n] for n in names])
    axes[0].invert_yaxis()
    fig.suptitle("A method cannot name a cause its causal model does not contain",
                 x=0.012, ha="left", fontsize=9.5)
    fig.savefig(OUT / "fig1_accuracy.pdf")
    plt.close(fig)
    print("  fig1_accuracy.pdf")


def fig2_repair_cost():
    repair = {r["method"]: r for r in load("e4_repair")["rows"]}
    cost = {r["method"]: r for r in load("e6_cost")["rows"]}
    names = [n for n in ORDER if n in repair and n in cost]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.7))
    values = [repair[n]["loss_recovered_share"] * 100 for n in names]
    colors = [GOOD if n in OURS else (ACCENT if n == "agent_only" else MUTED)
              for n in names]
    ax1.barh(range(len(names)), values, color=colors, height=0.65)
    ax1.set_yticks(range(len(names)), [LABEL[n] for n in names])
    ax1.invert_yaxis()
    ax1.set_xlabel("loss removed by repairing what the method named (%)")
    ax1.set_title("Acting on the attribution", loc="left", fontsize=9)

    for n in names:
        x = cost[n]["replays_per_episode"]
        y = repair[n]["loss_recovered_share"] * 100
        colour = GOOD if n in OURS else (ACCENT if n == "agent_only" else INK)
        ax2.scatter(x, y, s=28, color=colour)
        ax2.annotate(LABEL[n], (x, y), textcoords="offset points",
                     xytext=(5, 3 if n != "joint_greedy" else -9),
                     fontsize=7, color=colour)
    ax2.set_xscale("log")
    ax2.set_xlabel("replays per episode (log)")
    ax2.set_ylabel("loss removed (%)")
    ax2.set_ylim(-6, 112)
    ax2.set_title("What it costs to be right", loc="left", fontsize=9)
    fig.savefig(OUT / "fig2_repair_cost.pdf")
    plt.close(fig)
    print("  fig2_repair_cost.pdf")


def fig3_landscape():
    d = load("e5_landscape")
    rows = d["rows"]
    names = [r["policy"] for r in rows]
    infra = [r["infrastructure"] / 100 for r in rows]
    policy = [r["policy_gap"] / 100 for r in rows]
    irreducible = [r["irreducible"] / 100 for r in rows]

    fig, ax = plt.subplots(figsize=(7.2, 2.5))
    y = range(len(names))
    left = [0.0] * len(names)
    for values, colour, label in ((infra, ACCENT, "infrastructure"),
                                  (policy, INK, "policy"),
                                  (irreducible, MUTED, "irreducible")):
        ax.barh(list(y), values, left=left, color=colour, height=0.6, label=label)
        left = [a + b for a, b in zip(left, values)]
    ax.set_yticks(list(y), names)
    ax.invert_yaxis()
    ax.axvline(0, lw=0.7, color=INK)
    ax.set_xlabel("total excess loss over the corpus ($)")
    ax.legend(frameon=False, fontsize=7.5, ncols=3, loc="lower right")
    ax.set_title("Whose fault is it? The same split, four policies", loc="left",
                 fontsize=9)
    fig.savefig(OUT / "fig3_landscape.pdf")
    plt.close(fig)
    print("  fig3_landscape.pdf")


def main():
    OUT.mkdir(exist_ok=True)
    fig1_accuracy()
    fig2_repair_cost()
    fig3_landscape()


if __name__ == "__main__":
    main()
