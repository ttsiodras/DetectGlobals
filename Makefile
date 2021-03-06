TARGET:=detect_globals.py test_detector.py
PYTHON:=python3
VENV:=.venv

all:	.setup .analysed test

.analysed:	${TARGET}
	$(MAKE) flake8
	$(MAKE) pylint
	$(MAKE) mypy
	@touch $@

flake8: dev-install
	@echo "============================================"
	@echo " Running flake8..."
	@echo "============================================"
	${VENV}/bin/flake8 ${TARGET}

pylint: dev-install
	@echo "============================================"
	@echo " Running pylint..."
	@echo "============================================"
	${VENV}/bin/pylint --disable=I --rcfile=pylint.cfg ${TARGET}

mypy: dev-install
	@echo "============================================"
	@echo " Running mypy..."
	@echo "============================================"
	${VENV}/bin/mypy --ignore-missing-imports ${TARGET}

test: dev-install
	${VENV}/bin/pytest -v test_detector.py

test-dbg: dev-install
	${VENV}/bin/pytest -v --pdb test_detector.py

dev-install:	.setup | prereq

prereq:
	@${PYTHON} -c 'import sys; sys.exit(1 if (sys.version_info.major<3 or sys.version_info.minor<5) else 0)' || { \
	    echo "=============================================" ; \
	    echo "[x] You need at least Python 3.5 to run this." ; \
	    echo "=============================================" ; \
	    exit 1 ; \
	}

.setup:	requirements.txt
	@if [ ! -d ${VENV} ] ; then                            \
	    echo "[-] Installing VirtualEnv environment..." ;  \
	    ${PYTHON} -m venv ${VENV} || exit 1 ;              \
	fi
	echo "[-] Installing packages inside environment..." ; \
	. ${VENV}/bin/activate || exit 1 ;                     \
	${PYTHON} -m pip install -r requirements.txt || exit 1
	touch $@

coverage: | dev-install
	$(MAKE) clean
	${VENV}/bin/coverage run -a ./detect_globals.py || exit 0
	${VENV}/bin/coverage run -a ./detect_globals.py -h || exit 0
	${VENV}/bin/coverage run -a ./detect_globals.py -v tests/example*c
	${VENV}/bin/coverage run -a -m pytest
	@echo -n "Coverage achieved: " ; \
	${VENV}/bin/coverage report | grep ^detect | awk '{print $$NF}'


clean:
	rm -rf .cache/ .mypy_cache/ .analysed .setup __pycache__ \
	       tests/__pycache__ .pytest_cache/ .processed .coverage

.PHONY:	flake8 pylint mypy clean dev-install prereq
