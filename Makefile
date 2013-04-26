#/usr/bin/env make

env:
	virtualenv --no-site-packages env
	env/bin/python setup.py develop
    
test: env
	. env/bin/activate; python -m unittest test

clean-py:
	find -name "*.pyc" -delete
