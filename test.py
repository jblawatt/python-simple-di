# coding: utf-8

from __future__ import absolute_import

import os
import sys
import mock
import tempfile
import unittest
from unittest import TestCase

from di import DIContainer


class PersonBase(object):

    first_name = None
    last_name = None
    age = None


class TestPersonWithBase(PersonBase):

    def __init__(self, first_name, last_name, age):
        self.first_name = first_name
        self.last_name = last_name
        self.age = age


class TestPerson(object):

    def __init__(self, first_name, last_name, age):
        self.first_name = first_name
        self.last_name = last_name
        self.age = age


temp_file = tempfile.mkdtemp()
temp_path, temp_module = temp_file.rsplit(os.sep, 1)
temp_file = temp_file + '.py'


TEST_DI_SETTINGS = {
    'person': {
        'type': '__main__.TestPerson',
        'args': {
            '': [None, None, 0]
        }
    },
    'jessica': {
        'type': '__main__.TestPerson',
        'args': {
            'first_name': 'Jessica',
            'last_name': 'Backhaus',
            'age': 27,
        },
        'singleton': True,
    },
    'jens': {
        'type': '__main__.TestPerson',
        'singleton': True,
        'args': {
            '': ['Jens', 'Blawatt', 27]
        },
        'properties': {
            'hobbies': ['Tennis', 'Programming'],
            'loves': 'rel:jessica',
        }
    },
    'jens_nl': {
        'type': '__main__.TestPerson',
        'singleton': True,
        'lazy': False,
        'args': {'': ['Jens', 'Blawatt', 27]},
    },
    'jens_autopath': {
        'type': temp_path + ':' + temp_module + '.AutoPathPerson',
        'properties': {
            'first_name': 'Jens',
            'last_name': 'Blawatt'
        }
    },
    'jens_assert_base': {
        'type': '__main__.TestPersonWithBase',
        'assert_type': '__main__.PersonBase',
        'args': {'': ['Jens', 'Blawatt', 27]},
    },
    'jens_assert_no_base': {
        'type': '__main__.TestPerson',
        'assert_type': '__main__.PersonBase',
        'args': {'': ['Jens', 'Blawatt', 27]},
    },
    'logging_mod': {
        'type': '__builtin__.dict',
        'args': {'logging': 'mod:logging'}
    },
    'logging_ref': {
        'type': '__builtin__.dict',
        'args': {'DEBUG': 'ref:logging.DEBUG'}
    }
}


class DIContainerTestCase(TestCase):

    def setUp(self):
        self.manager = DIContainer(TEST_DI_SETTINGS)

    def test__person(self):
        p1 = self.manager.resolve('person')
        p2 = self.manager.resolve('person')

        self.assertIsNotNone(p1)
        self.assertIsNotNone(p2)

        self.assertNotEqual(p1, p2)

    def test__singleton(self):
        j1 = self.manager.resolve('jessica')
        j2 = self.manager.resolve('jessica')

        self.assertIsNotNone(j1)
        self.assertIsNotNone(j2)

        self.assertEqual(j1, j2)

    def test__relation(self):
        jessica = self.manager.resolve('jessica')
        jens = self.manager.resolve('jens')

        self.assertIsNotNone(jessica)
        self.assertIsNotNone(jens)

        self.assertEqual(jens.loves, jessica)
        self.assertEqual(jens.hobbies, ['Tennis', 'Programming'])

    def test__attr(self):
        jens1 = self.manager.resolve('jens')
        jens2 = self.manager.jens

        self.assertEqual(jens1, jens2)

        p1 = self.manager.person
        p2 = self.manager.person

        self.assertNotEqual(p1, p2)

    def test__lazy(self):
        self.assertIn('jens_nl', self.manager.singletons)
        self.assertNotIn('jens', self.manager.singletons)

    def test__register(self):
        self.manager.register('henrik', {
            'type': 'test.TestPerson',
            'singleton': True,
            'args': {'': ['Henrik', 'Blawatt', 24]}
        })

        henrik1 = self.manager.henrik
        henrik2 = self.manager.resolve('henrik')

        self.assertEqual(henrik1, henrik2)
        self.assertEqual(henrik1.first_name, 'Henrik')
        self.assertEqual(henrik1.last_name, 'Blawatt')
        self.assertEqual(henrik1.age, 24)

    def test_autopath(self):

        def create_tempmodule():
            with open(temp_file, 'w') as f:
                f.write(
                    "class AutoPathPerson(object):\n"
                    "    pass\n"
                )

        create_tempmodule()

        jens_autopath = self.manager.jens_autopath
        self.assertIsNotNone(jens_autopath)
        self.assertEqual(jens_autopath.first_name, 'Jens')
        self.assertEqual(jens_autopath.last_name, 'Blawatt')
        self.assertIn(temp_path, sys.path)

    def test_assertbasetype(self):

        def will_raise():
            o = self.manager.jens_assert_no_base
            assert o

        def will_not_raise():
            o = self.manager.jens_assert_base
            assert o

        self.assertRaises(TypeError, will_raise)

        try:
            will_not_raise()
        except Exception as e:
            self.fail('raised unexpected error: %s' % e)

    def test_logging_mod(self):
        objekt = self.manager.logging_mod
        self.assertTrue(isinstance(objekt, dict))
        module = objekt.get('logging')
        self.assertEqual(module.DEBUG, 10)

    def test_logging_ref(self):
        objekt = self.manager.logging_ref
        value = objekt.get('DEBUG')
        self.assertTrue(value, 10)

    def test_resolve_type(self):
        type_ = self.manager.resolve_type('jens')
        self.assertEqual(type_, TestPerson)

    def test_does_not_exist(self):
        def fnc():
            self.manager.does_not_exist
        self.assertRaises(AttributeError, fnc)

    def test_dir(self):
        values = dir(self.manager)
        for k in TEST_DI_SETTINGS.keys():
            self.assertIn(k, values)

    def test_register_registered(self):
        def fnc():
            self.manager.register('jens', dict())
        self.assertRaises(KeyError, fnc)

    def test_clear_singleton(self):
        def setUp():
            self.manager.singletons['foo'] = 'FOO'
            self.manager.singletons['bar'] = 'BAR'

        setUp()
        self.manager.clear('not-in-singletons')
        self.manager.clear('foo')
        self.assertNotIn('foo', self.manager.singletons)
        self.assertIn('bar', self.manager.singletons)

        self.manager.singletons = dict()

        setUp()
        self.manager.clear()
        self.assertNotIn('foo', self.manager.singletons)
        self.assertNotIn('bar', self.manager.singletons)

    def test_events(self):
        manager = DIContainer(TEST_DI_SETTINGS, event_dispatcher=mock.MagicMock)
        for name in ('jens',):
            manager.resolve(name)

        manager.resolve_type('jessica')
        manager.clear()
        manager.register('henrik_2', {
            'type': 'test.TestPerson',
            'singleton': True,
            'args': {'': ['Henrik', 'Blawatt', 24]}
        })

        for method in ('initialized', 'before_register', 'after_register',
                       'after_resolve', 'before_resolve', 'before_build_up',
                       'after_build_up', 'before_resolve_type', 'after_resolve_type',
                       'after_clear',):
            self.assertTrue(
                getattr(manager.event_dispatcher, method).called,
                'called method {}.'.format(method)
            )

    def test_inject(self):
        @self.manager.inject(person='henrik')
        def to_inject_function(person=None):
            self.assertIsNotNone(person)
            self.assertEqual(person.first_name, 'Henrik')

        to_inject_function()

    def test_child_container(self):

        ccontainer = self.manager.create_child_container({
            'jens': {
                'type': 'test.TestPerson',
                'args': {
                    'first_name': 'Jens',
                    'last_name': 'Backhaus',
                    'age': 32
                }
            }
        })

        jens_bl = self.manager.resolve('jens')
        jens_ba = ccontainer.resolve('jens')

        self.assertNotEqual(jens_ba, jens_bl)
        self.assertEqual(jens_ba.first_name, jens_bl.first_name)
        self.assertEqual(jens_ba.last_name, 'Backhaus')

if __name__ == '__main__':
    unittest.main()
