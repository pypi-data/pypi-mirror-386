# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@echo "Documentation commands:"
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo ""
	@echo "Test commands:"
	@echo "  test         Run unit tests only (fast, default)"
	@echo "  test-unit    Run fast unit tests with mocking"
	@echo "  test-integration  Run slow integration tests with real DWD server"
	@echo "  test-all     Run both unit and integration tests"
	@echo "  test-quick   Quick syntax and import check"

.PHONY: help Makefile test test-unit test-integration test-all test-quick

# Test targets
test: test-unit

test-unit:
	@echo "Running unit tests (fast, mocked)..."
	python -m unittest src/dwd_opendata/tests/test_dwd_opendata.py -v

test-integration:
	@echo "Running integration tests (slow, real server calls)..."
	@echo "This requires internet connectivity and may take several minutes..."
	python -m unittest src/dwd_opendata/tests/test_integration.py -v

test-all: test-unit test-integration

test-quick:
	@echo "Quick syntax check..."
	python -c "import src.dwd_opendata; print('✓ Module imports successfully')"
	python -m py_compile src/dwd_opendata/__init__.py
	@echo "✓ Syntax check passed"

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
