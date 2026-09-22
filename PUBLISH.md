# Publishing

## 1. Push to GitHub

```bash
export GH_TOKEN=<token with repo scope>
gh repo create abhisheksharma2411/causalloss-fin --public \
  --description "Splitting financial agent loss between decisions and infrastructure faults" 
git remote add origin https://github.com/abhisheksharma2411/causalloss-fin.git
CRED='!f() { echo username=x-access-token; echo "password=$GH_TOKEN"; }; f'
git -c credential.helper="$CRED" push -u origin HEAD:main
git -c credential.helper="$CRED" push origin v1.0.1
gh release create v1.0.1 --title "CausalLoss-Fin v1.0.1" --notes-file RELEASE_NOTES.md
```

Keep the token in the environment; do not let it reach `.git/config`.

## 2. Zenodo — done

Concept DOI **10.5281/zenodo.22893020** (v1.0.1 = 22893021), minted
2026-09-22 and written into the paper and `CITATION.cff` by
`scripts/insert_doi.py`.

It took two attempts to understand why. Zenodo archives only **public** repos,
and only on a GitHub *release* that fires its webhook. The v1.0.0 release
predated the webhook, so it minted nothing and the repository sat without a DOI
for three weeks. The order that works is: repo public, toggle it on at
<https://zenodo.org/account/settings/github/> (this installs the webhook),
cut a release, then run `scripts/insert_doi.py <doi>`. Check the webhook exists
with `GET /repos/<owner>/<repo>/hooks` before assuming the toggle is enough.

Cite the **concept** DOI: it resolves to the latest version, which is what
FinalityBench and HoldSpec do.

## 3. arXiv

```bash
make arxiv    # paper/causalloss-arxiv.tar.gz, verified standalone
```

- **Primary:** `cs.AI`. Cross-list `cs.SE`.
- **ACM classes:** `I.2.11; D.2.5; C.2.4` — the same three FinalityBench
  carries, which keeps the series findable together.
- **Licence:** the arXiv perpetual non-exclusive licence, not CC BY. Every
  paper here is `\documentclass[conference]{IEEEtran}`, and IEEE's copyright
  transfer asks you to warrant you have not granted conflicting rights; a CC BY
  grant is irrevocable and world-wide. The code stays MIT regardless, which is
  where reuse of the artifact actually happens.
- Not `cs.LG`: nothing here trains or evaluates a learning method. The
  policies are deterministic procedures and the analysis is causal
  decomposition, so the category would misdirect readers looking for a
  learning contribution.
- **Abstract:** `paper/arxiv_abstract.txt` (under the 1,920 limit, macros resolved).
- **Compiler:** pdfLaTeX. No BibTeX needed.

FinalityBench is posted as arXiv:2609.04706 and the bibliography cites it.
