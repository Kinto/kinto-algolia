VIRTUALENV = virtualenv
VENV := $(shell echo $${VIRTUAL_ENV-.venv})
DEV_STAMP = $(VENV)/.dev_env_installed.stamp
INSTALL_STAMP = $(VENV)/.install.stamp
PYTHON = $(VENV)/bin/python
TOX = $(VENV)/bin/tox
TEMPDIR := $(shell mktemp -d)

build-requirements:
	$(VIRTUALENV) $(TEMPDIR)
	$(TEMPDIR)/bin/pip install -U pip
	$(TEMPDIR)/bin/pip install -Ue .
	$(TEMPDIR)/bin/pip freeze | grep -v -- '-e' > requirements.txt

virtualenv: $(PYTHON)
$(PYTHON):
	virtualenv $(VENV) --python=python3

install: $(INSTALL_STAMP)
$(INSTALL_STAMP): $(PYTHON) setup.py
	$(VENV)/bin/pip install -U pip
	$(VENV)/bin/pip install -Ue .
	touch $(INSTALL_STAMP)

install-dev: $(INSTALL_STAMP) $(DEV_STAMP)
$(DEV_STAMP): $(PYTHON) dev-requirements.txt
	$(VENV)/bin/pip install -r dev-requirements.txt
	touch $(DEV_STAMP)

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d | xargs rm -fr

distclean: clean
	rm -fr *.egg *.egg-info/ dist/ build/

maintainer-clean: distclean
	rm -fr .venv/ .tox/

tox: $(TOX)
$(TOX): virtualenv
	$(VENV)/bin/pip install tox

black: install-dev
	$(VENV)/bin/black kinto_algolia

tests-once: install-dev
	$(VENV)/bin/py.test --cov-report term-missing --cov-fail-under 100 --cov kinto_algolia

tests: tox
	$(VENV)/bin/tox

flake8: install-dev
	$(VENV)/bin/flake8 kinto_algolia tests
