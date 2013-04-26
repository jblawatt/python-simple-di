#/usr/bin/env make

env:
	virtualenv --no-site-packages env
	env/bin/python setup.py develop
	env/bin/pip install pep8
    
test: env
	. env/bin/activate; python -m unittest test

clean-py:
	find -name "*.pyc" -delete

check: env
	pep8 di.py

