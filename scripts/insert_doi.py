"""Insert a minted Zenodo DOI into the paper and CITATION.cff.

Run after the Zenodo deposit exists:

    .venv/bin/python scripts/insert_doi.py 10.5281/zenodo.NNNNNNNN

Idempotent: running it twice with the same DOI changes nothing.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = "ZENODO_DOI_PLACEHOLDER"
#: The paper ships saying the DOI is coming rather than showing a placeholder,
#: because a literal ZENODO_DOI_PLACEHOLDER in a posted preprint is worse than
#: an honest sentence. This is the sentence to replace once the DOI exists.
FORTHCOMING = "An archival DOI is forthcoming."


def main(doi: str) -> int:
    if not re.fullmatch(r"10\.5281/zenodo\.\d+", doi):
        print(f"not a Zenodo DOI: {doi}")
        return 1

    tex = ROOT / "paper" / "causalloss.tex"
    body = tex.read_text()
    if FORTHCOMING in body:
        escaped = doi.replace("_", r"\_")
        tex.write_text(body.replace(
            FORTHCOMING, f"It is archived at DOI \\texttt{{{escaped}}}."))
        print(f"  paper/causalloss.tex <- {doi}")
    elif PLACEHOLDER in body:
        tex.write_text(body.replace(PLACEHOLDER, doi.replace("_", r"\_")))
        print(f"  paper/causalloss.tex <- {doi}")
    elif doi in body:
        print("  paper already carries this DOI")
    else:
        print("  WARNING: no placeholder and no matching DOI in the paper")

    cff = ROOT / "CITATION.cff"
    text = cff.read_text()
    if "\ndoi:" in text:
        text = re.sub(r"\ndoi: .*", f"\ndoi: {doi}", text)
    else:
        # Zenodo's reader is strict: doi goes on its own unquoted line after
        # license, and date-released must stay unquoted or the whole file is
        # rejected with "Citation metadata load failed".
        text = text.replace("\nlicense: MIT\n", f"\nlicense: MIT\ndoi: {doi}\n")
    cff.write_text(text)
    print(f"  CITATION.cff <- {doi}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
