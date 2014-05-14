#/usr/bin/env make

SHELL=bash

env:
	virtualenv --no-site-packages env
	env/bin/python setup.py develop
	env/bin/pip install pep8 pyflakes coverage mock
    
test: env
	. env/bin/activate; python -m unittest test

clean:
	rm -rf env

clean-py:
	find -name "*.pyc" -delete

check: env
	. env/bin/activate; pep8 di.py
	. env/bin/activate; pyflakes di.py

coverage: env
	test -d htmlcov && rm -rf htmlcov
	. env/bin/activate; coverage run -m unittest test; \
        coverage html; coverage report; coverage erase
