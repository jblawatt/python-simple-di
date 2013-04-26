# coding: utf-8

import logging


_logger = logging.getLogger(__name__)


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
            Resolves the following name, trys to __import__ it and passes
            the result as argument.
        - rel:
            Resolves an instance with the following name an passes it as
            argument. (warning: beware of recursion error.)
        - ref:
            Resolves a variable with the following name off a given module
            and passes it as an argument.

    """

    def __init__(self, settings):
        """
        Creates a new DI Container.

        :param settings: The dictionary, containing the container-configuration.
        """
        self.settings = settings
        self.names = settings.keys()
        self.singletons = {}

        for key, conf in self.settings.items():
            if not conf.get('lazy', True):
                self.resolve(key)

    # ---------------------------
    # private methods
    # ---------------------------
    def _resolve_type(self, python_name):
        """
        Resolves a type.
        """
        type_path, type_name = python_name.rsplit('.', 1)
        mod = __import__(type_path)
        return getattr(mod, type_name)

    def _resolve_value(self, value_conf):
        value = value_conf
        if isinstance(value_conf, str):
            # keyword: rel - relation to another di object
            if value_conf.startswith('rel:'):
                key, name = value_conf.split(':', 1)
                return self.resolve(name)
            # keyword: mod - relation to an module import follows
            if value_conf.startswith('mod:'):
                key, name = value_conf.split(':', 1)
                return __import__(name)
            # reference to an type / variable in an module
            if value_conf.startswith('ref:'):
                key, name = value_conf.split(':', 1)
                mod_name, var_name = name.rsplit('.', 1)
                mod = __import__(mod_name)
                return getattr(mod, var_name)
        return value

    def _resolve_args(self, conf):
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

    def register(self, name, settings):
        pass

    def resolve(self, name):
        """
        Resolves an object by its name assigned in the configuration.

        :param name: object's name in the configuration.
        :returns: object
        """

        # check if there already is a singleton instance
        # for this name
        if name in self.singletons:
            return self.singletons[name]

        # load information to create the instance
        conf = self.settings[name]
        singleton = conf.get('singleton', False)
        type_ = self._resolve_type(conf['type'])

        # resolve the arguments to pass into the constructor
        _args, _kwargs = self._resolve_args(conf.get('args', []))

        # create the instance
        obj = type_(*_args, **_kwargs)
        obj = self.build_up(name, obj)

        if singleton:
            self.singletons[name] = obj

        return obj

    def build_up(self, name, instance, **overrides):
        """
        Injects the information spezified in the properties config
        into an existing object.

        :param name: name of the object definition in the container config.
        :param instance: the instance to buildup
        :param **overrides: sets/overrides the information of the config
                            with the given information.

        :returns: the buildup instance
        """
        prop = self.settings[name].get('properties', {}).copy()
        prop.update(overrides)

        for key, value in prop.items():
            setattr(instance, key, self._resolve_value(value))

        return instance

    def clear(self, name=None):
        """
        Deletes all or the given singleton instances.

        :param name: the name of the singleton instance that shoud be
                     destroied.
        """
        if name:
            del self.singletons[name]
        else:
            self.singletons = {}

    def __dir__(self):
        d = []
        d.extend(dir(type(self)))
        d.extend(self.__dict__.keys())
        d.extend(self.names)
        return list(set(d))

    def __getattr__(self, name):
        if not name in self.names:
            raise AttributeError('no component named "%s". please adjust in settings.' % name)
        return self.resolve(name)
