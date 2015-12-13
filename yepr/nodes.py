# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from sys import version_info
import re


class Base(object):
    if version_info >= (3,):
        # Don't return the "bytes" type from Python 3's __str__:
        def __str__(self):
            return self.__unicode__()
    else:
        def __str__(self):
            return self.__unicode__().encode('utf-8')

    __repr__ = __str__  # Language spec says must be string, not unicode.



# Token {{{
class TokenMeta(type):
    def __new__(mcs, name, bases, attrs):
        super_new = super(TokenMeta, mcs).__new__
        if not any(isinstance(b, TokenMeta) for b in bases):
            # If this isn't a subclass, don't do anything special.
            return super_new(mcs, name, bases, attrs)

        # Create the class.
        module = attrs.pop('__module__')
        new_class = super_new(mcs, name, bases, {'__module__': module})

        _tokens = {}
        # Add all attributes to the class.
        for obj_name, obj in attrs.items():
            if isinstance(obj, Token):
                obj.p = new_class   # for output token's base
                for txt in [obj.txt] + obj.alias:
                    if txt in _tokens:
                        raise ValueError('token "{}" txt/alias "{}" conflict with "{}"'.format(
                            obj_name, txt, _tokens[txt].txt
                        ))
                    _tokens[txt] = obj
            setattr(new_class, obj_name, obj)
        setattr(new_class, '_tokens', _tokens)

        return new_class


class Token(Base):
    # class var {{{
    _next_id = 1
    _token_map = {}
    _tokens = None        # per sub class
    # }}}

    __metaclass__ = TokenMeta

    def __init__(self, txt, *alias, **kwargs):
        id = Token._next_id
        Token._token_map[id] = self
        Token._next_id += 1

        self.id = id
        self.txt = txt
        self.alias = list(alias)
        self.opts = kwargs

    @classmethod
    def parse(cls, txt):
        return cls._tokens[txt]

    def __unicode__(self):
        return u'<{}({})>'.format(
            self.p.__name__,
            self.txt,
        )


class UnaryOp(Token):
    NOT = Token('!', 'not')
    PLUS = Token('+')
    MINUS = Token('-')
    HASH = Token('#')

class LogicOp(Token):
    AND = Token('&&', 'and')
    OR = Token('||', 'or')

class BinaryOp(Token):
    LE = Token('<=', 'le')
    LT = Token('<', 'lt')
    GE = Token('>=', 'ge')
    GT = Token('>', 'gt')

    IN = Token('in')
    NOTIN = Token('not in')

class EqOp(Token):
    EQ = Token('==', 'eq')
    NE = Token('!=', 'ne')
    RE = Token('=~')
    NR = Token('!~')

    ISA = Token('isa')
    ISNOT = Token('is not')
    IS = Token('is')

class AsgnOp(Token):
    ASGN = Token(':=')

# }}} Token



# Syntax {{{
class Node(Base):
    def __unicode__(self):
        return u'<{} at 0x{}>'.format(
            self.__class__.__name__,
            id(self),
        )

    def ast(self):
        ast = {
            '$type': self.__class__.__name__,
        }

        ast.update(self.ast_prop())

        return ast

    def ast_prop(self):
        return {}


class Exp(Node):
    pass


class Literal(Node):
    def __init__(self, val):
        self.val = val

    def ex(self, ctx):
        return self.val

    def __unicode__(self):
        return u'<{} at 0x{}> val:{!r}'.format(
            self.__class__.__name__,
            id(self),
            self.val,
        )

    def ast_prop(self):
        return {
            'val': self.val,
        }


class LiteralString(Literal):
    pass

class LiteralRegex(Literal):
    def __init__(self, pat, flags):
        raise NotImplementedError('LiteralRegex not ready for use')

        self.pat, self.flags = pat, flags
        self.val = '/{}/{}'.format(re.escape(pat), flags)   # for .ast_prop() & __unicode__

    def ex(self, ctx):
        return re.compile(self.pat, self.flags)

class LiteralNumber(Literal):
    def ex(self, ctx):
        return float(self.val) if ('.' in self.val) else int(self.val)

class LiteralTrue(Literal):
    val = True
    def __init__(self):
        pass

class LiteralFalse(Literal):
    val = False
    def __init__(self):
        pass

class LiteralNull(Literal):
    val = None
    def __init__(self):
        pass


class UnaryExp(Exp):
    def __init__(self, op, exp):
        self.op, self.exp = op, exp

    def __unicode__(self):
        return u'<{} at 0x{}>\n\top:{!r}\n\texp:{!r}'.format(
            self.__class__.__name__,
            id(self),
            self.op,
            self.exp,
        )

    def ast_prop(self):
        return {
            '$op': unicode(self.op),
            'exp': self.exp.ast(),
        }

    def ex(self, ctx):
        val = self.exp.ex(ctx)

        return self.ex_op(self.op, val)

    def ex_op(self, op, val):
        if op == UnaryOp.HASH:
            return len(val)
        elif op == UnaryOp.MINUS:
            return -val
        elif op == UnaryOp.NOT:
            return not val
        elif op == UnaryOp.PLUS:
            return +val
        else:
            raise RuntimeError('Unknow op "{}"'.format(op))

class BinaryExp(Node):
    def __init__(self, op, l, r):
        self.l, self.r, self.op = l, r, op
        print('rel op: {}'.format(op))

    def ex(self, ctx):
        l, r = self.l.ex(ctx), self.r.ex(ctx)

        return self.ex_op(self.op, l, r)

    def ex_op(self, op, l, r):
        if op == BinaryOp.LE:
            return l <= r
        elif op == BinaryOp.LT:
            return l < r
        elif op == BinaryOp.GE:
            return l >= r
        elif op == BinaryOp.GT:
            return l > r
        elif op == BinaryOp.IN:
            return l in r
        elif op == BinaryOp.NOTIN:
            return l not in r
        else:
            raise RuntimeError('Unknow op "{}"'.format(op))

    def __unicode__(self):
        # TODO: improve this output
        return u'<{} at 0x{}>\n\top:{!r}\n\tl:{!r}\n\tr:{!r}'.format(
            self.__class__.__name__,
            id(self),
            self.op,
            self.l,
            self.r,
        )

    def ast_prop(self):
        return {
            '$op': unicode(self.op),
            'l': self.l.ast(),
            'r': self.r.ast(),
        }


class EqExp(BinaryExp):
    def ex_op(self, op, l, r):
        if op == EqOp.EQ:
            return l == r
        elif op == EqOp.NE:
            return l != r
        elif op == EqOp.RE:
            return bool(re.search(r, l))
        elif op == EqOp.NR:
            return not re.search(r, l)
        elif op == EqOp.ISA:
            # TODO: r maybe string type
            return isinstance(l, r)
        elif op == EqOp.IS:
            return l is r
        elif op == EqOp.ISNOT:
            return l is not r
        else:
            raise RuntimeError('Unknow op "{}"'.format(op))


class LogicOrExp(BinaryExp):
    def ex(self, ctx):
        return self.l.ex(ctx) or self.r.ex(ctx)


class LogicAndExp(BinaryExp):
    def ex(self, ctx):
        return self.l.ex(ctx) and self.r.ex(ctx)


class CondExp(Node):
    def __init__(self, cond, yes, no):
        self.cond, self.yes, self.no = cond, yes, no

    def ex(self, ctx):
        if self.cond.ex(ctx):
            return self.yes.ex(ctx)
        else:
            return self.no.ex(ctx)

    def __unicode__(self):
        # TODO: improve this output
        return u'<{} at 0x{}>\n\tc:{!r}\n\tyes:{!r}\n\tno:{!r}'.format(
            self.__class__.__name__,
            id(self),
            self.cond,
            self.yes,
            self.yes,
        )

    def ast_prop(self):
        return {
            'cond': self.cond.ast(),
            'true': self.yes.ast(),
            'false': self.no.ast(),
        }


# }}} Syntax


# Semantic/parser/ast builder {{{
def make_binary_exp_process_fn(node_cls):
    def fn(self, ast):
        # print('exp for {}:{!r}'.format(node_cls.__name__, ast))
        l = ast.l

        if ast.op_and_r:
            for op, r in ast.op_and_r:
                l = node_cls(op, l, r)

        return l

    return fn


class YepSemantics(object):
    def __init__(self):
        pass

    def conditional_expression(self, ast):
        if not ast.val:
            return ast.cond

        return CondExp(ast.cond, ast.yes, ast.no)

    logical_or_expression = make_binary_exp_process_fn(LogicOrExp)
    logical_and_expression = make_binary_exp_process_fn(LogicAndExp)
    equality_expression = make_binary_exp_process_fn(EqExp)
    relational_expression = make_binary_exp_process_fn(BinaryExp)

    @staticmethod
    def _merge_ast(ast, sep=''):
        return sep.join(ast) if isinstance(ast, list) else ast

    def OP_BINARY(self, ast):
        # print('OP_BINARY:{!r}'.format(ast))
        ast = self._merge_ast(ast, sep=' ')
        return BinaryOp.parse(ast)

    def OP_OR(self, ast):
        # print('OP_OR:{!r}'.format(ast))
        ast = self._merge_ast(ast, sep=' ')
        return LogicOp.parse(ast)

    def OP_AND(self, ast):
        # print('OP_AND:{!r}'.format(ast))
        ast = self._merge_ast(ast, sep=' ')
        return LogicOp.parse(ast)

    def OP_EQ(self, ast):
        ast = self._merge_ast(ast, sep=' ')
        return EqOp.parse(ast)

    def OP_UNARY(self, ast):
        ast = self._merge_ast(ast)
        return UnaryOp.parse(ast)

    def unary_expression(self, ast):
        # print('unary_expression:{!r}'.format(ast))
        if ast.exp:
            return ast.exp
        return UnaryExp(op=ast.op, exp=ast.op_exp)

    def simple_string(self, ast):
        # rint('simple string:{!r}'.format(ast))
        return LiteralString(ast)

    def quoted_string(self, ast):
        # print('q string:{!r}'.format(ast))
        return LiteralString(ast)

    def number(self, ast):
        # print('number:{!r}'.format(ast))
        return LiteralNumber(ast)

# }}} Semantic
