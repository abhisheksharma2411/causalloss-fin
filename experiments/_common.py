"""Shared plumbing for the experiment scripts."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)


#: Paths that are outputs of a run rather than inputs to it. A run writes its
#: own results, and on the second experiment of a batch the first one's output
#: would otherwise make the tree look dirty and mark every later result as
#: irreproducible. What has to be clean is the code and the data that went in.
GENERATED = ("results/", "figures/", "paper/")


def _dirty_inputs(root) -> str:
    """Uncommitted changes outside the generated directories."""
    out = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"],
        capture_output=True, text=True, timeout=10,
    ).stdout.splitlines()
    changed = []
    for line in out:
        path = line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ")[-1]
        if not any(path.startswith(g) for g in GENERATED):
            changed.append(path)
    return "; ".join(sorted(changed))


def git_revision() -> dict[str, str]:
    """Full commit SHA and whether the tree was dirty.

    The short form was used at first and every result file recorded
    ``unversioned``, because the experiments ran before the repository had a
    first commit. A reader could not map a result to a revision, which is the
    only reason to record one.

    When the tree is dirty the offending paths are recorded too. A bare
    ``"git_dirty": "yes"`` tells a reader that something was uncommitted but
    not what, so the cause has to be guessed from the build system -- and two
    reviewers in a row guessed ``distclean``, which is filtered and was not it.
    Naming the paths turns that into a fact the file already contains.
    """
    info = {"commit": "uncommitted", "dirty": "unknown"}
    try:
        head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                              capture_output=True, text=True, timeout=5)
        if head.returncode == 0 and head.stdout.strip():
            info["commit"] = head.stdout.strip()
        dirty = _dirty_inputs(ROOT)
        info["dirty"] = "yes" if dirty else "no"
        if dirty:
            info["dirty_paths"] = dirty
    except Exception:
        pass
    return info


def provenance(**extra: Any) -> dict[str, Any]:
    from causalloss import __version__, p1_provenance

    revision = git_revision()
    return {"version": __version__,
            "git_commit": revision["commit"], "git_dirty": revision["dirty"],
            # Only present when the tree was dirty, and then it says what was
            # uncommitted so nobody has to infer it from the build system.
            **({"git_dirty_paths": revision["dirty_paths"]}
               if revision.get("dirty_paths") else {}),
            "command": " ".join(sys.argv),
            "python": platform.python_version(),
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            **p1_provenance(), **extra}


def save(name: str, payload: dict[str, Any]) -> Path:
    path = RESULTS / f"{name}.json"
    path.write_text(json.dumps(payload, indent=1))
    print(f"  wrote {path.relative_to(ROOT)}")
    return path


def load(name: str) -> dict[str, Any]:
    return json.loads((RESULTS / f"{name}.json").read_text())


def banner(title: str) -> None:
    print(f"\n=== {title} ===")


#: The policies attribution is run over. ReAct is the default subject: it is
#: competent enough that its losses are interesting and simple enough that its
#: traces are short.
POLICY_NAMES = ("react", "rule_based", "optimistic", "transactional")


def policy_factory(name: str):
    from finalitybench import policies as P

    return {
        "react": P.ReActPolicy, "rule_based": P.RuleBasedPolicy,
        "optimistic": P.OptimisticPolicy, "transactional": P.TransactionalRuntimePolicy,
        "eager": P.EagerPolicy, "majority": P.MajorityVotePolicy,
    }[name]
