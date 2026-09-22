# CausalLoss-Fin -- attributing financial agent loss to decisions and to faults.
#
#   make setup        virtualenv, and fetch FinalityBench (P1) if it is absent
#   make test         property tests, including decomposition completeness
#   make experiments  run E1-E6 and write results/
#   make figures      regenerate figures from results/
#   make tables       regenerate LaTeX tables and macros from results/
#   make paper        build paper/causalloss.pdf
#   make arxiv        build and verify a self-contained arXiv submission
#   make verify       provenance and prose-number gates over the built paper
#   make reproduce    all of the above, from a clean tree, ending in verify

PY  := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: setup p1 test experiments figures tables paper arxiv verify reproduce clean distclean

setup: $(PY) p1

$(PY):
	python3 -m venv .venv
	$(PIP) install --quiet --upgrade pip
	$(PIP) install --quiet -r requirements.txt

# This paper is a causal layer over FinalityBench and does not reimplement it.
# A sibling checkout is used when present; otherwise the released tag is cloned.
p1:
	@$(PY) -c "import sys; sys.path.insert(0,'src'); \
	from causalloss._p1 import ensure_p1, clone_p1, p1_provenance; \
	import pathlib; \
	(ensure_p1() if any((pathlib.Path('../finalitybench/src')/'finalitybench').glob('__init__.py')) else clone_p1()); \
	print('finalitybench:', p1_provenance())" 2>/dev/null || \
	$(PY) -c "import sys; sys.path.insert(0,'src'); \
	from causalloss._p1 import clone_p1; print('cloned to', clone_p1())"

test: setup
	$(PY) -m pytest

experiments: setup
	cd experiments && ../$(PY) run_all.py

figures: setup
	$(PY) figures/make_figures.py

tables: setup
	$(PY) paper/make_tables.py

paper: tables figures
	cd paper && latexmk -pdf -interaction=nonstopmode -halt-on-error causalloss.tex
	@echo "built paper/causalloss.pdf"

arxiv: paper
	$(PY) paper/make_arxiv.py

# The gates a finished paper has to pass. Not a ``## help'' comment on the
# target line: this Makefile has no help target, and make would read the words
# after the colon as prerequisites.
verify:
	$(PY) scripts/check_provenance.py
	$(PY) scripts/check_prose_numbers.py
	$(PY) scripts/check_package_current.py

reproduce: distclean setup test experiments figures tables paper arxiv verify
	@echo
	@echo "reproduce complete -- paper/causalloss.pdf, gates passed"

clean:
	rm -rf paper/*.aux paper/*.log paper/*.out paper/*.fls paper/*.fdb_latexmk \
	       paper/*.bbl paper/*.blg .pytest_cache src/**/__pycache__

distclean: clean
	rm -rf results/*.json figures/*.pdf paper/tables paper/numbers.tex paper/causalloss.pdf
