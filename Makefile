.PHONY: clean clean-test clean-pyc clean-build docs help
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +
	tox -e clean

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

check: dist ## check
	tox -e check

lint: ## check style with flake8
	flake8 src tests

pylint: ## check style with flake8
	pylint src tests

isort:
	isort -rc src/aiscalator

test: install ## run tests quickly with the default Python
	py.test tests

test-all: ## run tests on every Python version with tox
	tox

coverage: ## check code coverage quickly with the default Python
	PYTEST_ADDOPTS=--cov-append TOX_SKIP_ENV="py.*-nocov" tox
	$(BROWSER) htmlcov/index.html

codacy:
	mkdir -p build
	codacy-analysis-cli analyse -d "${PWD}" | tee build/codacy.txt

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/aiscalator.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ src/aiscalator
	tox -e docs
	$(BROWSER) dist/docs/index.html

release: dist ## package and upload a release
	twine upload dist/*

test-release: dist ## package and upload a release on test.pypi instead of real pypi
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

dist: clean ## builds source and wheel package
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

install: clean ## install the package to the active Python's site-packages
	python setup.py install

bumpversion:
	bumpversion patch setup.py
	git diff

bumpversion-release: ## increment version of released package
	bumpversion --config-file .bumpversion_release.cfg patch .bumpversion_release.cfg
	git diff

