# coding: utf-8

from __future__ import absolute_import, unicode_literals

import os
import sys
import tempfile
import mock

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from di import DIContainer, DIConfig, rel, relation, RelationResolver, \
    ref, reference, ReferenceResolver, mod, module, ModuleResolver


class TestConfigurationTestCase(unittest.TestCase):

    def test__type_missing_error(self):
        """
        Passes if a ValueError is thrown becouse there is no type given.
        :return:
        """
        def inner():
            DIContainer({'name': {}})
        self.assertRaises(ValueError, inner)

    def test__config(self):
        """
        Passes if there is a DIConfig Instance created with the given configuration.
        """
        test_config = {
            'type': 'mock.MagicMock',
            'args': [],
            'properties': {},
            'singleton': True,
            'lazy': False,
            'assert_type': None
        }

        container = DIContainer({'test_config': test_config})
        conf = container.settings['test_config']
        self.assertIsInstance(conf, DIConfig)
        for key, value in test_config.items():
            self.assertEqual(getattr(conf, key), value)

    def test__create_non_lazy_instances(self):
        """
        Passes if resolve is called with the none_lazy key.
        """
        with mock.patch('di.DIContainer.resolve') as patched_func:
            DIContainer({
                'none_lazy': {'type': 'mock.MagicMock', 'lazy': False},
                'lazy': {'type': 'mock.MagicMock'}
            })

        self.assertEqual(patched_func.called,1)
        self.assertTrue(patched_func.called_with_args(['none_lazy']))

    def test__register(self):
        """
        Passes if `runtime_config` is not configured and is configured at the
        end of the test. the second registration raises an error.
        """
        container = DIContainer({})

        def raises_not_registred():
            container.resolve('runtime_config')

        self.assertRaises(KeyError, raises_not_registred)
        container.register('runtime_config', {'type': 'mock.MagicMock'})
        runtime_config = container.resolve('runtime_config')
        self.assertIsNotNone(runtime_config)

        def raises_already_registred():
            container.register('runtime_config', {'type': 'mock.MagicMock'})

        self.assertRaises(KeyError, raises_already_registred)

    def test__python_type(self):
        """
        Passes if a given python type also creates an instance.
        :return:
        """
        container = DIContainer({
            'a': DIConfig(type=mock.Mock)
        })
        self.assertIsInstance(container.a, mock.Mock)


class EventDispatcherTestCase(unittest.TestCase):

    def test__hooks_called(self):

        # TODO: improve.

        container = DIContainer({'a': DIConfig(
            type='mock.Mock',
            args={'': [mock.Mock()], 'b': mock.Mock()}
        )}, event_dispatcher=mock.Mock())

        container.resolve('a')
        container.clear()
        container.resolve_type('a')
        container.register('b', DIConfig(type='mock.Mock'))

        for method in ('initialized', 'before_register', 'after_register',
                       'after_resolve', 'before_resolve', 'before_build_up',
                       'after_build_up', 'before_resolve_type', 'after_resolve_type',
                       'after_clear',):
            self.assertTrue(
                getattr(container.event_dispatcher, method).called,
                'called method {0}.'.format(method))


class TypeCreationTestCase(unittest.TestCase):

    @staticmethod
    def get_john_doe_config():
        return {
            'type': 'mock.MagicMock',
            'args': {
                'first_name': 'John',
                'last_name': 'Doe',
                'age': 45
            },
            'properties': {
                'email': 'john@doe.org'
            }
        }

    def test__simple_resolve(self):
        """
        Passes if john is created with the given arguments and property settings.
        john must be resolvable by `resolve` method and by the containers
        __getitem__ method.
        """
        john_config = self.get_john_doe_config()
        container = DIContainer({'john_doe': john_config})
        john_resolve = container.resolve('john_doe')
        john_getitem = container.john_doe
        self.assertIsNotNone(john_resolve)
        self.assertIsNotNone(john_getitem)

        for john in (john_getitem, john_resolve):
            for key, value in john_config['args'].items():
                self.assertEqual(getattr(john, key), value)
            for key, value in john_config['properties'].items():
                self.assertEqual(getattr(john, key), value)

    def test__resolve_type(self):
        """
        Passes if resolve type returns the configured type for key a.
        """
        container = DIContainer({'a': {
            'type': 'mock.Mock'
        }})

        resolved_type = container.resolve_type('a')
        self.assertEqual(resolved_type, mock.Mock)

    def test__singleton(self):
        """
        Passes if the singleton configuration works and the same instance
        if given if resolve is called twice.
        """
        container = DIContainer({
            'singleton': DIConfig(type='mock.MagicMock', singleton=True)
        })

        first = container.resolve('singleton')
        second = container.resolve('singleton')

        self.assertEqual(first, second)
        self.assertIn('singleton', container.singletons)

    def test__non_singleton(self):
        """
        Passes if the singleton configuration works and different instances
        are given if resolve is called twice.
        """
        container = DIContainer({
            'non_singleton': DIConfig(type='mock.MagicMock', singleton=False)
        })

        first = container.resolve('non_singleton')
        second = container.resolve('non_singleton')

        self.assertNotEquals(first, second)
        self.assertNotIn('non_singleton', container.singletons)

    def test__assert_type(self):
        """
        Passes if the type resolution of `type_implemenation` works and
        the resolution of `no_type_implementation` raises a `ValueError`.
        :return:
        """

        container = DIContainer({
            'type_implementation': DIConfig(type='mock.MagicMock', assert_type='mock.MagicMock'),
            'no_type_implementation': DIConfig(type='object', assert_type='mock.MagicMock')
        })

        resolved_instance = container.resolve('type_implementation')
        self.assertIsNotNone(resolved_instance)

        def raises():
            container.resolve('no_type_implementation')
        self.assertRaises(TypeError, raises)

    def test__assert_init_args(self):

        mock_types = mock.Mock()
        mock_types.ArgsCalledType = mock.Mock(name='ArgsCalledType')
        mock_types.KWargsCalledType = mock.Mock(name='KWargsCalledType')
        mock_types.MixedCalledType = mock.Mock(name='MixedCalledType')

        sys.modules['mock_types'] = mock_types

        args = [mock.Mock(), mock.Mock()]
        kwargs = {'a': mock.Mock(), 'b': mock.Mock()}
        mixed = {'': args}
        mixed.update(kwargs)

        container = DIContainer({
            'args_instance': DIConfig(type='mock_types.ArgsCalledType', args=args),
            'kwargs_instance': DIConfig(type='mock_types.KWargsCalledType', args=kwargs),
            'mixed_instance': DIConfig(type='mock_types.MixedCalledType', args=mixed)
        })

        container.resolve('args_instance')
        self.assertEqual(mock_types.ArgsCalledType.called, 1)
        mock_types.ArgsCalledType.assert_called_with(*args)

        container.resolve('kwargs_instance')
        self.assertEqual(mock_types.KWargsCalledType.called, 1)
        mock_types.KWargsCalledType.assert_called_with(**kwargs)

        container.resolve('mixed_instance')
        self.assertEqual(mock_types.MixedCalledType.called, 1)
        mock_types.MixedCalledType.assert_called_with(*args, **kwargs)


    def test__extend_path(self):
        tmp_file = tempfile.NamedTemporaryFile(suffix='.py', delete=False)
        tmp_file.write('# coding: utf-8\nclass DynamicDummy(object):\n  pass')
        tmp_file.close()
        basename = os.path.basename(tmp_file.name)
        filename, ext = os.path.splitext(basename)
        container = DIContainer({
            'dynamic': DIConfig(type='{0}:{1}.DynamicDummy'.format(tempfile.tempdir, filename))
        })
        instance = container.resolve('dynamic')
        self.assertIsNotNone(instance)
        module = sys.modules[filename]
        self.assertIsInstance(instance, module.DynamicDummy)

        os.remove(tmp_file.name)


class ResolverTestCase(unittest.TestCase):

    def test__relation_resolver(self):
        """
        Passes if the related configured instances becomes injectet into
        the new created instance and set to it's property.
        """
        def inner_test(setting):

            container = DIContainer({
                'main_instance': DIConfig(
                    type='mock.MagicMock',
                    args={'referenced_instance_construct': setting},
                    properties={'referenced_instance_property': setting}),
                'referenced_instance': DIConfig(type='mock.MagicMock', singleton=True)
            })

            main = container.resolve('main_instance')
            referenced = container.resolve('referenced_instance')
            self.assertEqual(main.referenced_instance_construct, referenced)
            self.assertEqual(main.referenced_instance_property, referenced)

        for resolver_setting in (
                'rel:referenced_instance',
                rel('referenced_instance'),
                relation('referenced_instance'),
                RelationResolver('referenced_instance')):
            inner_test(resolver_setting)

    def test__reference_resolver(self):
        import sys

        def inner_test(setting):
            container = DIContainer({
                'main_instance': DIConfig(
                    type='mock.MagicMock',
                    args={'python_version_construct': setting},
                    properties={'python_version_property': setting})
            })

            main = container.resolve('main_instance')
            self.assertEqual(main.python_version_construct, sys.version)
            self.assertEqual(main.python_version_property, sys.version)

        for reference_setting in (
                'ref:sys.version',
                ref('sys.version'),
                reference('sys.version'),
                ReferenceResolver('sys.version')):
            inner_test(reference_setting)

    def test__module_resolver(self):

        import json

        def inner_test(setting):
            container = DIContainer({
                'test_instance': DIConfig(
                    type='mock.MagicMock',
                    args={'serializer_constructor': setting},
                    properties={'serializer_property': setting})
            })

            instance = container.resolve('test_instance')
            self.assertEqual(instance.serializer_constructor, json)
            self.assertEqual(instance.serializer_property, json)

        for module_setting in (
                'mod:json',
                mod('json'),
                module('json'),
                ModuleResolver('json')):
            inner_test(module_setting)

    def test__factory_resolver(self):

        FACTORY_VALUE = mock.MagicMock()

        def inner_test(setting):
            container = DIContainer({
                'instance': DIConfig(
                    type='mock.MagicMock',
                    args={'factory_value_constructor': setting},
                    properties={'factory_value_property': setting})
            })

            instance = container.resolve('instance')
            self.assertEqual(instance.factory_value_constructor, FACTORY_VALUE)
            self.assertEqual(instance.factory_value_property, FACTORY_VALUE)

        mock_module = mock.MagicMock()
        mock_module.factory_method = lambda: FACTORY_VALUE

        sys.modules['mock_module'] = mock_module

        for factory_setting in ('factory:mock_module.factory_method', ):
            inner_test(factory_setting)

    def test__attribute_resolver(self):

        ATTR_VALUE = mock.MagicMock()

        def inner_test(setting):
            container = DIContainer({
                'instance': DIConfig(
                    type='mock.MagicMock',
                    args={'attr_value_constructor': setting},
                    properties={'attr_value_property': setting})
            })

            instance = container.resolve('instance')
            self.assertEqual(instance.attr_value_constructor, ATTR_VALUE)
            self.assertEqual(instance.attr_value_property, ATTR_VALUE)

        mock_module = mock.MagicMock()
        mock_module.mock_instance = mock.MagicMock()
        mock_module.mock_instance.mock_attribute = ATTR_VALUE

        sys.modules['mock_module'] = mock_module

        for attr_setting in ('attr:mock_module.mock_instance.mock_attribute', ):
            inner_test(attr_setting)


class InjectDecoratorTestCase(unittest.TestCase):

    def test__inject(self):

        container = DIContainer({'service': DIConfig(type=mock.Mock, singleton=True)})

        @container.inject(service='service')
        def some_function(data, service):
            service.call_service_function(data)

        some_function('data')
        some_function(data='data', service=mock.Mock())
        some_function('data', mock.Mock())

        service = container.resolve('service')
        self.assertEqual(service.call_service_function.called, 1)