# coding: utf-8

import di
from setuptools import setup


setup_args = {
    'name': 'python-simple-di',
    'version': di.__version__,
    'description': 'A simple dependency injection container.',
    'long_description': open('README.rst').read(),
    'url': 'http://bitbucket.org/jblawatt/python-simple-di',
    'author': 'Jens Blawatt',
    'author_email': 'jblawatt@googlemail.com',
    'py_modules': ['src/di'],
}


if __name__ == '__main__':
    setup(**setup_args)
