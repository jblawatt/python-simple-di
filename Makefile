#/usr/bin/env make

SHELL=bash

pythonenv:
	virtualenv pythonenv
	pythonenv/bin/pip install tox pip --upgrade

test:
	pythonenv/bin/tox

clean:
	find -name "*.pyc" -delete
	find -name "*.*~" -delete


dist:
	pythonenv/bin/python setup.py sdist --formats=zip,gztar,bztar,ztar,tar
	pythonenv/bin/python setup.py bdist_wheel
