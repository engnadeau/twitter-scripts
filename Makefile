.DEFAULT_GOAL = all
OUTPUT_DIR = "out"

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# phony targets

.PHONY: all
all: clean format check

.PHONY: clean
clean:
	-rm -rf $(OUTPUT_DIR)

.PHONY: check
check:
	pipenv run black --check .
	pipenv run isort --check .
	pipenv run flake8 .

.PHONY: format
format:
	pipenv run black .
	pipenv run isort .
