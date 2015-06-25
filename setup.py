# coding: utf-8

from __future__ import absolute_import

import di
import sys

from setuptools import setup


py26 = sys.version_info < (2, 7)
py27 = not py26 and sys.version_info < (3, 0)
py3 = sys.version_info >= (3, 0)


if py26:
    install_requires = [
        'importlib'
    ]
else:
    install_requires = [
    ]


setup_args = {
    'name': 'python-simple-di',
    'version': di.__version__,
    'description': 'A simple dependency injection container.',
    'long_description': open('README.rst', 'r').read(),
    'author': di.__author__,
    'author_email': di.__author_email__,
    'maintainer': di.__maintainer__,
    'maintainer_email': di.__maintainer_email__,
    'url': di.__website__,
    'py_modules': ['di'],
    'license': 'MIT',
    'install_requires': install_requires,
    'classifiers': [
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Topic :: Utilities',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Operating System :: OS Independent',
    ]
}


if __name__ == '__main__':
    setup(**setup_args)
