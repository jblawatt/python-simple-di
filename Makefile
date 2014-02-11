#/usr/bin/env make

env:
	virtualenv --no-site-packages env
	env/bin/python setup.py develop
	env/bin/pip install pep8 pyflakes
    
test: env
	. env/bin/activate; python -m unittest test

clean:
	rm -rf env

clean-py:
	find -name "*.pyc" -delete

check: env
	. env/bin/activate; pep8 src/di.py
	. env/bin/activate; pyflakes src/di.py

