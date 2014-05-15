# coding: utf-8

import sys
sys.path.append('src/')

import di
from setuptools import setup


setup_args = {
    'name': 'python-simple-di',
    'version': di.__version__,
    'description': 'A simple dependency injection container.',
    'long_description': open('README.rst').read(),
    'url': 'http://bitbucket.org/jblawatt/python-simple-di',
    'author': di.__author__,
    'author_email': di.__author_email__,
    'url': di.__website__,
    'py_modules': ['di'],
    'licence': 'MIT',
    'install_requires': ['importlib']
}


if __name__ == '__main__':
    setup(**setup_args)
