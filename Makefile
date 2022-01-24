.DEFAULT_GOAL = all
OUTPUT_DIR = "out"

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# phony targets

.PHONY: all
all: clean format check

.PHONY: clean
clean:
	-rm -rf $(OUTPUT_DIR)

.PHONY: lint
lint: check

.PHONY: check
check:
	find . -type f -name "*.py" | xargs pipenv run pylint -j 0
	pipenv run bandit -r .
	pipenv run black --check .
	pipenv run flake8 .
	pipenv run isort --check .
	pipenv run vulture .

.PHONY: format
format:
	pipenv run black .
	pipenv run isort .

.PHONY: install-extras
install-extras:
	pipenv run python -m pip install -r requirements-plot.txt
