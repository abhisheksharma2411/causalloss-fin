"""Build a self-contained arXiv submission and verify it compiles alone.

arXiv unpacks a submission into one directory and compiles there. Two things in
the working tree do not survive that: figures referenced as ``../figures/...``
escape the submission root, and there is no BibTeX run on their side. This
script flattens the tree, rewrites the paths, and then compiles the result in a
scratch directory with nothing else in it -- because the only way to know the
tarball works is to build it the way arXiv will.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
MAIN = "causalloss"


def build(staging: Path) -> list[str]:
    staging.mkdir(parents=True, exist_ok=True)
    tex = (PAPER / f"{MAIN}.tex").read_text()

    # Figures move to the submission root and lose their directory.
    tex = re.sub(r"\{\.\./figures/([^}]+)\}", r"{\1}", tex)
    # Tables and macros are inlined by name; they are copied flat below.
    tex = tex.replace("{tables/", "{tbl_")

    (staging / f"{MAIN}.tex").write_text(tex)
    carried = [f"{MAIN}.tex"]

    for pdf in sorted((ROOT / "figures").glob("*.pdf")):
        shutil.copy2(pdf, staging / pdf.name)
        carried.append(pdf.name)

    for table in sorted((PAPER / "tables").glob("*.tex")):
        shutil.copy2(table, staging / f"tbl_{table.name}")
        carried.append(f"tbl_{table.name}")

    shutil.copy2(PAPER / "numbers.tex", staging / "numbers.tex")
    carried.append("numbers.tex")

    # arXiv does not run BibTeX. The paper uses an inline thebibliography, so
    # there is nothing to carry -- but if that ever changes, the .bbl must come
    # with it, and this is where it would go.
    bbl = PAPER / f"{MAIN}.bbl"
    if bbl.exists():
        shutil.copy2(bbl, staging / bbl.name)
        carried.append(bbl.name)

    return carried


def verify(staging: Path) -> tuple[bool, str]:
    """Compile in a scratch copy containing only the submission files."""
    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "sub"
        shutil.copytree(staging, scratch)
        log = ""
        for _ in range(3):
            run = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", f"{MAIN}.tex"],
                cwd=scratch, capture_output=True, text=True,
            )
            log = run.stdout
        pdf = scratch / f"{MAIN}.pdf"
        if not pdf.exists():
            return False, log[-3000:]

        problems = []
        for pattern, label in (
            (r"Citation .* undefined", "undefined citation"),
            (r"Reference .* undefined", "undefined reference"),
            (r"File .* not found", "missing file"),
            (r"LaTeX Error", "LaTeX error"),
        ):
            hits = re.findall(pattern, log)
            if hits:
                problems.append(f"{len(hits)} {label}(s)")

        pages = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True)
        page_line = next((l for l in pages.stdout.splitlines() if l.startswith("Pages")), "")
        shutil.copy2(pdf, PAPER / f"{MAIN}-arxiv-verified.pdf")
        return (not problems), (page_line + ("; " + ", ".join(problems) if problems else "; clean"))


def abstract_text() -> str:
    """Extract the abstract with macros resolved, for pasting into the form."""
    tex = (PAPER / f"{MAIN}.tex").read_text()
    macros = dict(re.findall(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}",
                             (PAPER / "numbers.tex").read_text()))
    match = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    body = match.group(1) if match else ""
    for name, value in macros.items():
        body = body.replace(f"\\{name}{{}}", value).replace(f"\\{name}", value)
    body = re.sub(r"\\textbf\{([^}]*)\}", r"\1", body)
    body = re.sub(r"\\emph\{([^}]*)\}", r"\1", body)
    body = re.sub(r"\\texttt\{([^}]*)\}", r"\1", body)
    body = re.sub(r"\\textsuperscript\{([^}]*)\}", r"^\1", body)
    body = body.replace("\\%", "%").replace("\\$", "$").replace("\\&", "&")
    # ``\%\ `` in the source leaves a bare ``\ `` behind once the percent is
    # unescaped, so the pasted abstract read "100%\ of". Drop TeX's explicit
    # inter-word space and its tie, which the submission form renders
    # literally.
    body = body.replace("\\ ", " ").replace("~", " ")
    body = body.replace("---", "--").replace("``", '"').replace("''", '"')
    body = re.sub(r"\s+", " ", body).strip()
    return body


def main() -> int:
    staging = PAPER / "arxiv"
    if staging.exists():
        shutil.rmtree(staging)
    carried = build(staging)

    ok, detail = verify(staging)
    tarball = PAPER / f"{MAIN}-arxiv.tar.gz"
    with tarfile.open(tarball, "w:gz") as tar:
        for name in carried:
            tar.add(staging / name, arcname=name)

    abstract = abstract_text()
    (PAPER / "arxiv_abstract.txt").write_text(abstract + "\n")

    size_kb = tarball.stat().st_size / 1024
    print(f"  files       {len(carried)}")
    print(f"  tarball     {tarball.relative_to(ROOT)} ({size_kb:.0f} KB)")
    print(f"  standalone  {'OK' if ok else 'FAILED'}{detail}")
    print(f"  abstract    {len(abstract)} chars (arXiv limit 1920)")
    if len(abstract) > 1920:
        print("  WARNING: abstract exceeds the arXiv limit")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
