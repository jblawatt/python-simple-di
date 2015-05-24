Python Simple DI
================

::
	
	THIS README IS STILL UNDER DEVELOPMENT!!


``python-simple-di`` is a dependency injection container implementation. With its help you can create instances and its dependencies on runtime.

Install
-------

You can install ``python-simple-di`` via ``pip``: ::
	
	pip install python-simple-di

or via ``easy_install``: ::
	
	easy_install python-simple-di


Configuration
-------------

To configure the ``di.DIContainer`` you need to pass a ``dict`` with the needed configuration in it. Define the objects name as *key* to access it at runtime. The *value* needs to be the configuration to create the instance.

- **type** *(required)*: This option defines the type with its complete python dotted path or the real python type. You can add a path that will dynamicly become added to the ``sys.path`` if the instance is requested. *Examples:* ::
		
	'type': 'path.to.my.Type'
    'type': path.to.my.Type
	# or
	'type': '/add/to/sys/path:add.to.sys.path.Type'

- **args** *(optional)*: The args can be a ``list`` of values to pass as Arguments or a ``dict`` to pass as Keyword Arguments. To mix both define a dictionary with an empty string as key and a list as value. *Examples:* ::
	
	'args': ['first', 3, 'third'] 
	# or 
	'args': {'one': '1', 'two':'two'}
	# or
	'args': {'': [1, 'two'], 'three': 3}

- **lazy** *(optional)*: This option defines whether the instance will be created on runtime or will be created on container initialization. *Example:* ::
	
	'lazy': False # default: True

- **singleton** *(optional, default: True)*: If this option is set to `True`, the created instance will become saved inside the container. Next time the same instance will be returned. If this value is set to False a new instance will be created every time.

- **properties** *(optional)*: This options works similar to the args option. After an instance was created a buildup is called. This buildup fills the given Properties with the given values.

- **assert_type** *(optional)*: Checks weather the created type has the given base_type. ::
	
	'type': 'path.to.implementet.Type',
	'assert_type': 'path.to.parent.Type'

Argument Resolvers
__________________


WILL FOLLOW...

- **ref**: ...
- **rel**: ...
- **mod**: ...
- **factory**: ...
- **attr**: ...

Events
______

You can pass an EventDispatcher into the DiContainer. This Dispatcher will be called if anything interesting happens inside the Container. BaseType is di.DIEventDispatcher.


Usage
-----

::
	
	container = DIContainer(config)
	instance = container.resolve('instance_key')

