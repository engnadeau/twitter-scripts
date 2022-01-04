.DEFAULT_GOAL = all
OUTPUT_DIR = "out"

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# phony targets

.PHONY: all
all: clean format

.PHONY: clean
clean:
	-rm -rf $(OUTPUT_DIR)

.PHONY: format
format:
	pipenv run black .
	pipenv run isort .
