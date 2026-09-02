# Publishing

## 1. Push to GitHub

```bash
export GH_TOKEN=<token with repo scope>
gh repo create abhisheksharma2411/causalloss-fin --public \
  --description "Splitting financial agent loss between decisions and infrastructure faults" 
git remote add origin https://github.com/abhisheksharma2411/causalloss-fin.git
CRED='!f() { echo username=x-access-token; echo "password=$GH_TOKEN"; }; f'
git -c credential.helper="$CRED" push -u origin HEAD:main
git -c credential.helper="$CRED" push origin v1.0.0
gh release create v1.0.0 --title "CausalLoss-Fin v1.0.0" --notes-file RELEASE_NOTES.md
```

Keep the token in the environment; do not let it reach `.git/config`.

## 2. Zenodo

The GitHub–Zenodo webhook did **not** list a newly created repository on this
account even after an explicit "Sync now", so prefer the manual deposit:

```bash
git archive --format=zip --prefix=causalloss-fin-1.0.0/ v1.0.0 \
  -o ~/Downloads/causalloss-fin-v1.0.0.zip
```

Upload at <https://zenodo.org/uploads/new> as **Software**, with the metadata in
`CITATION.cff`, and add a related identifier: *is supplement to* the GitHub URL.
Also add *is derived from* the FinalityBench DOI once that exists.

Then:

```bash
.venv/bin/python scripts/insert_doi.py 10.5281/zenodo.NNNNNNNN
make paper
```

## 3. arXiv

```bash
make arxiv    # paper/causalloss-arxiv.tar.gz, verified standalone
```

- **Primary:** `cs.AI`. Cross-list `cs.SE`, `cs.LG`.
- **Abstract:** `paper/arxiv_abstract.txt` (under the 1,920 limit, macros resolved).
- **Compiler:** pdfLaTeX. No BibTeX needed.

Submit after FinalityBench, and cite its arXiv ID in place of the bare GitHub
URL once it exists.
