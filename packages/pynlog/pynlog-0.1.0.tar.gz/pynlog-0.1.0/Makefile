PYTHON=python3
PACKAGE_NAME=pynlog

VENV_PATH=.venv
BIN_PATH=$(VENV_PATH)/bin
TEST_PATH=test
SRC_PATH=src
PACKAGE_PATH=$(SRC_PATH)/$(PACKAGE_NAME)
OUT_PATH=out
LOGS_PATH=logs
REQUIREMENTS_PATH=requirements.txt


init: clean
	@echo "Setting up virtual environment"
	@$(PYTHON) -m venv $(VENV_PATH)

	@echo "Creating output folder"
	@mkdir $(OUT_PATH)

	@echo "Creating logs folder"
	@mkdir $(LOGS_PATH)
	
	@echo "Installing external dependencies"
	@$(BIN_PATH)/pip install -r $(REQUIREMENTS_PATH)

	@echo "Installing project"
	@$(BIN_PATH)/pip install -e .


test-all:
	@for arg in $(TEST_PATH)/*.py; do \
		echo "Running $$arg..."; \
		$(BIN_PATH)/$(PYTHON) $$arg; \
	done


run-tests:
	@for arg in $(ARGS); do \
		echo "Running test_$$arg..."; \
		$(BIN_PATH)/$(PYTHON) $(TEST_PATH)/test_$$arg.py; \
	done

py-stubs: clean-py-stubs
	@echo "Creating stubs"
	@$(BIN_PATH)/stubgen -p $(PACKAGE_NAME) -o $(SRC_PATH)

clean:
	@echo "Removing virtual environment"
	@rm -rf $(VENV_PATH)
	@echo "Removing output folder"
	@rm -rf $(OUT_PATH)
	@echo "Removing logs folder"
	@rm -rf $(LOGS_PATH)

clean-py-stubs:
	@echo "Removing stubs"
	@find $(PACKAGE_PATH) -type f -name "*.pyi" -delete
