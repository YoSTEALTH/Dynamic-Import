# Local checks and release helpers. `make` (= `make all`) verifies everything; nothing here commits or pushes.
#
#   make venv    recreate the scratch venv with the `dev` dependency group (ruff, pytest, build, twine)
#   make all     lint, test on every interpreter, smoke, build, check
#   make bump    write today's date into `dynamic_import/version.py`
#   make tag     annotated tag `v<version>` (clean tree, version must be today)
#   make publish manual fallback for `release.yml`: PyPI upload + GitHub release

VENV    ?= /tmp/di-venv
PY      := $(VENV)/bin/python
PYTHONS ?= $(wildcard /opt/python/3.11/bin/python3 /opt/python/3.14/bin/python3 /opt/python/3.14t/bin/python3 \
                      /opt/python/3.15/bin/python3 /opt/python/3.15t/bin/python3)
SMOKE   ?= $(lastword $(PYTHONS))
DIST    := build/dist
VERSION  = $(shell sed -n "s/^version = '\(.*\)'$$/\1/p" dynamic_import/version.py)
TODAY    = $(shell date +%Y.%-m.%-d)

.PHONY: all venv lint test smoke build check bump tag publish clean
all: lint test smoke build check

venv:
	/opt/python/3.14/bin/python3 -m venv --clear $(VENV)
	$(PY) -m pip install -q --upgrade pip
	$(PY) -m pip install -q --group dev

lint:
	$(VENV)/bin/ruff check .

test:
	@test -n "$(PYTHONS)" || { echo 'no interpreter found, set PYTHONS'; exit 1; }
	@for py in $(PYTHONS); do \
		echo "== $$py"; \
		PYTHONPATH=. $$py -m pytest -q -p no:cacheprovider || exit 1; \
	done

smoke:
	cd example && $(SMOKE) calling.py

build:
	rm -rf $(DIST)
	$(PY) -m build --outdir $(DIST)

check:
	$(PY) -m twine check --strict $(DIST)/*
	@ver=$$($(PY) -c "from packaging.version import Version; print(Version('$(VERSION)'))"); \
	ls $(DIST)/dynamic_import-$$ver-py3-none-any.whl $(DIST)/dynamic_import-$$ver.tar.gz >/dev/null || \
		{ echo "no wheel/sdist for version $$ver in $(DIST)"; exit 1; }

bump:
	@if git rev-parse -q --verify "refs/tags/v$(TODAY)" >/dev/null; then \
		echo "tag v$(TODAY) already exists"; exit 1; fi
	sed -i "s/^version = '.*'$$/version = '$(TODAY)'/" dynamic_import/version.py
	@echo "version = $(TODAY): commit dynamic_import/version.py, then make tag"

tag:
	@test -z "$$(git status --porcelain --untracked-files=no)" || { echo 'working tree is dirty'; exit 1; }
	@test "$(VERSION)" = "$(TODAY)" || { echo "version.py is $(VERSION), not today ($(TODAY)): make bump"; exit 1; }
	@if git rev-parse -q --verify "refs/tags/v$(VERSION)" >/dev/null; then \
		echo "tag v$(VERSION) already exists"; exit 1; fi
	git tag -a "v$(VERSION)" -m "Dynamic Import - $(VERSION)"
	@echo "tagged v$(VERSION): git push && git push origin v$(VERSION)"

publish: all
	$(PY) -m twine upload $(DIST)/*
	gh release create "v$(VERSION)" $(DIST)/* --generate-notes --title "Dynamic Import - $(VERSION)"

clean:
	rm -rf build dynamic_import.egg-info .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
