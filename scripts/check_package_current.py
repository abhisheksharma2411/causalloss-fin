"""Refuse to call a submission package ready when it is older than the paper.

``paper/make_arxiv.py`` extracts the tarball, builds it, and keeps the result
as ``*-arxiv-verified.pdf``. That file is the one to check before uploading,
which makes it exactly the file that causes harm when it is stale: it looks
authoritative and can be a revision behind. A reviewer caught one that was
twenty-eight minutes older than the paper it claimed to verify.

So compare modification times. The package must be at least as new as every
input the paper is built from.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"

#: Everything a rebuild would pick up. A change to any of these makes an older
#: package obsolete.
SOURCES = ("*.tex", "tables/*.tex")


def main() -> int:
    verified = next(PAPER.glob("*-arxiv-verified.pdf"), None)
    tarball = next(PAPER.glob("*-arxiv.tar.gz"), None)
    if verified is None or tarball is None:
        print("  no submission package built; run `make arxiv`")
        return 1

    inputs: list[Path] = []
    for pattern in SOURCES:
        inputs += [p for p in PAPER.glob(pattern)
                   if "arxiv" not in p.parts and "arxiv" not in p.name]
    inputs += [p for p in (ROOT / "figures").glob("*.pdf")]

    newest = max(inputs, key=lambda p: p.stat().st_mtime)
    stale = [a for a in (verified, tarball)
             if a.stat().st_mtime < newest.stat().st_mtime]

    if stale:
        for a in stale:
            print(f"  {a.name} is older than {newest.relative_to(ROOT)}")
        print("  the package does not match the paper; run `make arxiv`")
        return 1
    print(f"submission package is current with {newest.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
