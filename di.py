# coding: utf-8

from __future__ import unicode_literals, absolute_import

import sys
import inspect
import logging
import warnings
import functools

from abc import ABCMeta, abstractmethod
from collections import namedtuple
from copy import copy

__major__ = 1
__minor__ = 5
__bugfix__ = 2

__version__ = '%s.%s.%s' % (__major__, __minor__, __bugfix__)

__website__ = 'http://bitbucket.org/jblawatt/python-simple-di/'
__author__ = 'Jens Blawatt'
__author_email__ = 'jblawatt@googlemail.com'
__author_website__ = 'http://www.blawatt.de/'
__maintainer__ = __author__
__maintainer_email__ = __author_email__

_logger = logging.getLogger(__name__)


__all__ = (
    'DIEventDispatcher', 'DIContainer', 'attr', 'module', 'mod', 'factory',
    'RelationResolver', 'ReferenceResolver', 'ModuleResolver',
    'FactoryResolver', 'AttributeResolver', 'fac', 'relation', 'rel',
    'reference', 'ref',
)

py = sys.version_info
py3 = py >= (3, 0, 0)
py2 = not py3


if py3:
    string_types = (str,)
else:
    string_types = (str, unicode)


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

    def after_resolve_type(self, name, type, *args, **kwargs):
        pass

    def after_clear(self, name):
        pass


class Proxy(object):
    """
    Will replaced with the real proxy instance
    """

    def __init__(self, factory_method):
        raise NotImplementedError()


default_config = {
    'name': None,
    'type': None,
    'args': [],
    'singleton': False,
    'lazy': True,
    'properties': {},
    'assert_type': None,
    'factory_method': None,
}


class DIConfig(namedtuple('DIConfigBase', default_config.keys())):
    """
    This type is used for the internal configuration. Each configuraiton dict
    becomes passed into an instance of this class.
    """

    def __new__(cls, **kwargs):
        type_ = kwargs.get('type')
        if not type_:
            raise ValueError("'type' argument is required.")
        cls_kwargs = copy(default_config)
        cls_kwargs.update(kwargs)
        return super(DIConfig, cls).__new__(cls, **cls_kwargs)


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

        _logger.debug(
            'Container __init__ called. Begin to bootstrap this container.')

        dispatcher_type = kwargs.get('event_dispatcher', DIEventDispatcher)

        self.event_dispatcher = dispatcher_type(container=self)

        self.settings = settings.copy()
        for key, config in self.settings.items():
            if not isinstance(self.settings[key], DIConfig):
                # create an instance of DIConfig for each config element.
                # that makes it easier to work with it later.
                self.settings[key] = DIConfig(name=key, **config)
                _logger.debug('Created DIConfig for configuration key %s.', key)

        self.names = settings.keys()
        self.singletons = {}
        self.parent = kwargs.get('parent', None)

        # assign default resolvers. better use a resolver instance.
        # maybe remove this in some version.
        self.value_resolvers = {
            'mod': self._resolve_module_value,
            'ref': self._resolve_reference_value,
            'rel': self._resolve_relation_value,
            'factory': self._resolve_factory_value,
            'attr': self._resolve_attribute_value
        }

        # check if individual value_resolves are given. update the internal
        # resolver dictionary with this values.
        if 'value_resolvers' in kwargs:
            _logger.debug('Updating value_resolvers with the given ones.')
            warnings.warn(
                '"value_resolvers" is deprecated. '
                'Use a Resolver instance in your configuration.',
                DeprecationWarning)
            self.value_resolvers.update(kwargs.get('value_resolvers'))

        _logger.debug('checking for non-lazy configrations.')
        for key, conf in self.settings.items():
            if not conf.lazy:
                _logger.debug(
                    'found non-lazy configuration %s. resovling it.', key)
                self.resolve(key)

        # set the proxy type name
        self.proxy_type_name = kwargs.get(
            'proxy_type_name', 'lazy_object_proxy.Proxy')

        self.event_dispatcher.initialized()

    def import_module(self, name, package=None):
        """
        Internal method to wrap the import_module function.
        """
        _logger.debug('calling import_module with name=%s, package=%s.', name, package)
        from importlib import import_module
        return import_module(name, package)

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
        :type python_name: str|unicode

        :returns: type
        """

        # check if python_name contains a : to split path
        # and python_name

        _logger.debug('resolving type "%s."', python_name)

        if (py2 and isinstance(python_name, string_types)) or \
                (py3 and isinstance(python_name, str)):
            if ':' in python_name:
                path, python_name = python_name.split(':')
                if path not in sys.path:
                    sys.path.append(path)
            try:
                type_path, type_name = python_name.rsplit('.', 1)
            except ValueError:
                if py3:
                    type_path = 'builtins'
                    type_name = python_name
                else:  # 2.x
                    type_path = '__builtin__'
                    type_name = python_name
        else:
            if len(python_name) == 3:
                path, type_path, type_name = python_name
                if path not in sys.path:
                    sys.path.append(path)
            else:
                type_path, type_name = python_name

        mod = self.import_module(type_path)
        return getattr(mod, type_name)

    def _resolve_module_value(self, value_conf):
        """
        Resolves a module, given in the value_conf.
        :param value_conf: str
        :rtype: object
        """
        return ModuleResolver(value_conf).resolve(self)

    def _resolve_relation_value(self, value_conf):
        """
        Resolve an object with the given name in this container.
        :param value_conf: str
        :rtype: object
        """
        return RelationResolver(value_conf).resolve(self)

    def _resolve_reference_value(self, value_conf):
        """
        Resolves the given module and returns the given object off it.
        :param value_conf: str
        :rtype: object
        """
        return ReferenceResolver(value_conf).resolve(self)

    def _resolve_factory_value(self, value_conf):
        """
        Resolves the factory method and returns the factories response.
        :param value_conf:
        :rtype: object
        """
        return FactoryResolver(value_conf).resolve(self)

    def _resolve_attribute_value(self, value_conf):
        """
        Resolves an attribute of an instance.
        :param value_conf:
        :return: object
        """
        return AttributeResolver(value_conf).resolve(self)

    def _resolve_value(self, value_conf):
        """
        resolves a value from a string.

        depeding on then value prefix some furthur action will follow:
        * ''rel'': relates to anoter type of in this container.
        * ''mod'': imports and return a module/package with that name.
        * ''ref'': load a variable off a module/package.
        * ''attr'':
        * ''factory'':

        :param value_conf: the value to pass or resolve.
        :type value_conf: dict

        :returns: object
        """
        value = value_conf
        if isinstance(value, Resolver):
            return value.resolve(self)
        if isinstance(value_conf, string_types):
            for key, resolver in self.value_resolvers.items():
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
                '%s is not a subclass of %s. This violates the '
                'configuration for key %s'
                % (type_, expected, conf_name)
            )

    def _get_proxy_type(self):
        """
        Returns the Proxy type, used for lazy resolving.

        :return: The type used as Proxy.
        :rtype: di.Proxy
        """
        try:
            proxy_type = self._resolve_type(self.proxy_type_name)
        except ImportError as e:
            # We do not provide lazy-object-proxy because of different licences.
            raise ImportError(
                'got an error while importing the proxy type `%s`. '
                'make sure you installed `lazy-object-proxy` or another '
                'lazy object implementation. (i.e. django.utils.functional'
                '.SimpleLazyObject).' % self.proxy_type_name)
        return proxy_type

    # ---------------------------
    # public methods
    # ---------------------------
    def register(self, name, settings):
        """
        register a new configuration at runtime.

        :param name: the name for the new configuration.
        :type name: str, unicode
        :param settings: the sessings dictionary for the new type.
        :type settings: dict, di.DIConfig
        """

        self.event_dispatcher.before_register(name=name, settings=settings)

        if name in self.settings:
            raise KeyError('there is already a configuration with this name.')
        if isinstance(settings, dict):
            conf = DIConfig(name=name, **settings)
        else:
            conf = settings
        self.settings[name] = conf

        self.event_dispatcher.after_register(name=name, settings=conf)

    def resolve(self, name):
        """
        Resolves an object by its name assigned in the configuration.

        :param name: object's name in the configuration.
        :type name: str|unicode

        :returns: object
        """

        self.event_dispatcher.before_resolve(name=name)

        # check if there already is a singleton instance
        # for this name
        if name in self.singletons:
            return self.singletons[name]

        # load information to create the instance
        conf = self.settings[name]
        singleton = conf.singleton
        if isinstance(conf.type, string_types):
            type_ = self._resolve_type(conf.type)
        else:
            type_ = conf.type

        # assert weather the type implements the
        # configures basetype.
        assert_type = conf.assert_type
        if assert_type:
            expected_type = self._resolve_type(assert_type)
            self._check_type(name, type_, expected_type)

        # resolve the arguments to pass into the constructor
        _args, _kwargs = self._resolve_args(conf.args)

        # create the instance
        if conf.factory_method:
            obj = getattr(type_, conf.factory_method)(*_args, **_kwargs)
        else:
            obj = type_(*_args, **_kwargs)
        obj = self.build_up(name, obj)

        if singleton:
            self.singletons[name] = obj

        self.event_dispatcher.after_resolve(name=name, instance=obj)

        return obj

    def resolve_lazy(self, name):
        """
        Return an object proxy to the to lazy resolve requested instance.

        :param name: object's name in the configuration.
        :type name: str|unicode

        :return: The proxy object to lazy access the instance.
        :rtype: di.Proxy
        """
        proxy_type = self._get_proxy_type()
        return proxy_type(lambda: self.resolve(name))

    def resolve_type(self, name):
        """
        Resolves a type for the given name in the configuration.

        :param name: name of an object in the configuration.
        :type name: str|unicode

        :returns: type
        :rtype: type
        """

        self.event_dispatcher.before_resolve_type(name=name)

        conf = self.settings[name]
        type_ = self._resolve_type(conf.type)

        self.event_dispatcher.after_resolve_type(name=name, type=type_)

        return type_

    def resolve_type_lazy(self, name):
        """
        Lazy resolves a type for the given name in the configuration.

        :param name: name of an object in the configuration.
        :type name: str|unicode

        :return: The proxy object to lazy access the type.
        :rtype: lazy_object_proxy.Proxy
        """
        proxy_type = self._get_proxy_type()
        return proxy_type(lambda: self.resolve_type(name))

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
        conf = self.settings[name]
        prop = conf.properties.copy()
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
        if name is not None:
            if name in self.singletons:
                del self.singletons[name]
        else:
            self.singletons = {}

        self.event_dispatcher.after_clear(name=name)

    def create_child_container(self, *args, **kwargs):
        """
        Creates a child container with the given Configuration
        :returns: a new container instance on this type.
        :rtype: di.DIContainer
        """
        kwargs['parent'] = self
        return type(self)(*args, **kwargs)

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
        Resolves the given name in this container.

        :param name: the key to resolve.
        :type name: str

        :returns: object
        :rtype: object
        """
        if name not in self.settings:
            if self.parent is not None:
                return self.parent.resolve(name)
            raise AttributeError(
                'no component named "%s". please adjust in settings.' % name)
        return self.resolve(name)

    def inject(self, force=False, **inject_kwargs):
        """
        method that can be used as decorator for another function.
        it can inject values from the container to keyworkd arguments,
        given in the **inject_kwargs.

        :param force: defines if the given value should be overwritten with
            the containers value. default: False.
        :type force: bool
        :rtype: types.FunctionType
        """
        def wrapper(func):

            @functools.wraps(func)
            def inner(*args, **kwargs):

                # if args are given we map the args to the kwargs to
                # ensure wie set the right values.
                if args:
                    args_spec = inspect.getargspec(func)
                    for i, arg_value in enumerate(args):
                        kwargs[args_spec.args[i]] = arg_value
                for key, name in inject_kwargs.items():
                    if force or key not in kwargs:
                        kwargs[key] = self.resolve(name)
                _logger.debug(
                    'calling decorated function %s with %s.',
                    func.__name__, kwargs)
                return func(**kwargs)

            return inner

        return wrapper


class Resolver(object):

    __metaclass__ = ABCMeta

    key = ''

    def __init__(self, value_conf):
        """
        :param value_conf: argument configuration string.
        :type value_conf: str, unicode
        """
        if value_conf.startswith(self.key):
            self.value_conf = value_conf[len(self.key) + 1:]
        else:
            self.value_conf = value_conf

    @abstractmethod
    def resolve(self, container):
        """
        :param container: a dicontainer instance
        :type container: di.DIContainer
        """
        raise NotImplementedError()


class ReferenceResolver(Resolver):

    key = 'ref'

    def resolve(self, container):
        """
        Resolves a value by pythonpath.
        :type container: di.DIContainer
        :param container:
        :rtype: object
        """
        try:
            mod_name, var_name = self.value_conf.rsplit('.', 1)
        except ValueError:
            # to many values to unpack. no . in it.
            return container.import_module(self.value_conf)
        else:
            mod = container.import_module(mod_name)
            return getattr(mod, var_name)


reference = ref = ReferenceResolver


class RelationResolver(Resolver):

    key = 'rel'

    def resolve(self, container):
        """
        :type container: di.DIContainer
        :param container: The Container Instance to lookup in.
        :rtype: object
        """
        return container.resolve(self.value_conf)


relation = rel = RelationResolver


class ModuleResolver(Resolver):

    key = 'mod'

    def resolve(self, container):
        """
        :type container: di.DIContainer
        :param container: The Container Instancze to resolve with.
        :rtype: object
        """
        return container.import_module(self.value_conf)


module = mod = ModuleResolver


class FactoryResolver(Resolver):

    key = 'factory'

    def resolve(self, container):
        """
        :type container: di.DIContainer
        :param container:
        :rtype: object
        """
        mod_name, factory_name = self.value_conf.rsplit('.', 1)
        mod = container.import_module(mod_name)
        return getattr(mod, factory_name)()


fac = factory = FactoryResolver


class AttributeResolver(Resolver):

    key = 'attr'

    def resolve(self, container):
        """
        :type container: di.DIContainer
        :param container:
        :rtype: object
        """
        pre_conf, attr_name = self.value_conf.rsplit('.', 1)
        instance = ReferenceResolver(pre_conf).resolve(container)
        return getattr(instance, attr_name)

attr = attribute = AttributeResolver
