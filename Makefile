install: install-flit
	flit install --deps develop

develop: install-flit
	flit install --deps all --pth-file

install-flit:
	python -m pip install --upgrade pip
	pip install flit

isort-src:
	isort ./imxInsights ./tests

isort-docs:
	isort ./docs -o imxInsights


format: isort-src isort-docs
	black .

isort-src-check:
	isort --check-only ./imxInsights ./tests

isort-docs-check:
	isort --check-only ./docs -o imxInsights


format-check: isort-src-check isort-docs-check
	black --check .

lint:
	flake8 ./imxInsights ./tests

typecheck:
	mypy imxInsights/ tests/

# todo: make sure in production covar is at least 90%
test:
	pytest --cov=imxInsights/ --cov-report=term-missing --cov-fail-under=80

bumpversion-major:
	bumpversion major

bumpversion-minor:
	bumpversion minor

bumpversion-patch:
	bumpversion patch

bumpversion-build:
	bumpversion build
	
build-wheel:
	flit build

docs-serve:
	mkdocs serve

docs-publish:
	mkdocs build
# 	mkdocs gh-deploy


check-all: test lint typecheck # docs-publish

check: lint typecheck

build-cli-app:
	python -m PyInstaller cli/imx_to_excel.py --onefile --add-data "imxInsights/custom_puic_config.yaml:imxInsights/."
