# coding: utf-8

from __future__ import absolute_import
from di import DIContainer
import unittest
from unittest import TestCase


class TestPerson(object):

    def __init__(self, first_name, last_name, age):
        self.first_name = first_name
        self.last_name = last_name
        self.age = age


TEST_DI_SETTINGS = {
    'person': {
        'type': 'test.TestPerson',
        'args': {
            '': [None, None, 0]
        }
    },
    'jessica': {
        'type': 'test.TestPerson',
        'args': {
            'first_name': 'Jessica',
            'last_name': 'Backhaus',
            'age': 27,
        },
        'singleton': True,
    },
    'jens': {
        'type': 'test.TestPerson',
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
        'type': 'test.TestPerson',
        'singleton': True,
        'lazy': False,
        'args': {'': ['Jens', 'Blawatt', 27]},
    },
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
        self.manager.register('henrik', {'type': 'test.TestPerson', 'singleton': True, 'args': {'': ['Henrik', 'Blawatt', 24]}})

        henrik1 = self.manager.henrik
        henrik2 = self.manager.resolve('henrik')

        self.assertEqual(henrik1, henrik2)
        self.assertEqual(henrik1.first_name, 'Henrik')
        self.assertEqual(henrik1.last_name, 'Blawatt')
        self.assertEqual(henrik1.age, 24)


if __name__ == '__main__':
    unittest.main()
