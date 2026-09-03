"""Generate every LaTeX table and numeric macro from results/."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
TABLES = ROOT / "paper" / "tables"

LABEL = {
    "last_action": "last action", "first_divergence": "first divergence",
    "agent_only": "agent-only intervention", "fault_single": "single-fault repair",
    "joint_greedy": "joint, greedy", "minimal_sufficient": "minimal sufficient set",
    "joint_shapley": "joint Shapley",
}
ORDER = ["last_action", "first_divergence", "agent_only", "fault_single",
         "joint_greedy", "minimal_sufficient", "joint_shapley"]
OURS = {"minimal_sufficient", "joint_shapley", "joint_greedy"}


def load(name):
    return json.loads((RESULTS / f"{name}.json").read_text())


def pct(x, places=1):
    return f"{x*100:.{places}f}"


def money(cents):
    return f"{cents/100:,.2f}"


def table_accuracy(d):
    rows = {r["method"]: r for r in d["rows"]}
    out = [r"\begin{tabular}{lrrrrr}", r"\toprule",
           r"& \multicolumn{4}{c}{top-1 identification (\%)} & \\",
           r"\cmidrule(lr){2-5}",
           r"method & single & conjunctive & overdet. & agent & verdict (\%) \\",
           r"\midrule"]
    for name in ORDER:
        r = rows[name]
        bold = r"\bfseries " if name in OURS else ""
        out.append(
            f"{bold}{LABEL[name]} & {pct(r['top1_single'],0)} & "
            f"{pct(r['top1_conjunctive'],0)} & {pct(r['top1_overdetermined'],0)} & "
            f"{pct(r['top1_agent'],0)} & {pct(r['verdict_overall'],1)} \\\\")
    out += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(out)


def table_allocation(d):
    rows = {r["method"]: r for r in d["rows"]}
    out = [r"\begin{tabular}{lrrr}", r"\toprule",
           r"method & allocation error (\%) & misattributed (\%) & \$ charged to agent \\",
           r"\midrule"]
    for name in ORDER:
        r = rows[name]
        bold = r"\bfseries " if name in OURS else ""
        out.append(f"{bold}{LABEL[name]} & {pct(r['mean_allocation_error'])} & "
                   f"{pct(r['misattribution_rate'],0)} & "
                   f"{money(r['dollars_wrongly_charged_to_agent'])} \\\\")
    out += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(out)


def table_repair(repair, cost):
    r_rows = {r["method"]: r for r in repair["rows"]}
    c_rows = {r["method"]: r for r in cost["rows"]}
    out = [r"\begin{tabular}{lrrrr}", r"\toprule",
           r"method & loss removed (\%) & fully fixed (\%) & replays/ep. & ms/ep. \\",
           r"\midrule"]
    for name in ORDER:
        r, c = r_rows[name], c_rows[name]
        bold = r"\bfseries " if name in OURS else ""
        out.append(f"{bold}{LABEL[name]} & {pct(r['loss_recovered_share'])} & "
                   f"{pct(r['fully_fixed_rate'])} & {c['replays_per_episode']:.1f} & "
                   f"{c['ms_per_episode']:.1f} \\\\")
    out += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(out)


def table_landscape(d):
    out = [r"\begin{tabular}{lrrrr}", r"\toprule",
           r"policy & mean loss (\$) & infrastructure (\%) & policy (\%) & irreducible (\%) \\",
           r"\midrule"]
    for r in d["rows"]:
        out.append(f"{r['policy'].replace('_',' ')} & {money(r['mean_loss'])} & "
                   f"{pct(r['infrastructure_share'])} & {pct(r['policy_share'])} & "
                   f"{pct(r['irreducible_share'])} \\\\")
    out += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(out)


def table_archetype(d):
    """Infrastructure share by archetype, averaged over the reported policies."""
    agg: dict[str, dict[str, float]] = {}
    for r in d["by_archetype"]:
        if r["policy"] == "transactional":
            continue
        bucket = agg.setdefault(r["archetype"], {"infra": 0.0, "policy": 0.0,
                                                 "irred": 0.0, "total": 0.0})
        bucket["infra"] += r["infrastructure"]
        bucket["policy"] += r["policy_gap"]
        bucket["irred"] += r["irreducible"]
        bucket["total"] += r["total"]
    out = [r"\begin{tabular}{lrrr}", r"\toprule",
           r"archetype & infrastructure (\%) & policy (\%) & irreducible (\%) \\",
           r"\midrule"]
    for name, b in sorted(agg.items(), key=lambda kv: -kv[1]["infra"] / max(1, kv[1]["total"])):
        t = max(1.0, b["total"])
        out.append(f"{name.replace('_', ' ')} & {pct(b['infra']/t)} & "
                   f"{pct(b['policy']/t)} & {pct(b['irred']/t)} \\\\")
    out += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(out)


def macros(e1, e2, e3, e4, e5, e6):
    a = {r["method"]: r for r in e1["rows"]}
    alloc = {r["method"]: r for r in e2["rows"]}
    rep = {r["method"]: r for r in e4["rows"]}
    cost = {r["method"]: r for r in e6["rows"]}
    land = {r["policy"]: r for r in e5["rows"]}
    defs = {
        "nPlanted": e1["n_episodes"],
        "nSingle": e1["strata"]["single"],
        "nConjunctive": e1["strata"]["conjunctive"],
        "nOverdetermined": e1["strata"]["overdetermined"],
        "nAgentStratum": e1["strata"]["agent"],
        "nPolicies": len(e1["policies"]),
        "agentOnlyInfra": pct(a["agent_only"]["top1_single"], 0),
        "agentOnlyVerdict": pct(a["agent_only"]["verdict_overall"], 1),
        "agentOnlyMisattr": pct(alloc["agent_only"]["misattribution_rate"], 0),
        "agentOnlyDollars": money(alloc["agent_only"]["dollars_wrongly_charged_to_agent"]),
        "agentOnlyRepair": pct(rep["agent_only"]["loss_recovered_share"], 1),
        "faultSingleOverdet": pct(a["fault_single"]["top1_overdetermined"], 0),
        "faultSingleRepair": pct(rep["fault_single"]["loss_recovered_share"], 1),
        "minSuffOverdet": pct(a["minimal_sufficient"]["top1_overdetermined"], 0),
        "minSuffRepair": pct(rep["minimal_sufficient"]["loss_recovered_share"], 1),
        "minSuffReplays": f"{cost['minimal_sufficient']['replays_per_episode']:.1f}",
        "shapleyReplays": f"{cost['joint_shapley']['replays_per_episode']:.1f}",
        "agentOnlyReplays": f"{cost['agent_only']['replays_per_episode']:.1f}",
        "dollarsAvailable": money(rep["minimal_sufficient"]["dollars_available"]),
        "additiveRate": pct(e3["additive_rate"], 1),
        "nonAdditiveRate": pct(1 - e3["additive_rate"], 1),
        "overdetRate": pct(e3["overdetermined_rate"], 1),
        "interactionGap": money(e3["mean_interaction_gap"]),
        "shapleyError": pct(e3["shapley_sampled_vs_exact_l1"], 2),
        "meanInstances": f"{e3['mean_instances']:.1f}",
        "maxInstances": e3["max_instances"],
        "decompExact": e5["decomposition_exact"],
        "reactInfra": pct(land["react"]["infrastructure_share"], 1),
        "reactPolicy": pct(land["react"]["policy_share"], 1),
        "ruleInfra": pct(land["rule_based"]["infrastructure_share"], 1),
        "optInfra": pct(land["optimistic"]["infrastructure_share"], 1),
        "optPolicy": pct(land["optimistic"]["policy_share"], 1),
        "gateIrreducible": pct(land["transactional"]["irreducible_share"], 1),
        "gateMeanLoss": money(land["transactional"]["mean_loss"]),
        "negPolicyRate": pct(max(r.get("negative_policy_share_rate", 0.0)
                                 for r in e5["rows"]), 1),
        "negPolicyWorst": money(min(r.get("most_negative_policy_share", 0)
                                    for r in e5["rows"])),
    }
    lines = [r"% Generated by paper/make_tables.py -- do not edit."]
    for key, value in defs.items():
        lines.append(rf"\newcommand{{\{key}}}{{{value}}}")
    return "\n".join(lines)


def main():
    TABLES.mkdir(parents=True, exist_ok=True)
    e1, e2, e3 = load("e1_attribution"), load("e2_allocation"), load("e3_shapley")
    e4, e5, e6 = load("e4_repair"), load("e5_landscape"), load("e6_cost")
    (TABLES / "accuracy.tex").write_text(table_accuracy(e1))
    (TABLES / "allocation.tex").write_text(table_allocation(e2))
    (TABLES / "repair.tex").write_text(table_repair(e4, e6))
    (TABLES / "landscape.tex").write_text(table_landscape(e5))
    (TABLES / "archetype.tex").write_text(table_archetype(e5))
    (ROOT / "paper" / "numbers.tex").write_text(macros(e1, e2, e3, e4, e5, e6) + "\n")
    for f in sorted(TABLES.glob("*.tex")):
        print(f"  {f.relative_to(ROOT)}")
    print("  paper/numbers.tex")


if __name__ == "__main__":
    main()
