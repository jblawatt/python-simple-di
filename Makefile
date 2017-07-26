#/usr/bin/env make

SHELL=bash

pythonenv:
	virtualenv pythonenv
	pythonenv/bin/pip install tox pip --upgrade

test:
	pythonenv/bin/tox

test-parallel:
	pythonenv/bin/detox

clean:
	find -name "*.pyc" -delete
	find -name "*.*~" -delete
	rm -rf python-simple-di-* env dist python_simple_di.egg-info htmlcov __pycache__


dist:
	pythonenv/bin/python setup.py build sdist bdist
