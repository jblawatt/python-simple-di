# coding: utf-8

from __future__ import absolute_import, unicode_literals

import mock

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from di import DIContainer, DIConfig, rel, relation, RelationResolver, \
    ref, reference, ReferenceResolver


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


class ResolverTestCase(unittest.TestCase):

    def test__relation_resolver(self):

        def inner_test(setting):

            container = DIContainer({
                'main_instance': DIConfig(type='mock.MagicMock', args={'referenced_instance': setting}),
                'referenced_instance': DIConfig(type='mock.MagicMock', singleton=True)
            })

            main = container.resolve('main_instance')
            referenced = container.resolve('referenced_instance')
            self.assertEqual(main.referenced_instance, referenced)

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
                'main_instance': DIConfig(type='mock.MagicMock', args={'python_version': setting})
            })

            main = container.resolve('main_instance')
            self.assertEqual(main.python_version, sys.version)

        for reference_setting in (
                'ref:sys.version',
                ref('sys.version'),
                reference('sys.version'),
                ReferenceResolver('sys.version')):
            inner_test(reference_setting)