"""Locate FinalityBench (P1), which this paper consumes rather than rebuilds.

CausalLoss-Fin is a causal layer *over* FinalityBench: its environment, fault
engine, policies and effect-level oracle are the object of study, not something
reimplemented here.  Resolution order:

1. an installed ``finalitybench`` package;
2. a sibling checkout at ``../finalitybench/src`` (the usual local layout);
3. a clone under ``vendor/finalitybench`` that ``make setup`` creates.

Failing all three we raise with the exact command to fix it, rather than
falling back to a stand-in.  A stand-in would silently change what the paper is
about: the whole claim is that these results are computed against the published
P1 artifact.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P1_REPO = "https://github.com/abhisheksharma2411/finalitybench.git"
P1_VERSION = "1.0.0"

_CANDIDATES = (
    ROOT.parent / "finalitybench" / "src",
    ROOT / "vendor" / "finalitybench" / "src",
)


def ensure_p1() -> Path:
    """Put FinalityBench on ``sys.path`` and return the source root used."""
    try:
        import finalitybench  # noqa: F401
        return Path(finalitybench.__file__).resolve().parent.parent
    except ImportError:
        pass

    for candidate in _CANDIDATES:
        if (candidate / "finalitybench" / "__init__.py").exists():
            sys.path.insert(0, str(candidate))
            return candidate

    raise ImportError(
        "FinalityBench (P1) not found. This paper is a causal layer over it and "
        "does not reimplement it. Fetch it with:\n"
        f"    git clone {P1_REPO} vendor/finalitybench\n"
        "or place a checkout beside this repository."
    )


def clone_p1(dest: Path | None = None) -> Path:
    """Clone P1 at its released tag.  Used by ``make setup``."""
    dest = dest or (ROOT / "vendor" / "finalitybench")
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", f"v{P1_VERSION}", P1_REPO, str(dest)],
        check=True,
    )
    return dest


def p1_provenance() -> dict[str, str]:
    """Which P1 the numbers were produced against.  Printed with every result."""
    ensure_p1()
    import finalitybench

    source = Path(finalitybench.__file__).resolve().parents[2]
    revision = "unknown"
    try:
        out = subprocess.run(
            ["git", "-C", str(source), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        revision = out.stdout.strip() or "unknown"
    except Exception:
        pass
    return {
        "finalitybench_version": finalitybench.__version__,
        "finalitybench_path": str(source),
        "finalitybench_git": revision,
    }


ensure_p1()
