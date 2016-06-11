Python Simple DI
================

.. image:: https://drone.io/bitbucket.org/jblawatt/python-simple-di/status.png


*python-simple-di* is a simple dependency injection container implementation. With its help you can create instances and its dependencies on runtime.


.. contents::


Changes
-------

1.6.0
_____

- **resolve many**: the new methods `resolve_many` and `resolve_many_lazy` gives you the possibility to resolve multiple objects depending on their class.
- **alias names**: you can provide a list of alias names within the object configuration.
- **constructor/factory (kw)argument overridies**: resolve methods noch accepts args and kwargs that will can be used instead of args configurations.
- **register decorator**: :code:`register` can be used as decorator now.
- **use as contextmanager**: the container can be used as context manager to temporarily override settings in :code:`with` block.

1.5.2
_____

- copy settings in DIContainer.__init__.


Install
-------

You can install it via pip: ::

	pip install python-simple-di

or via easy_install: ::

	easy_install -U python-simple-di


Configuration
-------------

To configure the ``di.DIContainer`` you need to pass a dict with the needed configuration in it. Alternativly you can use an instance of ``di.DIConfig`` which is used internal anyway.
Define the objects name as *key* to access it at runtime. The *value* needs to be the configuration to create the instance.

- **type** *(required)*: This option defines the type with its complete python dotted path or the python type instance. You can add a path that will dynamicly become added to the ``sys.path`` if the instance is requested. *Examples:*

.. code-block:: python

	'type': 'path.to.my.Type'
	'type': path.to.my.Type
	# or
	'type': '/add/to/sys/path:add.to.sys.path.Type'

- **args** *(optional)*: The args can either be a ``list`` of values to pass as Arguments or a ``dict`` to pass as Keyword Arguments. To mix both, you can define a dictionary with an empty string or None as key and a list as value. *Examples:*

.. code:: python

	'args': ['first', 3, 'third']
	# or
	'args': {'one': '1', 'two':'two'}
	# or
	'args': {'': [1, 'two'], 'three': 3}

- **lazy** *(optional)*: This option defines whether the instance will be created on runtime or on container initialization. *Example:*

.. code:: python

	'lazy': False # default: True

- **singleton** *(optional, default: True)*: If this option is set to ``True``, the created instance will be saved inside the container. Next time the same instance will be returned. If this value is set to ``False`` a new instance will be created every time.

- **properties** *(optional)*: This option is similar to the ``args`` option. After an instance was created a buildup is called. This buildup fills the given properties with the given values in this dictionary. *Examples:*

.. code-block:: python

	{
		'type': 'some.Person',
		'propeties': {
			'first_name': 'John',
			'last_name': 'Doe'
		}
	}

- **assert_type** *(optional)*: Checks weather the created type has the given base_type.

.. code:: python

	'type': 'path.to.implementet.Type',
	'assert_type': 'path.to.parent.Type'

- **factory_method** *(optional)*: This options can be used to create an instance by a classmethod which creates the wanted instance. For example this can be used to create a class based views in django at runtime. *Example:*

.. code:: python

	'type': 'myapp.views.ClassBasedView',
	'factory_method': 'as_view'


Argument Resolvers
__________________

With the help of the resolver the magic comes into play. Thanks to this small classes it is possible to trigger the dependencies of a type at runtime.

The following resolver be brought by the default package. Individual resolver can be implemented by extending the base class ``di.Resolver``.

ReferenceResolver
.................
The ReferenceResolver offers the possibility to an attribute within the python path to refer. This must be the path and the object, as a Python dotted path.

*Example:*

.. code:: python

	{
		'args': {
			'output_stream': ReferenceResolver('sys.stdout')
		}
	}

`di` also provides some shortcuts for this name:

- ``di.ref('sys.stdout')`` as shortcut for type.
- ``di.reference('sys.stdout')`` as shortcut for the type.
- ``'ref:sys.stdout'`` as prefix of the configured type to lazy use the resolver.

RelationResolver
................
The RelationResolver allows the resolution of an object of this container at runtime.

*Example:*

.. code:: python

	{
		'object_a': {
			'type': 'some.ClassName'
		},
		'object_b': {
			'type': 'some.other.ClassName',
			'args': [
				RelationResolver('object_a')
			]
		},
	}


`di` also provides some shortcuts for this name:

- ``di.rel('object_a')`` as shortcut for type.
- ``di.relation('object_a')`` as shortcut for the type.
- ``'rel:object_a'`` as prefix of the configured type to lazy use the resolver.

ModuleResover
.............

Sometimes it may be necessary to pass an entire module as a parameter. For this purpose the ModuleResolver available.

*Example:*

.. code:: python

	{
		'type': 'some.ClassName',
		'args': {
			'serializer': ModuleResolver('json')
		}
	}


Di also provides some shortcuts for this name.

- ``di.mod('json')`` as shortcut for type.
- ``di.module('json')`` as shortcut for the type.
- ``'mod:json'`` as prefix of the configured type to lazy use the resolver.


FactoryResolver
...............

With the help of FactoryResolver the return value of a function as an argument can be passed to the specified type.

*Example.*

.. code:: python

	{
		'type': 'some.ClassName',
		'args': [
			FactoryResolver('path.to.the.factory_method')
		]
	}

Di also provides some shortcuts for this name.

- ``di.fac('path.to.the.factory_method')`` as shortcut for type.
- ``di.factory('path.to.the.factory_method')`` as shortcut for the type.
- ``'factory:path.to.the.factory_method'`` as prefix of the configured type to lazy use the resolver.


AttributeResolver
.................

With the Resolver an attribute of an instance can be passed as an argument. This can be very useful if you are using the django web framework and want to pass a settings value as an argument fo an instance.

*Example:*

.. code:: python

	{
		'type': 'some.ClassName':
		'args': {
			'debug': AttributeResolver('django.conf.settings.DEBUG')
		}
	}


Di also provides some shortcuts for this name.

- ``di.attr('django.conf.settings.DEBUG')`` as shortcut for type.
- ``di.attribute('django.conf.settings.DEBUG')`` as shortcut for the type.
- ``'attr:django.conf.settings.DEBUG'`` as prefix of the configured type to lazy use the resolver.


Events
______

You can pass an EventDispatcher into the DiContainer. This Dispatcher will be called if anything interesting happens inside the Container. BaseType is ``di.DIEventDispatcher``.


Usage
.....

Simply create a dictionary with your type configuration and pass it as settings argument to the ``DIContainer``. The Dictionarys key is the type key to resolve the instance.

.. code:: python

	# create the container
	container = DIContainer(config)

	# resolve the instance
	instance = container.resolve('instance_key')

	# resolve the instance type only
	type_of_instance_key = container.resolve_type('instance_key')


Resolve Lazy
____________

Sometimes it may be necessary to create an instance at its first useage. So there are the following two messages, that returns a ``di.Proxy`` instance at first.

To use this Feature you need to provide a ``proxy_type_name`` and install the specific package for this. I recommend ``lazy-object-proxy`` with its type ``Proxy``. Which is the default value for this argument. It is not shipped with this package because of the many different other implementations and thier different licence.
If you use this in combination with django you can use ``django.utils.functional.SimpleLazyObject``. **But at this moment the ``resolve_type_lazy`` is not working properly with ``SimpleLazyObject``**.

.. code:: python

	# create the container
	container = DIContainer(config, proxy_type_name='lazy_object_proxy.Proxy')

	# lazy resolves the instance
	instance = container.resolve_lazy('instance_key')

	# lazy resolves the instance type only
	type_of_instance_key = container.resolve_type_lazy('instance_key')


Child Container
_______________

If you need the same container but override some settings you can create a child container and pass the deviant settings into it.

This is the unittest that explains this function at its best.

.. code:: python

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


Decorators
__________
Some method of the ``di.DIContainer`` can be used as decorator zu register or inject instances within your code.

Register by decorator
......................
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


Inject with decorator
......................
The method :code:`inject` gives you the possibility to inject instances into a
method if a keyword argument was not provided. that makes the loosely coupeling
and testing very easy:

.. code:: python

	@container.inject(service='some_service')
	def some_method(value, service):
		service.do_work(value)

	some_method("hello world")
	some_method("hello world", ExplicitService())


Inject many with decorator
..........................
The method :code:`inject_many` gives you the possibility to inject multiple instances depending on
their type.

.. code-block:: python

    @container.inject_many(hooks=SomeHookClass)
    def method(data, hook_instances):
        for hook in hook_instance:
            hook.hook(data)
        # ...

