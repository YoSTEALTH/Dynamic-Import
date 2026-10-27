# Local checks and release helpers. `make` (= `make all`) verifies everything; nothing here commits or pushes.
#
#   make venv    recreate the scratch venv with the `dev` dependency group (ruff, pytest, build, twine)
#   make all     lint, test on every interpreter, smoke, build, check
#   make bump    write today's date (`-<n>` if tag `v<today>` exists) into `dynamic_import/version.py`
#   make tag     annotated tag `v<version>` (clean tree, version must be exactly today: no `-<n>` release)
#   make publish `make all`, then upload `build/dist` to PyPI with twine (HEAD must carry tag `v<version>`,
#                version a plain `<year>.<month>.<day>`)

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

bump:  # today's date; if tag `v<today>` exists, the next free `<today>-<n>` (PEP 440 reads it as `.post<n>`)
	@ver=$(TODAY); n=0; \
	while git rev-parse -q --verify "refs/tags/v$$ver" >/dev/null; do n=$$((n + 1)); ver=$(TODAY)-$$n; done; \
	sed -i "s/^version = '.*'$$/version = '$$ver'/" dynamic_import/version.py; \
	echo "version = $$ver"

tag:
	@test -z "$$(git status --porcelain --untracked-files=no)" || { echo 'working tree is dirty'; exit 1; }
	@test "$(VERSION)" = "$(TODAY)" || \
		{ echo "version.py is $(VERSION), not today ($(TODAY)); a release is a plain date, one per day"; exit 1; }
	@if git rev-parse -q --verify "refs/tags/v$(VERSION)" >/dev/null; then \
		echo "tag v$(VERSION) already exists"; exit 1; fi
	git tag -a "v$(VERSION)" -m "Dynamic Import - $(VERSION)"
	@echo "tagged v$(VERSION): make publish"

publish:  # checks first, so a wrong state fails before the long `make all`
	@test -z "$$(git status --porcelain --untracked-files=no)" || { echo 'working tree is dirty'; exit 1; }
	@echo "$(VERSION)" | grep -Eqx '[0-9]{4}\.[1-9][0-9]?\.[1-9][0-9]?' || \
		{ echo "version.py is $(VERSION): only a plain <year>.<month>.<day> goes to PyPI"; exit 1; }
	@test "$$(git rev-parse -q --verify 'refs/tags/v$(VERSION)^{commit}')" = "$$(git rev-parse HEAD)" || \
		{ echo "HEAD is not tagged v$(VERSION): make tag"; exit 1; }
	$(MAKE) all
	$(PY) -m twine upload $(DIST)/*

clean:
	rm -rf build dynamic_import.egg-info .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
