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


def git_revision() -> dict[str, str]:
    """Full commit SHA and whether the tree was dirty.

    The short form was used at first and every result file recorded
    ``unversioned``, because the experiments ran before the repository had a
    first commit. A reader could not map a result to a revision, which is the
    only reason to record one.
    """
    info = {"commit": "uncommitted", "dirty": "unknown"}
    try:
        head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                              capture_output=True, text=True, timeout=5)
        if head.returncode == 0 and head.stdout.strip():
            info["commit"] = head.stdout.strip()
        status = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"],
                                capture_output=True, text=True, timeout=5)
        if status.returncode == 0:
            info["dirty"] = "yes" if status.stdout.strip() else "no"
    except Exception:
        pass
    return info


def provenance(**extra: Any) -> dict[str, Any]:
    from causalloss import __version__, p1_provenance

    revision = git_revision()
    return {"version": __version__,
            "git_commit": revision["commit"], "git_dirty": revision["dirty"],
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
