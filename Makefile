all: shell-script-style python-style

BASH_SCRIPTS = run-cf-tests.sh
shell-script-style:
	shellcheck --format=gcc ${BASH_SCRIPTS}

PYTHON_FILES=$(shell find . -name '*.py' | grep -v randoop_old.py)
python-style:
	black .
	pylint -f parseable --disable=W,invalid-name ${PYTHON_FILES}
