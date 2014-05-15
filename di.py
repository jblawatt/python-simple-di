# coding: utf-8

import sys
import logging

from copy import copy

from importlib import import_module

__major__ = 1
__minor__ = 3
__bugfix__ = 2

__version__ = '%s.%s.%s' % (__major__, __minor__, __bugfix__)

__website__ = 'http://bitbucket.org/jblawatt/python-simple-di/'
__author__ = 'Jens Blawatt'
__author_email__ = 'jblawatt@googlemail.com'
__author_website__ = 'http://www.blawatt.de/'


_logger = logging.getLogger(__name__)


__all__ = [
    'DIEventDispatcher', 'DIContainer', 'attr', 'module', 'mod', 'factory',
    'fac', 'relation', 'rel', 'reference', 'ref',
]


class DIEventDispatcher(object):

    def __init__(self, container, *args, **kwargs):
        self.container = container

    def initialized(self, *args, **kwargs):
        pass

    def before_register(self, name, settings, *args, **kwargs):
        pass

    def after_register(self, name, settings, *args, **kwargs):
        pass

    def after_resolve(self, name, instance, *args, **kwargs):
        pass

    def before_resolve(self, name, *args, **kwargs):
        pass

    def before_build_up(self, name, instance, overrides, *args, **kwargs):
        pass

    def after_build_up(self, name, instance, overrides, *args, **kwargs):
        pass

    def before_resolve_type(self, name, *args, **kwargs):
        pass

    def after_resolve_type(self, name, type, *args, **kwargs):  # @ReservedAssignment
        pass

    def after_clear(self, name):
        pass


class DIContainer(object):
    """
    DIContainer is a simple helper class for dependecy injection.

    Example:
    --------

    It can be configured by a dicationary containing the type information.

    .. example::

        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name


        class Firm(object):
            def __init__(self, name):
                self.name = name


        configuration = {
            'jens': {
                'type': 'test.Person',  # the class type
                'lazy': True,  # optional, default: True
                'singleton': True,  # optional, default: True
                'args': {
                    '': ['jens', 'blawatt'],
                }
                'properties': {
                    'loves': 'rel:jessica',
                    'works_at': 'rel:gws',
                },
            },
            'jessica': {
                'type': 'test.Person',
                'args': {
                    'first_name': 'Jessica',
                    'last_name': 'Backhaus',
                },
            },
            'gws': {
                'type': 'test.Firm',
                'args': ['Gesellschaft für Warenwirtschaftssysteme mbH', ]
            }
        }


        container = DIContainer(configuration)


        Config Options:
        ---------------

        The strings used for configuration can have prefixes to specify
        what exactly shout be injected.

        - mod:
            Resolves the following name, trys to import_module it and passes
            the result as argument.
        - rel:
            Resolves an instance with the following name an passes it as
            argument. (warning: beware of recursion error.)
        - ref:
            Resolves a variable with the following name off a given module
            and passes it as an argument.

    """

    def __init__(self, settings, *args, **kwargs):
        """
        Creates a new DI Container.

        :param settings: The dictionary, containing the container-
                         configuration.
        :type settings: dict
        """

        dispatcher_type = kwargs.get('event_dispatcher', DIEventDispatcher)

        self.event_dispatcher = dispatcher_type(container=self)

        self.settings = settings
        self.names = settings.keys()
        self.singletons = {}
        self.parent = kwargs.get('parent', None)

        self.value_resolvers = {
            'mod': self._resolve_module_value,
            'ref': self._resolve_reference_value,
            'rel': self._resolve_relation_value,
            'factory': self._resolve_factory_value,
            'attr': self._resolve_attribute_value
        }

        self.value_resolvers.update(
            kwargs.get('value_resolvers', {})
        )

        for key, conf in self.settings.items():
            if not conf.get('lazy', True):
                self.resolve(key)

        self.event_dispatcher.initialized()

    # ---------------------------
    # private methods
    # ---------------------------
    def _resolve_type(self, python_name):
        """
        Resolves a type. The Parameter :code:`python_name` is the
        types full path python name.
        * de.blawatt.test.Person

        The types module can dynamicly be added to the path this way:
        * /tmp/dir_with_module/:module.Person

        :param python_name: The full name of the type to reslove.
        :type python_name: str

        :returns: type
        """

        # check if python_name contains a : to split path
        # and python_name
        if ':' in python_name:
            path, python_name = python_name.split(':')
            if not path in sys.path:
                sys.path.append(path)

        type_path, type_name = python_name.rsplit('.', 1)
        mod = import_module(type_path)
        return getattr(mod, type_name)

    def _resolve_module_value(self, value_conf):
        """
        Resolves a module, given in the value_conf.
        :param value_conf: str
        :rtype: object
        """
        key, name = value_conf.split(':', 1)  # @UnusedVariable
        return import_module(name)

    def _resolve_relation_value(self, value_conf):
        """
        Resolve an object with the given name in this container.
        :param value_conf: str
        :rtype: object
        """
        key, name = value_conf.split(':', 1)  # @UnusedVariable
        return self.resolve(name)

    def _resolve_reference_value(self, value_conf):
        """
        Resolves the given module and returns the given object off it.
        :param value_conf: str
        :rtype: object
        """
        key, name = value_conf.split(':', 1)  # @UnusedVariable
        mod_name, var_name = name.rsplit('.', 1)
        mod = import_module(mod_name)
        return getattr(mod, var_name)

    def _resolve_factory_value(self, value_conf):
        """
        Resolves the factory method and returns the factories response.
        :param value_conf:
        :rtype: object
        """
        key, name = value_conf.split(':', 1)  # @UnusedVariable
        mod_name, factory_name = name.rsplit('.', 1)
        mod = import_module(mod_name)
        return getattr(mod, factory_name)()

    def _resolve_attribute_value(self, value_conf):
        pre_conf, attr_name = value_conf.rsplit('.', 1)
        instance = self._resolve_reference_value(pre_conf)
        return getattr(instance, attr_name)

    def _resolve_value(self, value_conf):
        """
        resolves a value from a string.

        depeding on then value prefix some furthur action will follow:
        * ''rel'': relates to anoter type of in this container.
        * ''mod'': imports and return a module/package with that name.
        * ''ref'': load a variable off a module/package.

        :param value_conf: the value to pass or resolve.
        :type value_conf: dict

        :returns: object
        """
        value = value_conf
        if isinstance(value_conf, str):
            for key, resolver in self.value_resolvers.iteritems():
                if value_conf.startswith('%s:' % key):
                    return resolver(value_conf)
        return value

    def _resolve_args(self, conf):
        """
        resolves the arguments off the container configuration.

        :param conf: value configuration.
        :type conf: dict

        :returns: (), {}
        """
        args = []
        kwargs = {}
        if isinstance(conf, dict):
            for key, value_conf in conf.items():
                if key == '':
                    if hasattr(value_conf, '__iter__'):
                        for arg_conf in value_conf:
                            args.append(self._resolve_value(arg_conf))
                    else:
                        args.append(self._resolve_value(value_conf))
                else:
                    kwargs[key] = self._resolve_value(value_conf)
        elif hasattr(conf, '__iter__'):
            for value_conf in conf:
                args.append(self._resolve_value(value_conf))
        return args, kwargs

    def _check_type(self, conf_name, type_, expected):
        """
        Check if `type_` is a subclass of `expected`.

        :param conf_name: Name of the Configuration name for this check.
        :type conf_name: str
        :param type_: Type that must implement the expected type.
        :type type_: type
        :param expected: Type that must be implemented by `type_`.
        :type expected: type

        :raises: TypeError
        """
        if not issubclass(type_, expected):
            raise TypeError(
                '%s is not a subclass of %s. This violates the'
                'configuration for key %s'
                % (type_, expected, conf_name)
            )

    # ---------------------------
    # public methods
    # ---------------------------
    def register(self, name, settings):
        """
        register a new configuration at runtime.

        :param name: the name for the new configuration.
        :type name: str
        :param settings: the sessings dictionary for the new type.
        :type settings: dict
        """

        self.event_dispatcher.before_register(name=name, settings=settings)

        if name in self.settings:
            raise KeyError('there is already a configuration with this name.')
        self.settings[name] = settings

        self.event_dispatcher.after_register(name=name, settings=settings)

    def resolve(self, name):
        """
        Resolves an object by its name assigned in the configuration.

        :param name: object's name in the configuration.
        :type name: str

        :returns: object
        """

        self.event_dispatcher.before_resolve(name=name)

        # check if there already is a singleton instance
        # for this name
        if name in self.singletons:
            return self.singletons[name]

        # load information to create the instance
        conf = self.settings[name]
        singleton = conf.get('singleton', False)
        type_ = self._resolve_type(conf['type'])

        # assert weather the type implements the
        # configures basetype.
        assert_type = conf.get('assert_type', None)
        if assert_type:
            expected_type = self._resolve_type(assert_type)
            self._check_type(name, type_, expected_type)

        # resolve the arguments to pass into the constructor
        _args, _kwargs = self._resolve_args(conf.get('args', []))

        # create the instance
        obj = type_(*_args, **_kwargs)
        obj = self.build_up(name, obj)

        if singleton:
            self.singletons[name] = obj

        self.event_dispatcher.after_resolve(name=name, instance=obj)

        return obj

    def resolve_type(self, name):
        """
        Resolves a type for the given name in the configuration.

        :param name: name of an object in the configuration.
        :type name: str

        :returns: type
        """

        self.event_dispatcher.before_resolve_type(name=name)

        conf = self.settings[name]
        type_ = self._resolve_type(conf['type'])

        self.event_dispatcher.after_resolve_type(name=name, type=type_)

        return type_

    def build_up(self, name, instance, **overrides):
        """
        Injects the information spezified in the properties config
        into an existing object.

        :param name: name of the object definition in the container config.
        :type name: str
        :param instance: the instance to buildup
        :type instance: object

        :param **overrides: sets/overrides the information of the config
                            with the given information.

        :returns: the buildup instance
        """

        self.event_dispatcher.before_build_up(
            name=name, instance=instance, overrides=overrides
        )

        prop = self.settings[name].get('properties', {}).copy()
        prop.update(overrides)

        for key, value in prop.items():
            setattr(instance, key, self._resolve_value(value))

        self.event_dispatcher.after_build_up(
            name=name, instance=instance, overrides=overrides
        )

        return instance

    def clear(self, name=None):
        """
        Deletes all or the given singleton instances.

        :param name: the name of the singleton instance that shoud be
                     destroied.
        :type name: str
        """
        if name:
            del self.singletons[name]
        else:
            self.singletons = {}

        self.event_dispatcher.after_clear(name=name)

    def create_child_container(self, settings):
        # TODO: Copy singleton reference into the child container
        orig_settings = copy(self.settings)
        orig_settings.update(settings)
        return type(self)(orig_settings, parent=self)

    def __dir__(self):
        """
        override the base dir and extend with the configuration names.

        :returns: list of strings
        """
        d = []
        d.extend(dir(type(self)))
        d.extend(self.__dict__.keys())
        d.extend(self.names)
        return list(set(d))

    def __getattr__(self, name):
        """
        resolves the given name in this container.

        :param name: the key to resolve.
        :type name: str

        :returns: object
        """
        if not name in self.settings:
            raise AttributeError(
                'no component named "%s". please adjust in settings.' % name)
        return self.resolve(name)


def reference(value):
    return 'ref:{0}'.format(value)

ref = reference


def relation(value):
    return 'rel:{0}'.format(value)

rel = relation


def module(value):
    return 'mod:{0}'.format(value)

mod = module


def factory(value):
    return 'factory:{0}'.format(value)

fac = factory


def attr(value):
    return 'attr:{0}'.format(value)
