# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from builtins import str

from unittest import TestCase

from yepr.parser import Parser


class TestParser(TestCase):
    def test_base(self):
        parser = Parser()
        ast = parser.parse('a and b')

        self.assertEqual(
            ast.ast(),
            {
                '$type': 'LogicAndExp',
                '$op': '<LogicOp(&&)>',
                'l': {
                    '$type': 'LiteralString',
                    'val': 'a'
                },
                'r': {
                    '$type': 'LiteralString',
                    'val': 'b'
                }
            }
        )

        self.assertEqual(ast.ex({}), 'b')

        self.assertEqual(parser.parse_and_ex('a or b', {}), 'a')
        self.assertEqual(parser.parse_and_ex('a and b or c', {}), 'b')
        self.assertEqual(parser.parse_and_ex('a and b and c', {}), 'c')
