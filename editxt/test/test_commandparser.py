# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2012 Daniel Miller <millerdev@gmail.com>
#
# This file is part of EditXT, a programmer's text editor for Mac OS X,
# which can be found at http://editxt.org/.
#
# EditXT is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# EditXT is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EditXT.  If not, see <http://www.gnu.org/licenses/>.
import logging
import re

from mocker import Mocker, expect, ANY, MATCH
from nose.tools import eq_
from editxt.test.util import assert_raises, TestConfig

from editxt.commandparser import (Choice, Int, String, Regex, CommandParser,
    identifier, Options, Error, ArgumentError, ParseError)

log = logging.getLogger(__name__)

Args = lambda *a, **k: (a, k)

def make_type_checker(arg):
    def test(text, start, expect):
        if isinstance(expect, Exception):
            def check(err):
                eq_(err, expect)
            with assert_raises(type(expect), msg=check):
                arg.consume(text, start)
        else:
            eq_(arg.consume(text, start), expect)
    return test

def test_identifier():
    def test(name, ident):
        eq_(identifier(name), ident)
    yield test, "arg", "arg"
    yield test, "arg_ument", "arg_ument"
    yield test, "arg-ument", "arg_ument"

def test_Choice():
    arg = Choice('arg-ument', 'nope', 'nah')
    eq_(str(arg), 'arg-ument')
    eq_(arg.name, 'arg_ument')

    test = make_type_checker(arg)
    yield test, 'arg-ument', 0, ("arg-ument", 9)
    yield test, 'arg', 0, ("arg-ument", 3)
    yield test, 'a', 0, ("arg-ument", 1)
    yield test, 'a', 1, ("arg-ument", 1)
    yield test, '', 0, ("arg-ument", 0)
    yield test, '', 3, ("arg-ument", 3)
    yield test, 'arg arg', 0, ("arg-ument", 4)
    yield test, 'nope', 0, ("nope", 4)
    yield test, 'nop', 0, ("nope", 3)
    yield test, 'no', 0, ("nope", 2)
    yield test, 'nah', 0, ("nah", 3)
    yield test, 'na', 0, ("nah", 2)

    arg = Choice(('arg-ument', True), ('nope', False), ('nah', ""))
    test = make_type_checker(arg)
    yield test, 'arg-ument', 0, (True, 9)
    yield test, 'arg', 0, (True, 3)
    yield test, 'a', 0, (True, 1)
    yield test, 'a', 1, (True, 1)
    yield test, '', 0, (True, 0)
    yield test, '', 3, (True, 3)
    yield test, 'arg arg', 0, (True, 4)
    yield test, 'nope', 0, (False, 4)
    yield test, 'nop', 0, (False, 3)
    yield test, 'no', 0, (False, 2)
    yield test, 'nah', 0, ("", 3)
    yield test, 'na', 0, ("", 2)
    yield test, 'n', 0, \
        ParseError("'n' is ambiguous: nope, nah", arg, 0, 1)
    yield test, 'arg', 1, \
        ParseError("'rg' does not match any of: arg-ument, nope, nah", arg, 1, 3)
    yield test, 'args', 0, \
        ParseError("'args' does not match any of: arg-ument, nope, nah", arg, 0, 4)
    yield test, 'args arg', 0, \
        ParseError("'args' does not match any of: arg-ument, nope, nah", arg, 0, 5)

    arg = Choice("argument parameter", "find search")
    test = make_type_checker(arg)
    yield test, 'a', 0, ("argument", 1)
    yield test, 'arg', 0, ("argument", 3)
    yield test, 'argument', 0, ("argument", 8)
    yield test, 'p', 0, ("argument", 1)
    yield test, 'param', 0, ("argument", 5)
    yield test, 'parameter', 0, ("argument", 9)
    yield test, 'f', 0, ("find", 1)
    yield test, 'find', 0, ("find", 4)
    yield test, 's', 0, ("find", 1)
    yield test, 'search', 0, ("find", 6)
    yield test, 'arg-ument', 0, \
        ParseError("'arg-ument' does not match any of: argument, find", arg, 0, 9)

    arg = Choice(("argument parameter", True), ("find search", False))
    test = make_type_checker(arg)
    yield test, 'a', 0, (True, 1)
    yield test, 'arg', 0, (True, 3)
    yield test, 'argument', 0, (True, 8)
    yield test, 'p', 0, (True, 1)
    yield test, 'param', 0, (True, 5)
    yield test, 'parameter', 0, (True, 9)
    yield test, 'f', 0, (False, 1)
    yield test, 'find', 0, (False, 4)
    yield test, 's', 0, (False, 1)
    yield test, 'search', 0, (False, 6)
    yield test, 'arg-ument', 0, \
        ParseError("'arg-ument' does not match any of: argument, find", arg, 0, 9)

def test_Choice_default_first():
    arg = Choice(('true', True), ('false', False))
    eq_(str(arg), 'true')
    eq_(arg.name, 'true')
    eq_(repr(arg), "Choice(('true', True), ('false', False))")

    test = make_type_checker(arg)
    yield test, '', 0, (True, 0)
    yield test, 't', 0, (True, 1)
    yield test, 'true', 0, (True, 4)
    yield test, 'false', 0, (False, 5)
    yield test, 'f', 0, (False, 1)
    yield test, 'True', 0, \
        ParseError("'True' does not match any of: true, false", arg, 0, 4)
    yield test, 'False', 0, \
        ParseError("'False' does not match any of: true, false", arg, 0, 5)

def test_Choice_strings():
    arg = Choice('maybe yes no', name='yes')
    eq_(str(arg), 'maybe')
    eq_(arg.name, 'yes')
    eq_(repr(arg), "Choice('maybe yes no', name='yes')")

def test_Choice_repr():
    def test(rep, args):
        eq_(repr(Choice(*args[0], **args[1])), rep)
    yield test, "Choice('arg-ument no')", Args('arg-ument no')
    yield test, "Choice('arg-ument', 'no')", Args('arg-ument', 'no')
    yield test, "Choice('y', 'n', name='abc')", Args('y', 'n', name='abc')

def test_Int():
    arg = Int('num')
    eq_(str(arg), 'num')
    eq_(repr(arg), "Int('num')")

    test = make_type_checker(arg)
    yield test, '', 0, (None, 0)
    yield test, '3', 0, (3, 1)
    yield test, '42', 0, (42, 2)
    yield test, '100 99', 0, (100, 4)
    yield test, '1077 ', 1, (77, 5)
    yield test, 'a 99', 0, \
        ParseError("invalid literal for int() with base 10: 'a'", arg, 0, 2)

def test_String():
    arg = String('str')
    eq_(str(arg), 'str')
    eq_(repr(arg), "String('str')")

    test = make_type_checker(arg)
    yield test, '', 0, (None, 0)
    yield test, 'a', 0, ('a', 1)
    yield test, 'abc', 0, ('abc', 3)
    yield test, 'abc def', 0, ('abc', 4)
    yield test, 'abc', 1, ('bc', 3)
    yield test, '"a c"', 0, ('a c', 5)
    yield test, "'a c'", 0, ('a c', 5)
    yield test, "'a c' ", 0, ('a c', 6)
    yield test, "'a c", 0, \
        ParseError("unterminated string: 'a c", arg, 0, 4)
    yield test, r"'a c\' '", 0, ("a c' ", 8)
    yield test, r"'a c\\' ", 0, ("a c\\", 8)
    yield test, r"'a c\"\' '", 0, ("a c\"\' ", 10)
    yield test, r"'a c\\\' '", 0, ("a c\\' ", 10)
    yield test, r"'a c\a\' '", 0, ("a c\a' ", 10)
    yield test, r"'a c\b\' '", 0, ("a c\b' ", 10)
    yield test, r"'a c\f\' '", 0, ("a c\f' ", 10)
    yield test, r"'a c\n\' '", 0, ("a c\n' ", 10)
    yield test, r"'a c\r\' '", 0, ("a c\r' ", 10)
    yield test, r"'a c\t\' '", 0, ("a c\t' ", 10)
    yield test, r"'a c\v\' '", 0, ("a c\v' ", 10)
    yield test, r"'a c\v\' ' ", 0, ("a c\v' ", 11)

def test_Regex():
    arg = Regex('regex')
    eq_(str(arg), 'regex')
    eq_(repr(arg), "Regex('regex')")

    def test(text, start, expect, flags=0):
        if isinstance(expect, Exception):
            def check(err):
                eq_(err, expect)
            with assert_raises(type(expect), msg=check):
                arg.consume(text, start)
            return
        value = arg.consume(text, start)
        if expect[0] in [None, (None, None)]:
            eq_(value, expect)
            return
        expr, index = value
        if arg.replace:
            (expr, replace) = expr
            got = ((expr.pattern, replace), index)
        else:
            got = (expr.pattern, index)
        eq_(got, expect)
        eq_(expr.flags, flags | re.UNICODE | re.MULTILINE)
    yield test, '', 0, (None, 0)
    yield test, '/abc/', 0, ('abc', 5)
    yield test, '/abc/ def', 0, ('abc', 6)
    yield test, '/abc/  def', 0, ('abc', 6)
    yield test, '/abc/i def', 0, ('abc', 7), re.I
    yield test, '/abc/is def', 0, ('abc', 8), re.I | re.S
    yield test, '/abc/is  def', 0, ('abc', 8), re.I | re.S
    yield test, 'abc', 0, \
        ParseError("invalid search pattern: 'abc'", arg, 0, 3)
        #('abc', 3)
    yield test, '^abc$', 0, \
        ParseError("invalid search pattern: '^abc$'", arg, 0, 5)
        #('^abc$', 5)
    yield test, '^abc$ def', 0, \
        ParseError("invalid search pattern: '^abc$ def'", arg, 0, 9)
        #('^abc$', 6)
    yield test, '/abc/X def', 0, \
        ParseError('unknown flag: X', arg, 5, 5)

    arg = Regex('regex', replace=True)
    eq_(repr(arg), "Regex('regex', replace=True)")
    yield test, '', 0, ((None, None), 0)
    yield test, '/abc', 0, (('abc', None), 5)
    yield test, '/abc ', 0, (('abc ', None), 6)
    yield test, ' abc', 0, (('abc', None), 5)
    yield test, ' abc ', 0, (('abc', None), 6)
    yield test, ' abc  ', 0, (('abc', ''), 6)
    yield test, '/abc def', 0, (('abc def', None), 9)
    yield test, '/abc/def', 0, (('abc', 'def'), 9)
    yield test, '/abc/def/', 0, (('abc', 'def'), 9)
    yield test, '/abc/def/ def', 0, (('abc', 'def'), 10)
    yield test, '/abc/def/  def', 0, (('abc', 'def'), 10)
    yield test, '/abc/def/i  def', 0, (('abc', 'def'), 11), re.I
    yield test, '/abc/def/is  def', 0, (('abc', 'def'), 12), re.I | re.S
    yield test, 'abc', 0, \
        ParseError("invalid search pattern: 'abc'", arg, 0, 3)
    yield test, 'abc def', 0, \
        ParseError("invalid search pattern: 'abc def'", arg, 0, 7)
    yield test, '/abc/def/y  def', 0, \
        ParseError('unknown flag: y', arg, 9, 9)

arg_parser = CommandParser(Choice(('yes', True), ('no', False)))

def test_CommandParser_empty():
    eq_(arg_parser.parse(''), Options(yes=True))

def test_CommandParser():
    eq_(arg_parser.parse('yes'), Options(yes=True))

def test_CommandParser_too_many_args():
    with assert_raises(ArgumentError, msg="unexpected argument(s): unexpected"):
        arg_parser.parse('yes unexpected')

def test_CommandParser_incomplete():
    parser = CommandParser(Choice('arg', 'all'))
    def check(err):
        eq_(err.options, Options())
        eq_(err.errors, [ParseError("'a' is ambiguous: arg, all", Choice('arg', 'all'), 0, 1)])
    print assert_raises
    with assert_raises(ArgumentError, msg=check):
        parser.parse('a')

def test_CommandParser_order():
    def test(text, result):
        if isinstance(result, Options):
            eq_(parser.parse(text), result)
        else:
            assert_raises(result, parser.parse, text)
    parser = CommandParser(
        Choice(('selection', True), ('all', False)),
        Choice(('forward', False), ('reverse', True), name='reverse'),
    )
    tt = Options(selection=True, reverse=True)
    yield test, 'selection reverse', tt
    yield test, 'sel rev', tt
    yield test, 'rev sel', ArgumentError
    yield test, 'r s', ArgumentError
    yield test, 's r', tt
    yield test, 'rev', ArgumentError
    yield test, 'sel', Options(selection=True, reverse=False)
    yield test, 'r', ArgumentError
    yield test, 's', Options(selection=True, reverse=False)

#def test_
#    CommandParser(
#        Regex('regex'),
#        Choice('bool b'),
#        Int('num'),
#    )
#    matches:
#        '/^abc$/ bool 123'
#        '/^abc$/ b 123'
#        '/^abc$/b 123'
