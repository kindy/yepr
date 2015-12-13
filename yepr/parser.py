#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

from .yep_grako import yepParser
from .nodes import YepSemantics


class Parser(object):
    def __init__(self):
        pass

    def parse(self, expr):
        parser = yepParser(parseinfo=False)
        semantics = YepSemantics()
        startrule = 'yep'

        ast = parser.parse(
            expr,
            startrule,
            filename=None,
            trace=False,
            semantics=semantics,
            whitespace=None,
        )
        # nameguard=nameguard

        return ast

    def parse_and_ex(self, expr, ctx):
        return self.parse(expr).ex(ctx)


def main(filename, startrule, trace=False, yep=False, whitespace=None, nameguard=None):
    import json
    from pprint import pprint
    with open(filename) as f:
        text = f.read()
    parser = yepParser(parseinfo=False)
    semantics = YepSemantics() if yep else None
    ast = parser.parse(
        text,
        startrule,
        filename=filename,
        trace=trace,
        semantics=semantics,
        whitespace=whitespace,
        nameguard=nameguard)

    if yep:
        print('AST:')
        print(json.dumps(ast.ast(), indent=2))
    else:
        print('AST:')
        pprint(ast)
        print()
        print('JSON:')
        print(json.dumps(ast, indent=2))

    print('Done!')


if __name__ == '__main__':
    import argparse
    import string
    import sys

    class ListRules(argparse.Action):
        def __call__(self, parser, namespace, values, option_string):
            print('Rules:')
            for r in yepParser.rule_list():
                print(r)
            print()
            sys.exit(0)

    parser = argparse.ArgumentParser(description="Simple parser for yep.")
    parser.add_argument('-l', '--list', action=ListRules, nargs=0,
                        help="list all rules and exit")
    parser.add_argument('-n', '--no-nameguard', action='store_true',
                        dest='no_nameguard',
                        help="disable the 'nameguard' feature")
    parser.add_argument('-t', '--trace', action='store_true',
                        help="output trace information")
    parser.add_argument('-E', '--use-yep', action='store_true',
                        dest='use_yep',
                        help="Use Yep Node")
    parser.add_argument('-w', '--whitespace', type=str, default=string.whitespace,
                        help="whitespace specification")
    parser.add_argument('-r', '--rule', type=str, default='yep',
                        help="the start rule for parsing")
    parser.add_argument('file', metavar="FILE", help="the input file to parse")

    args = parser.parse_args()

    main(
        args.file,
        args.rule,
        trace=args.trace,
        yep=args.use_yep,
        whitespace=args.whitespace,
        nameguard=not args.no_nameguard
    )
