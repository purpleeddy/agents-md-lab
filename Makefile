PY ?= python3

.PHONY: all guard data check report test check-links

all: data check report

guard:
	@$(PY) -c 'import sys; assert sys.version_info >= (3, 11), "agents-md-lab needs Python 3.11 or newer (tomllib); found %d.%d" % sys.version_info[:2]'

data: guard
	$(PY) scripts/data.py

check: guard
	$(PY) scripts/lint.py --corpus

report: guard
	$(PY) scripts/report.py

test: guard
	$(PY) -m unittest discover -s tests -t .
	$(PY) scripts/report.py --check
	$(PY) scripts/lint.py --self-test

check-links: guard
	$(PY) scripts/data.py --check-links
