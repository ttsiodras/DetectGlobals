TARGET:=detect_globals.py
PYTHON:=python3
BIN:=.venv

all:	.processed

.processed:	${TARGET} flake8 pylint mypy
	@touch $@

flake8: | dev-install
	@echo "============================================"
	@echo " Running flake8..."
	@echo "============================================"
	${BIN}/bin/flake8 ${TARGET}

pylint: | dev-install
	@echo "============================================"
	@echo " Running pylint..."
	@echo "============================================"
	${BIN}/bin/pylint --disable=I --rcfile=pylint.cfg ${TARGET}

mypy: | dev-install
	@echo "============================================"
	@echo " Running mypy..."
	@echo "============================================"
	${BIN}/bin/mypy --ignore-missing-imports ${TARGET}

dev-install:
	@${PYTHON} -c 'import sys; sys.exit(1 if (sys.version_info.major<3 or sys.version_info.minor<5) else 0)' || { \
	    echo "=============================================" ; \
	    echo "[x] You need at least Python 3.5 to run this." ; \
	    echo "=============================================" ; \
	    exit 1 ; \
	}
	@if [ ! -d ${BIN} ] ; then                                  \
	    echo "[-] Installing VirtualEnv environment..." ;      \
	    ${PYTHON} -m venv ${BIN} || exit 1 ;                    \
	    echo "[-] Installing packages inside environment..." ; \
	    . ${BIN}/bin/activate || exit 1 ;                       \
	    ${PYTHON} -m pip install -r requirements.txt || exit 1 ; \
	fi

clean:
	rm -rf .cache/ .mypy_cache/ .processed

.PHONY:	flake8 pylint mypy clean dev-install
