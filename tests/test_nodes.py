# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from unittest import TestCase
from collections import namedtuple

from yepr import nodes


class TestToken(TestCase):
    def test_base(self):
        self.assertIs(nodes.EqOp, nodes.EqOp.EQ.p)
        self.assertEqual('EqOp', nodes.EqOp.EQ.p.__name__)


class TestExpr(TestCase):
    def test_literal_base(self):
        self.assertIs(True, nodes.LiteralTrue().ex({}))
        self.assertIs(False, nodes.LiteralFalse().ex({}))
        self.assertIs(None, nodes.LiteralNull().ex({}))

        self.assertRegexpMatches(
            unicode(nodes.LiteralTrue()),
            r'<LiteralTrue at 0x[\da-f]+> val:True',
        )
        self.assertRegexpMatches(
            unicode(nodes.LiteralFalse()),
            r'<LiteralFalse at 0x[\da-f]+> val:False',
        )
        self.assertRegexpMatches(
            unicode(nodes.LiteralNull()),
            r'<LiteralNull at 0x[\da-f]+> val:None',
        )

    def test_literal_string(self):
        self.assertEqual('abc', nodes.LiteralString('abc').ex({}))
        self.assertEqual('', nodes.LiteralString('').ex({}))

    def test_literal_number(self):
        self.assertEqual(123, nodes.LiteralNumber('123').ex({}))
        self.assertEqual(123.23, nodes.LiteralNumber('123.23').ex({}))

    def test_unary_exp(self):
        def run_for(op, ctx=None):
            op = getattr(nodes.UnaryOp, op)
            ctx = ctx or {}

            return nodes.UnaryExp(op, nodes.LiteralNumber('123')).ex(ctx)

        self.assertEqual(False, run_for('NOT'))
        self.assertEqual(123, run_for('PLUS'))
        self.assertEqual(-123, run_for('MINUS'))

        with self.assertRaisesRegexp(TypeError, r'object of type \'int\' has no len'):
            run_for('HASH')

    def test_unary_exp_string(self):
        def run_for(op, ctx=None):
            op = getattr(nodes.UnaryOp, op)
            ctx = ctx or {}

            return nodes.UnaryExp(op, nodes.LiteralString('abc')).ex(ctx)

        self.assertEqual(False, run_for('NOT'))

        with self.assertRaisesRegexp(TypeError, r'bad operand type for unary \+'):
            run_for('PLUS')

        with self.assertRaisesRegexp(TypeError, r'bad operand type for unary -'):
            run_for('MINUS')

        self.assertEqual(3, run_for('HASH'))

    def test_eq_exp(self):
        self.assertEqual(
            True,
            nodes.EqExp(
                nodes.EqOp.EQ,
                nodes.LiteralNumber('123'),
                nodes.LiteralNumber('123'),
            ).ex({})
        )
        self.assertEqual(
            False,
            nodes.EqExp(
                nodes.EqOp.NE,
                nodes.LiteralNumber('123'),
                nodes.LiteralNumber('123'),
            ).ex({})
        )
        self.assertEqual(
            True,
            nodes.EqExp(
                nodes.EqOp.IS,
                nodes.LiteralNumber('123'),
                nodes.LiteralNumber('123'),
            ).ex({})
        )

        self.assertEqual(
            True,
            nodes.EqExp(
                nodes.EqOp.EQ,
                nodes.LiteralNumber('123'),
                nodes.LiteralNumber('123.0'),
            ).ex({})
        )
        self.assertEqual(
            True,
            nodes.EqExp(
                nodes.EqOp.ISNOT,
                nodes.LiteralNumber('123'),
                nodes.LiteralNumber('123.0'),
            ).ex({})
        )

        self.assertEqual(
            True,
            nodes.EqExp(
                nodes.EqOp.RE,
                nodes.LiteralString('abc'),
                nodes.LiteralString(r'^\w+$'),
            ).ex({})
        )
        self.assertEqual(
            True,
            nodes.EqExp(
                nodes.EqOp.NR,
                nodes.LiteralString('.abc'),
                nodes.LiteralString(r'^\w+$'),
            ).ex({})
        )

    def test_or_exp(self):
        self.assertEqual(
            123,
            nodes.LogicOrExp(
                nodes.LogicOp.OR,
                nodes.LiteralNumber('123'),
                nodes.LiteralNumber('456'),
            ).ex({})
        )
        self.assertEqual(
            456,
            nodes.LogicOrExp(
                nodes.LogicOp.OR,
                nodes.LiteralNumber('0'),
                nodes.LiteralNumber('456'),
            ).ex({})
        )

    def test_and_exp(self):
        self.assertEqual(
            456,
            nodes.LogicAndExp(
                nodes.LogicOp.AND,
                nodes.LiteralNumber('123'),
                nodes.LiteralNumber('456'),
            ).ex({})
        )
        self.assertEqual(
            False,
            nodes.LogicAndExp(
                nodes.LogicOp.AND,
                nodes.LiteralNumber('0'),
                nodes.LiteralNumber('456'),
            ).ex({})
        )

    def test_cond_exp(self):
        self.assertEqual(
            123,
            nodes.CondExp(
                nodes.LiteralTrue(),
                nodes.LiteralNumber('123'),
                nodes.LiteralNumber('456'),
            ).ex({})
        )

        self.assertEqual(
            456,
            nodes.CondExp(
                nodes.LiteralFalse(),
                nodes.LiteralNumber('123'),
                nodes.LiteralNumber('456'),
            ).ex({})
        )

    def test_binary_exp(self):
        for val, op in (
            (True, nodes.BinaryOp.LT),
            (True, nodes.BinaryOp.LE),
            (False, nodes.BinaryOp.GT),
            (False, nodes.BinaryOp.GE),
        ):
            self.assertEqual(
                val,
                nodes.BinaryExp(
                    op,
                    nodes.LiteralNumber('123'),
                    nodes.LiteralNumber('456'),
                ).ex({})
            )

        self.assertEqual(
            True,
            nodes.BinaryExp(
                nodes.BinaryOp.IN,
                nodes.LiteralString('b'),
                nodes.LiteralString('abc'),
            ).ex({})
        )

        self.assertEqual(
            True,
            nodes.BinaryExp(
                nodes.BinaryOp.NOTIN,
                nodes.LiteralString('e'),
                nodes.LiteralString('abc'),
            ).ex({})
        )


class TestSemantics(TestCase):
    def setUp(self):
        self.s = nodes.YepSemantics()

    def test_operator(self):
        s = self.s

        # OP_BINARY
        self.assertEqual(nodes.BinaryOp.LE, s.OP_BINARY('<='))
        self.assertEqual(nodes.BinaryOp.LE, s.OP_BINARY('le'))
        self.assertEqual(nodes.BinaryOp.IN, s.OP_BINARY('in'))
        self.assertEqual(nodes.BinaryOp.NOTIN, s.OP_BINARY('not in'))

        # OP_EQ
        self.assertEqual(nodes.EqOp.ISA, s.OP_EQ('isa'))
        self.assertEqual(nodes.EqOp.ISNOT, s.OP_EQ('is not'))
        self.assertEqual(nodes.EqOp.ISNOT, s.OP_EQ(['is', 'not']))

        # OP_AND & OP_OR
        self.assertEqual(nodes.LogicOp.AND, s.OP_AND('and'))
        self.assertEqual(nodes.LogicOp.AND, s.OP_AND('&&'))
        self.assertEqual(nodes.LogicOp.OR, s.OP_OR('or'))
        self.assertEqual(nodes.LogicOp.OR, s.OP_OR('||'))

        # OP_UNARY
        self.assertEqual(nodes.UnaryOp.NOT, s.OP_UNARY('!'))
        self.assertEqual(nodes.UnaryOp.NOT, s.OP_UNARY('not'))
        self.assertEqual(nodes.UnaryOp.PLUS, s.OP_UNARY('+'))
        self.assertEqual(nodes.UnaryOp.MINUS, s.OP_UNARY('-'))
        self.assertEqual(nodes.UnaryOp.HASH, s.OP_UNARY('#'))

    def test_conditional_expression(self):
        s = self.s
        Ast = namedtuple('Ast', 'cond, val, yes, no')

        cond = s.conditional_expression(Ast(
            nodes.LiteralNull(),
            None,
            None,
            None,
        ))

        self.assertIsInstance(cond, nodes.LiteralNull)

        cond = s.conditional_expression(Ast(
            nodes.LiteralNull(),
            True,
            nodes.LiteralNumber('1'),
            nodes.LiteralNumber('2'),
        ))
        self.assertIsInstance(cond, nodes.CondExp)

        self.assertEqual(cond.ex({}), 2)
