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
	# /usr/bin/python2.6 setup.py sdist --formats=zip,gztar,bztar,ztar,tar
	/usr/bin/python2.7 setup.py sdist --formats=zip,gztar,bztar,ztar,tar
	/usr/bin/python3.3 setup.py sdist --formats=zip,gztar,bztar,ztar,tar
