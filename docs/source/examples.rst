Examples
========

Creating a simple container
---------------------------

Resolving instances
-------------------

Using resolvers
---------------

Usage as contextmanager
-----------------------

Using decorators
----------------

Register class with the register decorator
..........................................

The method `register` can be used as decorator for classes or factory methods. With this
you do not need to provide the instances configuration at container creation.

Passing the settings is optional.

.. code:: python

	@container.register("my_service", dict(args={'init_arg': 'test'}))
	class MyService(object):

		def __init__(self, init_arg):
			self.init_arg = init_arg

		def get_data(self, args):
			pass

Load instances with the inject or inject_many decorator
.......................................................

The method :code:`inject` gives you the possibility to inject instances into a
method if a keyword argument was not provided. that makes the loosely coupeling
and testing very easy:

.. code:: python

	@container.inject(service='some_service')
	def some_method(value, service):
		service.do_work(value)

	some_method("hello world")
	some_method("hello world", ExplicitService())


The method :code:`inject_many` gives you the possibility to inject multiple instances depending on
their type.

.. code-block:: python

    @container.inject_many(hooks=SomeHookClass)
    def method(data, hook_instances):
        for hook in hook_instance:
            hook.hook(data)
        # ...



Using a child container
-----------------------

If you need the same container but override some settings you can create a child container and pass the deviant settings into it.

This is the unittest that explains this function at its best.

.. code-block:: python

    container = DIContainer({
		'one': {
			'type': 'mock.Mock',
			'properties': {
				'source': 'parent'
			}
		},
		'two': {
			'type': 'mock.Mock',
			'properties': {
				'source': 'parent'
			}
		}
	})

    self.assertEqual(container.one.source, 'parent')
    self.assertEqual(container.two.source, 'parent')

    child_container = container.create_child_container({
		'two': {
			'type': 'mock.Mock',
			'properties': {
				'source': 'child'
			}
		}
	})

    self.assertEqual(child_container.one.source, 'parent')
    self.assertEqual(child_container.two.source, 'child')
    self.assertEqual(container.one.source, 'parent')
    self.assertEqual(container.two.source, 'parent')
