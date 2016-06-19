.. Python Simple DI documentation master file, created by
   sphinx-quickstart on Tue Feb 11 11:00:04 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Python Simple DI
================

.. image:: https://drone.io/bitbucket.org/jblawatt/python-simple-di/status.png
.. image:: https://img.shields.io/pypi/v/python-simple-di.svg
.. image:: https://img.shields.io/pypi/l/python-simple-di.svg
.. image:: https://img.shields.io/pypi/pyversions/python-simple-di.svg

*python-simple-di* is a simple dependency injection container implementation. With its help you can create instances and its dependencies on runtime.


.. toctree::
   :maxdepth: 2
   
   installation
   changes
   examples
   api


Example
-------
Using the DIContainer is very simple. This is a quick example how to define an configure a container using
the given settings and how to resolve the configured instance.

.. code-block:: python

   container = DIContainer({
      'john': {
         'type': 'python.name.to.person.Class',
         'args' {
            'first_name': 'John',
            'last_name': 'Doe'
         }
      }
   })

   # ------

   john = container.resolve("john")


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

