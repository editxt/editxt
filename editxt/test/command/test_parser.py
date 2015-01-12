# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2013 Daniel Miller <millerdev@gmail.com>
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
import os
import re
from functools import partial
from os.path import isabs, join

from mocker import Mocker, expect, ANY, MATCH
from nose.tools import eq_
from editxt.test.util import assert_raises, gentest, replattr, TestConfig

import editxt.command.parser as mod
from editxt.command.parser import (Arg, Choice, Int, String, Regex, RegexPattern,
    File, CommandParser, SubArgs, SubParser, VarArgs, CompleteWord, Conditional,
    identifier, Options, Error, ArgumentError, ParseError)

log = logging.getLogger(__name__)


class ColonString(String):
    def get_completions(self, arg):
        if arg:
            start = str(arg).rfind(":")
            if start < 0:
                start = len(arg)
                begin = ""
            else:
                begin = str(arg)[start:]
            return [CompleteWord(v, start=start)
                    for v in [":abc", ":def"]
                    if v.startswith(begin)]
        return []


yesno = Choice(('yes', True), ('no', False))
arg_parser = CommandParser(yesno)

def test_CommandParser():
    def test_parser(argstr, options, parser):
        if isinstance(options, Exception):
            def check(err):
                eq_(type(err), type(options))
                eq_(str(err), str(options))
                eq_(err.errors, options.errors)
                eq_(err.parse_index, options.parse_index)
            with assert_raises(type(options), msg=check):
                parser.parse(argstr)
        else:
            opts = parser.default_options()
            opts.__dict__.update(options)
            eq_(parser.parse(argstr), opts)

    test = partial(test_parser, parser=CommandParser(yesno))
    yield test, "", Options(yes=True)
    yield test, "no", Options(yes=False)

    manual = SubArgs("manual",
                Int("bass", default=50),
                Int("treble", default=50))
    preset = SubArgs("preset",
                Choice("flat", "rock", "cinema", name="value"))
    level = Choice(
        ("off", 0),
        ('high', 4),
        ("medium", 2),
        ('low', 1),
        name="level"
    )
    radio_parser = CommandParser(
        SubParser("equalizer",
            manual,
            preset,
        ),
        level,
        Int("volume", default=50), #, min=0, max=100),
        String("name"),
    )
    test = partial(test_parser, parser=radio_parser)
    yield test, "manual", Options(equalizer=(manual, Options(bass=50, treble=50)))
    yield test, "", Options()
    yield test, "preset rock low", Options(
        level=1, equalizer=(preset, Options(value="rock")))
    yield test, "  high", Options(level=0, name="high")
    yield test, " high", Options(level=4)
    yield test, "high", Options(level=4)
    yield test, "hi", Options(level=4)
    yield test, "high '' yes", ArgumentError('unexpected argument(s): yes', ..., [], 8)

    def test_placeholder(argstr, expected, parser=radio_parser):
        eq_(parser.get_placeholder(argstr), expected)
    test = test_placeholder
    yield test, "", "equalizer ... off 50 name"
    yield test, "  ", "50 name"
    yield test, "  5", " name"
    yield test, "  5 ", "name"
    yield test, "  high", ""
    yield test, " hi", "gh 50 name"
    yield test, " high", " 50 name"
    yield test, "hi", "gh 50 name"
    yield test, "high ", "50 name"

    def check_completions(argstr, expected, start=None, parser=radio_parser):
        words = parser.get_completions(argstr)
        eq_(words, expected)
        if start is not None:
            eq_([w.start for w in words], [start] * len(words), words)
    test = check_completions
    yield test, "", ['manual', 'preset'], 0
    yield test, "  ", []
    yield test, "  5", []
    yield test, "  5 ", []
    yield test, "  high", []
    yield test, " ", ["off", "high", "medium", "low"], 1
    yield test, " hi", ["high"], 1

    parser = CommandParser(
        Int("num", default=0),
        VarArgs("value", ColonString("value")),
    )
    test = partial(check_completions, parser=parser)
    yield test, "", []
    yield test, "abc", [":abc", ":def"], 3
    yield test, " abc", [":abc", ":def"], 4
    yield test, " abc:def:ghi def:a", [":abc"], 16

    parser = CommandParser(
        level, Int("value"), Choice("highlander", "tundra", "4runner"))
    test = partial(check_completions, parser=parser)
    yield test, "h", ["high"], 0
    yield test, "t", ["tundra"], 0
    yield test, "high", ["high"], 0
    yield test, "high ", []
    yield test, "high 4", []
    yield test, "high x", []
    yield test, "high  4", ["4runner"], 6

def test_CommandParser_empty():
    eq_(arg_parser.parse(''), Options(yes=True))

def test_CommandParser_too_many_args():
    with assert_raises(ArgumentError, msg="unexpected argument(s): unexpected"):
        arg_parser.parse('yes unexpected')

def test_CommandParser_incomplete():
    field = Choice('arg', 'all')
    parser = CommandParser(field)
    def check(err):
        eq_(err.options, Options(arg=Arg(field, 'a', 0, Options())))
        eq_(err.errors, [ParseError("'a' is ambiguous: arg, all", Choice('arg', 'all'), 0, 2)])
    with assert_raises(ArgumentError, msg=check):
        parser.parse('a')

def test_CommandParser_arg_string():
    parser = CommandParser(yesno, Choice('arg', 'all'))
    def test(options, argstr):
        if isinstance(argstr, Exception):
            def check(err):
                eq_(err, argstr)
            with assert_raises(type(argstr), msg=check):
                parser.arg_string(options)
        else:
            result = parser.arg_string(options)
            eq_(result, argstr)
    yield test, Options(yes=True, arg="arg"), ""
    yield test, Options(yes=False, arg="arg"), "no"
    yield test, Options(yes=True, arg="all"), " all"
    yield test, Options(yes=False, arg="all"), "no all"
    yield test, Options(), Error("missing option: yes")
    yield test, Options(yes=True), Error("missing option: arg")
    yield test, Options(yes=None), Error("invalid value: yes=None")

def test_CommandParser_with_SubParser():
    sub = SubArgs("num", Int("n"), abc="xyz")
    arg = SubParser("var", sub)
    parser = CommandParser(arg, yesno)

    def test(text, result):
        eq_(parser.get_placeholder(text), result)
    yield test, "", "var ... yes"
    yield test, " ", "yes"
    yield test, "  ", ""
    yield test, "n", "um n yes"
    yield test, "n ", "n yes"
    yield test, "num ", "n yes"
    yield test, "num  ", "yes"

    def test(text, expect, start=None):
        result = parser.get_completions(text)
        eq_(result, expect)
        if start is not None:
            eq_([w.start for w in result], [start] * len(expect), result)
    yield test, "", ["num"]
    yield test, " ", ["yes", "no"]
    yield test, "  ", []
    yield test, "n", ["num"]
    yield test, "n ", []
    yield test, "num ", []
    yield test, "num  ", ["yes", "no"]

    cat = SubArgs("cat", yesno)
    arg = SubParser("var", cat)
    parser = CommandParser(yesno, arg)
    yield test, "y", ["yes"], 0
    yield test, " cat ", ["yes", "no"], 5

    cat = SubArgs("cat", Choice("siamese", "simple"), yesno)
    arg = SubParser("var", cat)
    parser = CommandParser(arg)
    yield test, "", ["cat"], 0
    yield test, "cat si", ["siamese", "simple"], 4

def test_CommandParser_with_SubParser_errors():
    sub = SubArgs("num", Int("num"), abc="xyz")
    arg = SubParser("var", sub)
    parser = CommandParser(arg)
    def check(err):
        arg = Arg(None, 'num x', 0, Options())
        eq_(str(err), "invalid arguments: num x\n"
                      "invalid literal for int() with base 10: 'x'")
        eq_(err.options, Options(var=arg))
        eq_(err.errors,
            [ParseError("invalid literal for int() with base 10: 'x'",
                        Int("num"), 4, 5)])
    with assert_raises(ArgumentError, msg=check):
        parser.parse('num x')

def test_CommandParser_with_Conditional():
    def not_off(arg):
        return arg.args.level.value != 0
    parser = CommandParser(
        Choice(
            ("off", 0),
            ('high', 4),
            ("medium", 2),
            ('low', 1),
            name="level"
        ),
        Conditional(not_off, yesno),
    )

    def test(text, result):
        eq_(parser.get_placeholder(text), result)
    yield test, "", "off"
    yield test, " ", ""
    yield test, "  ", ""
    yield test, "h", "igh yes"
    yield test, "h ", "yes"
    yield test, "lo", "w yes"
    yield test, "lo ", "yes"
    yield test, "num ", ""
    yield test, "num  ", ""

    def test(text, result):
        eq_(parser.get_completions(text), result)
    yield test, "", ["off", "high", "medium", "low"]
    yield test, " ", []
    yield test, "  ", []
    yield test, "h", ["high"]
    yield test, "h ", ["yes", "no"]
    yield test, "lo", ["low"]
    yield test, "lo ", ["yes", "no"]
    yield test, "num ", []
    yield test, "num  ", []

    def test(text, args):
        eq_(parser.parse(text), args)
    yield test, "", Options(level=0, yes=True)
    yield test, " ", Options(level=0, yes=True)
    yield test, "h", Options(level=4, yes=True)
    yield test, "h ", Options(level=4, yes=True)
    yield test, "h n", Options(level=4, yes=False)
    yield test, "lo", Options(level=1, yes=True)

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
    yield test, 'rev', tt
    yield test, 'sel', Options(selection=True, reverse=False)
    yield test, 'r', tt
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

def test_Arg():
    opts = Options()
    @gentest
    def test(arg, strval):
        eq_(str(arg), strval)
    yield test(mod.Arg(yesno, '', 0, opts), '')
    yield test(mod.Arg(yesno, ' ', 0, opts), '')
    yield test(mod.Arg(yesno, ' xyz', 0, opts), '')
    yield test(mod.Arg(yesno, 'y', 0, opts), 'y')
    yield test(mod.Arg(yesno, 'yes', 0, opts), 'yes')
    yield test(mod.Arg(yesno, 'yes ', 0, opts), 'yes')
    yield test(mod.Arg(yesno, ' yes ', 0, opts), '')

    string = String('str')
    yield test(mod.Arg(string, '', 0, opts), '')
    yield test(mod.Arg(string, '" " ', 0, opts), '" "')
    yield test(mod.Arg(string, '\\ ', 0, opts), '\\ ')
    yield test(mod.Arg(string, ' \\ ', 0, opts), '')
    yield test(mod.Arg(string, '  \\ ', 0, opts), '')

def test_identifier():
    def test(name, ident):
        eq_(identifier(name), ident)
    yield test, "arg", "arg"
    yield test, "arg_ument", "arg_ument"
    yield test, "arg-ument", "arg_ument"

def test_Choice():
    field = Choice('arg-ument', 'nope', 'nah')
    eq_(str(field), 'arg-ument')
    eq_(field.name, 'arg_ument')

    test = make_consume_checker(field)
    yield test, 'arg-ument', 0, ("arg-ument", 10)
    yield test, 'arg', 0, ("arg-ument", 4)
    yield test, 'a', 0, ("arg-ument", 2)
    yield test, 'a', 1, ("arg-ument", 2)
    yield test, '', 0, ("arg-ument", 1)
    yield test, '', 3, ("arg-ument", 3)
    yield test, 'arg arg', 0, ("arg-ument", 4)
    yield test, 'nope', 0, ("nope", 5)
    yield test, 'nop', 0, ("nope", 4)
    yield test, 'no', 0, ("nope", 3)
    yield test, 'nah', 0, ("nah", 4)
    yield test, 'na', 0, ("nah", 3)

    test = make_arg_string_checker(field)
    yield test, "arg-ument", ""
    yield test, "nope", "nope"
    yield test, "nah", "nah"
    yield test, "arg", Error("invalid value: arg_ument='arg'")

    field = Choice(('arg-ument', True), ('nope', False), ('nah', ""))
    test = make_consume_checker(field)
    yield test, 'arg-ument', 0, (True, 10)
    yield test, 'arg', 0, (True, 4)
    yield test, 'a', 0, (True, 2)
    yield test, 'a', 1, (True, 2)
    yield test, '', 0, (True, 1)
    yield test, '', 3, (True, 3)
    yield test, 'arg arg', 0, (True, 4)
    yield test, 'nope', 0, (False, 5)
    yield test, 'nop', 0, (False, 4)
    yield test, 'no', 0, (False, 3)
    yield test, 'nah', 0, ("", 4)
    yield test, 'na', 0, ("", 3)
# TODO pass arg instead of field to errors
    yield test, 'n', 0, \
        ParseError("'n' is ambiguous: nope, nah", field, 0, 2)
    yield test, 'arg', 1, \
        ParseError("'rg' does not match any of: arg-ument, nope, nah", field, 1, 3)
    yield test, 'args', 0, \
        ParseError("'args' does not match any of: arg-ument, nope, nah", field, 0, 4)
    yield test, 'args arg', 0, \
        ParseError("'args' does not match any of: arg-ument, nope, nah", field, 0, 4)

    test = make_placeholder_checker(field)
    yield test, '', 0, "arg-ument"
    yield test, 'a', 0, "rg-ument"
    yield test, 'n', 0, "..."

    field = Choice("argument parameter", "find search")
    test = make_consume_checker(field)
    yield test, 'a', 0, ("argument", 2)
    yield test, 'arg', 0, ("argument", 4)
    yield test, 'argument', 0, ("argument", 9)
    yield test, 'p', 0, ("argument", 2)
    yield test, 'param', 0, ("argument", 6)
    yield test, 'parameter', 0, ("argument", 10)
    yield test, 'f', 0, ("find", 2)
    yield test, 'find', 0, ("find", 5)
    yield test, 's', 0, ("find", 2)
    yield test, 'search', 0, ("find", 7)
    yield test, 'arg-ument', 0, \
        ParseError("'arg-ument' does not match any of: argument, find", field, 0, 9)

    field = Choice(("argument parameter", True), ("find search", False))
    test = make_consume_checker(field)
    yield test, 'a', 0, (True, 2)
    yield test, 'arg', 0, (True, 4)
    yield test, 'argument', 0, (True, 9)
    yield test, 'p', 0, (True, 2)
    yield test, 'param', 0, (True, 6)
    yield test, 'parameter', 0, (True, 10)
    yield test, 'f', 0, (False, 2)
    yield test, 'find', 0, (False, 5)
    yield test, 's', 0, (False, 2)
    yield test, 'search', 0, (False, 7)
    yield test, 'arg-ument', 0, \
        ParseError("'arg-ument' does not match any of: argument, find", field, 0, 9)

def test_Choice_default_first():
    field = Choice(('true on', True), ('false off', False))
    eq_(str(field), 'true')
    eq_(field.name, 'true')
    eq_(repr(field), "Choice(('true on', True), ('false off', False))")

    test = make_consume_checker(field)
    yield test, '', 0, (True, 1)
    yield test, 't', 0, (True, 2)
    yield test, 'true', 0, (True, 5)
    yield test, 'false', 0, (False, 6)
    yield test, 'f', 0, (False, 2)
    yield test, 'True', 0, \
        ParseError("'True' does not match any of: true, false", field, 0, 4)
    yield test, 'False', 0, \
        ParseError("'False' does not match any of: true, false", field, 0, 5)

    test = make_placeholder_checker(field)
    yield test, '', 0, "true"
    yield test, 't', 0, "rue"
    yield test, 'true', 0, ""
    yield test, 'false', 0, ""
    yield test, 'f', 0, "alse"
    yield test, 'o', 0, "..."
    yield test, 'on', 0, ""
    yield test, 'of', 0, "f"

def test_Choice_strings():
    field = Choice('maybe yes no', name='yes')
    eq_(str(field), 'maybe')
    eq_(field.name, 'yes')
    eq_(repr(field), "Choice('maybe yes no', name='yes')")

def test_Choice_repr():
    def test(rep, args):
        eq_(repr(Choice(*args[0], **args[1])), rep)
    yield test, "Choice('arg-ument no')", Args('arg-ument no')
    yield test, "Choice('arg-ument', 'no')", Args('arg-ument', 'no')
    yield test, "Choice('y', 'n', name='abc')", Args('y', 'n', name='abc')

def test_Int():
    field = Int('num')
    eq_(str(field), 'num')
    eq_(repr(field), "Int('num')")

    test = make_consume_checker(field)
    yield test, '', 0, (None, 1)
    yield test, '3', 0, (3, 2)
    yield test, '42', 0, (42, 3)
    yield test, '100 99', 0, (100, 4)
    yield test, '1077 ', 1, (77, 5)
    yield test, 'a 99', 0, \
        ParseError("invalid literal for int() with base 10: 'a'", field, 0, 1)

    test = make_arg_string_checker(field)
    yield test, 42, "42"
    yield test, -42, "-42"
    yield test, None, ""
    yield test, "arg", Error("invalid value: num='arg'")

def test_Float():
    field = mod.Float('num')
    eq_(str(field), 'num')
    eq_(repr(field), "Float('num')")

    test = make_consume_checker(field)
    yield test, '', 0, (None, 1)
    yield test, '3', 0, (3.0, 2)
    yield test, '3.', 0, (3.0, 3)
    yield test, '3.1', 0, (3.1, 4)
    yield test, '42', 0, (42.0, 3)
    yield test, '1.2 99', 0, (1.2, 4)
    yield test, '10.7 ', 1, (0.7, 5)
    yield test, 'a 99', 0, \
        ParseError("could not convert string to float: 'a'", field, 0, 1)

    test = make_arg_string_checker(field)
    yield test, 42.0, "42.0"
    yield test, -42.0, "-42.0"
    yield test, None, ""
    yield test, "arg", Error("invalid value: num='arg'")

def test_String():
    field = String('str')
    eq_(str(field), 'str')
    eq_(repr(field), "String('str')")

    test = make_consume_checker(field)
    yield test, '', 0, (None, 0)
    yield test, 'a', 0, ('a', 2)
    yield test, 'abc', 0, ('abc', 4)
    yield test, 'abc def', 0, ('abc', 4)
    yield test, 'abc', 1, ('bc', 4)
    yield test, 'a"c', 0, ('a"c', 4)
    yield test, '\\"c', 0, ('"c', 4)
    yield test, 'a\\ c', 0, ('a c', 5)
    yield test, '"a c"', 0, ('a c', 5)
    yield test, "'a c'", 0, ('a c', 5)
    yield test, "'a c' ", 0, ('a c', 6)
    yield test, "'a c", 0, ParseError("unterminated string: 'a c", field, 0, 4)
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
    yield test, '\\', 0, ParseError("unterminated string: \\", field, 0, 1)
    yield test, '\\\\', 0, ("\\", 3)
    yield test, '\\\\\\', 0, ParseError("unterminated string: \\\\\\", field, 0, 3)
    yield test, '\\\\\\\\', 0, ("\\\\", 5)
    yield test, '""', 0, ("", 2)
    yield test, '"\\"', 0, ParseError('unterminated string: "\\"', field, 0, 3)
    yield test, '"\\\\"', 0, ("\\", 4)
    yield test, '"\\\\\\"', 0, ParseError('unterminated string: "\\\\\\"', field, 0, 5)
    yield test, '"\\\\\\\\"', 0, ("\\\\", 6)

    test = make_arg_string_checker(field)
    yield test, "str", "str"
    yield test, "a b", '"a b"', 5
    yield test, "a 'b", '''"a 'b"''', 6
    yield test, 'a "b', """'a "b'""", 6
    yield test, """a"'b""", """a"'b"""
    yield test, """a "'b""", '''"a \\"'b"''', 8
    yield test, "'ab", '''"'ab"''', 5
    yield test, '"ab', """'"ab'""", 5
    yield test, "ab'", "ab'"
    yield test, 'ab"', 'ab"'
    yield test, "\u0168", "\u0168"
    yield test, '\u0168" \u0168', """'\u0168" \u0168'""", 6
    yield test, "\u0168' \u0168", '''"\u0168' \u0168"''', 6
    for char, esc in String.ESCAPES.items():
        if char not in "\"\\'":
            yield test, esc, "\\" + char
    yield test, "\\x", "\\\\x"
    yield test, "\\", '\\\\'
    yield test, "\\\\", '\\\\\\\\'
    yield test, "\\\\\\", '\\\\\\\\\\\\'
    yield test, None, "", 0
    yield test, 5, Error("invalid value: str=5")

def test_File():
    from editxt.test.util import test_app
    field = File('path')
    eq_(str(field), 'path')
    eq_(repr(field), "File('path')")

    with test_app("project(/dir) editor") as app:
        tmp = test_app(app).tmp
        os.mkdir(join(tmp, "dir"))
        for path in [
            "dir/a.txt",
            "dir/b.txt",
            "dir/B file",
            ".hidden",
            "file.txt",
            "file.doc",
            #"x y",
        ]:
            assert not isabs(path), path
            with open(join(tmp, path), "w") as fh:
                pass

        test = make_consume_checker(field)
        yield test, "relative.txt", 0, Error("cannot make absolute path (no context): relative.txt")

        test = make_completions_checker(field)
        yield test, "", []

        editor = app.windows[0].projects[0].editors[0]
        field = field.with_context(editor)

        test = make_arg_string_checker(field)
        yield test, "/str", "/str"
        yield test, "/a b", '"/a b"', 6
        yield test, os.path.expanduser("~/a b"), '"~/a b"', 7
        yield test, join(tmp, "dir/file"), "file"
        yield test, join(tmp, "dir/a b"), '"a b"', 5
        yield test, join(tmp, "file"), join(tmp, "file")
        yield test, "arg/", Error("not a file: path='arg/'")

        test = make_consume_checker(field)
        yield test, '', 0, (None, 0)
        yield test, 'a', 0, (join(tmp, 'dir/a'), 2)
        yield test, 'abc', 0, (join(tmp, 'dir/abc'), 4)
        yield test, 'abc ', 0, (join(tmp, 'dir/abc'), 4)
        yield test, 'file.txt', 0, (join(tmp, 'dir/file.txt'), 9)
        yield test, '../file.txt', 0, (join(tmp, 'dir/../file.txt'), 12)
        yield test, '/file.txt', 0, ('/file.txt', 10)
        yield test, '~/file.txt', 0, (os.path.expanduser('~/file.txt'), 11)
        yield test, '"ab c"', 0, (join(tmp, 'dir/ab c'), 6)
        yield test, "'ab c'", 0, (join(tmp, 'dir/ab c'), 6)
        yield test, "'ab c/'", 0, (join(tmp, 'dir/ab c/'), 7)

        # completions
        def expanduser(path):
            if path.startswith("~"):
                if len(path) == 1:
                    return tmp
                assert path.startswith("~/"), path
                return tmp + path[1:]
            return path
        def test(input, output):
            if input.startswith("/"):
                input = tmp + "/"
            with replattr(os.path, "expanduser", expanduser):
                arg = mod.Arg(field, input, 0, None)
                eq_(field.get_completions(arg), output)
        yield test, "", ["a.txt", "B\\ file", "b.txt"]
        yield test, "a", ["a.txt"]
        yield test, "a.txt", ["a.txt"]
        yield test, "b", ["B\\ file", "b.txt"]
        yield test, "B", ["B\\ file"]
        yield test, "..", ["../"]
        yield test, "../", ["dir", "file.doc", "file.txt"]
        yield test, "../.", [".hidden"]
        yield test, "../dir", ["dir/"]
        yield test, "../dir/", ["a.txt", "B\\ file", "b.txt"]
        yield test, "val", []
        yield test, "/", ["dir", "file.doc", "file.txt"]
        yield test, "~", ["~/"]
        yield test, "~/", ["dir", "file.doc", "file.txt"]

        # delimiter completion
        def test(input, output, start=0):
            arg = mod.Arg(field, input, 0, None)
            words = field.get_completions(arg)
            assert all(isinstance(w, CompleteWord) for w in words), \
                repr([w for w in words if not isinstance(w, CompleteWord)])
            eq_([w.complete() for w in words], output)
            eq_([w.start for w in words], [start] * len(words), words)
        yield test, "", ["a.txt ", "B\\ file ", "b.txt "]
        yield test, "x", []
        yield test, "..", ["../"]
        yield test, "../", ["dir/", "file.doc ", "file.txt "], 3
        yield test, "../dir", ["dir/"], 3
        yield test, "../di", ["dir/"], 3
        yield test, "~", ["~/"], None

        field = File('dir', directory=True)
        eq_(str(field), 'dir')
        eq_(repr(field), "File('dir', directory=True)")
        field = field.with_context(editor)

        test = make_consume_checker(field)
        yield test, '', 0, (None, 0)
        yield test, 'a', 0, (join(tmp, 'dir/a'), 2)
        yield test, 'abc', 0, (join(tmp, 'dir/abc'), 4)
        yield test, 'abc ', 0, (join(tmp, 'dir/abc'), 4)
        yield test, 'abc/', 0, (join(tmp, 'dir/abc/'), 5)

        test = make_completions_checker(field)
        yield test, "", [], 0
        yield test, "a", [], 0
        yield test, "..", ["../"], 0
        yield test, "../", ["dir"], 3

def test_FontFace():
    from editxt.datatypes import Font
    field = mod.FontFace('face', default="Mono Type")
    eq_(str(field), 'face')
    eq_(repr(field), "FontFace('face', default='Mono Type')")

    test = make_consume_checker(field)
    yield test, "", 0, (field.default, 0)

    test = make_completions_checker(field)
    yield test, "", ["Duo\\ Type", "Mension", "Mono\\ Type", "Courier\\ New"]

    class editor:
        font = Font("Mono Type", 10.0, False, None)
    field = field.with_context(editor)

    test = make_consume_checker(field)
    yield test, '', 0, (field.default, 0)
    yield test, 'a', 0, ParseError(
        "'a' does not match any of: Duo Type, Mension, Mono Type, Courier New",
        mod.FontFace('face', default='Mono Type'), 0, 1)
    yield test, 'c', 0, ("Courier New", 2)
    yield test, 'C', 0, ("Courier New", 2)
    yield test, 'Du', 0, ("Duo Type", 3)
    yield test, 'm', 0, ParseError(
        "'m' is ambiguous: Mension, Mono Type",
        mod.FontFace('face', default='Mono Type'), 0, 2)
    yield test, 'me', 0, ("Mension", 3)

    test = make_completions_checker(field)
    yield test, "", ["Duo\\ Type", "Mension", "Mono\\ Type", "Courier\\ New"]
    yield test, "a", []
    yield test, "m", ["Mension", "Mono\ Type"]
    yield test, "M", ["Mension", "Mono\ Type"]

    test = make_placeholder_checker(field)
    yield test, "", 0, field.default
    yield test, "a", 0, ""
    yield test, "m", 0, ""
    yield test, "mo", 0, "no Type"
    yield test, "Me", 0, "nsion"

    test = make_arg_string_checker(field)
    yield test, "Mono Type", '"Mono Type"', 11

    field = mod.FontFace('face', default=["a", "b", "c"])
    test = make_consume_checker(field)
    yield test, "", 0, (field.default, 0)

def test_Regex():
    field = Regex('regex')
    eq_(str(field), 'regex')
    eq_(repr(field), "Regex('regex')")

    def regex_test(text, start, expect, flags=0):
        if isinstance(expect, Exception):
            def check(err):
                eq_(err, expect)
            with assert_raises(type(expect), msg=check):
                field.consume(text, start)
            return
        value = field.consume(text, start)
        if expect[0] in [None, (None, None)]:
            eq_(value, expect)
            return
        expr, index = value
        if field.replace:
            (expr, replace) = expr
            got = ((expr, replace), index)
        else:
            got = (expr, index)
        eq_(got, expect)
        eq_(expr.flags, flags | re.UNICODE | re.MULTILINE)

    test = regex_test
    yield test, '', 0, (None, 1)
    yield test, '/abc/', 0, ('abc', 6)
    yield test, '/abc/ def', 0, ('abc', 6)
    yield test, '/abc/  def', 0, ('abc', 6)
    yield test, '/abc/i def', 0, ('abc', 7), re.I
    yield test, '/abc/is def', 0, ('abc', 8), re.I | re.S
    yield test, '/abc/is  def', 0, ('abc', 8), re.I | re.S
    yield test, 'abc', 0, ('abc', 4)
    yield test, '^abc$', 0, ('^abc$', 6)
    yield test, '^abc$ def', 0, ('^abc$', 6)
    yield test, '/abc/X def', 0, \
        ParseError('unknown flag: X', field, 5, 5)

    test = make_placeholder_checker(field)
    yield test, "", 0, "regex"
    yield test, "/", 0, "/"
    yield test, "//", 0, ""
    #yield test, "// ", 0, None

    test = make_arg_string_checker(field)
    yield test, RegexPattern("str"), "/str/"
    yield test, RegexPattern("str", re.I), "/str/i"
    yield test, RegexPattern("/usr/bin"), ":/usr/bin:"
    yield test, RegexPattern("/usr/bin:"), '"/usr/bin:"'
    yield test, RegexPattern(r'''//''\:""'''), r'''://''\:"":'''
    yield test, RegexPattern(r'''//''\\:""'''), r'''://''\\\:"":''', False
    yield test, RegexPattern(r'''\://''""'''), r''':\://''"":'''
    yield test, RegexPattern(r'''\\://''""'''), r''':\\\://''"":''', False
    # pedantic cases with three or more of all except ':'
    yield test, RegexPattern(r'''///'"'::"'"'''), r''':///'"'\:\:"'":''', False
    yield test, RegexPattern(r'''///'"':\\:"'"'''), r''':///'"'\:\\\:"'":''', False
    yield test, "str", Error("invalid value: regex='str'")

    field = Regex('regex', replace=True)
    eq_(repr(field), "Regex('regex', replace=True)")
    test = regex_test
    yield test, '', 0, ((None, None), 1)
    yield test, '/abc', 0, (('abc', None), 5)
    yield test, '/abc ', 0, (('abc ', None), 6)
    yield test, '/\\\\', 0, (('\\\\', None), 4)
    yield test, '/\\/', 0, (('\\/', None), 4)
    yield test, '"abc', 0, (('abc', None), 5)
    yield test, '"abc"', 0, (('abc', ''), 6)
    yield test, '"abc""', 0, (('abc', ''), 7)
    yield test, '/abc def', 0, (('abc def', None), 9)
    yield test, '/abc/def', 0, (('abc', 'def'), 9)
    yield test, '/abc/def/', 0, (('abc', 'def'), 10)
    yield test, '/abc/def/ def', 0, (('abc', 'def'), 10)
    yield test, '/abc/def/  def', 0, (('abc', 'def'), 10)
    yield test, '/abc/def/i  def', 0, (('abc', 'def'), 11), re.I
    yield test, '/abc/def/is  def', 0, (('abc', 'def'), 12), re.I | re.S
    yield test, '/(', 0, (("(", None), 3)
    yield test, 'abc', 0, \
        ParseError("invalid search pattern: 'abc'", field, 0, 0)
    yield test, 'abc def', 0, \
        ParseError("invalid search pattern: 'abc def'", field, 0, 0)
    yield test, '/abc/def/y  def', 0, \
        ParseError('unknown flag: y', field, 9, 9)
    msg = 'invalid regular expression: unbalanced parenthesis'

    test = make_placeholder_checker(field)
    yield test, "", 0, "regex"
    yield test, "/", 0, "//"
    yield test, "/x/", 0, "/"
    yield test, "/\\//", 0, "/"
    yield test, "/x//", 0, ""

    field = Regex('regex', replace=True, default=("", ""))
    test = make_placeholder_checker(field)
    yield test, "", 0, "regex"
    yield test, "/", 0, "//"
    yield test, "/x/", 0, "/"
    yield test, "/\\//", 0, "/"
    yield test, "/x//", 0, ""

    test = make_arg_string_checker(field)
    yield test, (RegexPattern("str"), 'abc'), "/str/abc/"
    yield test, (RegexPattern("str", re.I), 'abc'), "/str/abc/i"
    yield test, (RegexPattern("/usr/bin"), "abc"), ":/usr/bin:abc:"
    yield test, (RegexPattern("/usr/bin:"), ":"), '"/usr/bin:":"'
    yield test, (RegexPattern(r'''//''\:""'''), r'''/"'\:'''), r'''://''\:"":/"'\::'''
    yield test, (RegexPattern(r'''//''\:""'''), r'''/"'\\:'''), r'''://''\:"":/"'\\\::''', False
    yield test, ("str", "abc"), Error("invalid value: regex=('str', 'abc')")
    yield test, ("str", 42), Error("invalid value: regex=('str', 42)")

def test_RegexPattern():
    yield eq_, RegexPattern("a"), RegexPattern("a")
    yield eq_, RegexPattern("a", re.I), RegexPattern("a", re.I)
    yield eq_, RegexPattern("a", re.I), "a"
    yield eq_, "a", RegexPattern("a", re.I)

    def ne(a, b):
        assert a != b, "{!r} == {!r}".format(a, b)
    yield ne, RegexPattern("a", re.I), RegexPattern("b", re.I)
    yield ne, RegexPattern("a", re.I), RegexPattern("a")
    yield ne, RegexPattern("a", re.I), RegexPattern("b")
    yield ne, RegexPattern("a", re.I), "b"
    yield ne, "b", RegexPattern("a", re.I)

    def lt(a, b):
        assert a < b, "{!r} >= {!r}".format(a, b)
    yield lt, RegexPattern("a"), RegexPattern("a", re.I)

def test_VarArgs():
    field = VarArgs("var", Choice('arg', 'nope', 'nah'))
    eq_(str(field), 'arg ...')
    eq_(repr(field), "VarArgs('var', Choice('arg', 'nope', 'nah'))")

    test = make_completions_checker(field)
    yield test, "", ['arg', 'nope', 'nah']
    yield test, "a", ["arg"]
    yield test, "a ", ['arg', 'nope', 'nah']
    yield test, "b ", []
    yield test, "nah", ["nah"]
    yield test, "nah ", ['arg', 'nope', 'nah']
    yield test, "arg a", ['arg']
    yield test, "arg b", []

    test = make_placeholder_checker(field)
    yield test, "", 0, "arg ..."
    yield test, "a", 0, "rg ..."
    yield test, "a ", 0, "arg ..."
    yield test, "a ", 2, "arg ..."
    yield test, "arg", 0, " ..."
    yield test, "arg ", 0, "arg ..."
    yield test, "arg a", 0, "rg ..."
    yield test, "arg x", 0, None
    yield test, "x", 0, None
    yield test, "x ", 0, None

    test = make_consume_checker(field)
    yield test, '', 0, (['arg'], 1)
    yield test, 'x', 0, ParseError("'x' does not match any of: arg, nope, nah", field.field, 0, 1)
    yield test, 'a', 0, (['arg'], 2)
    yield test, 'a na no', 0, (['arg', 'nah', 'nope'], 8)

    test = make_arg_string_checker(field)
    yield test, ["arg"], ""
    yield test, ["nope"], "nope"
    yield test, ["nah", "arg", "nah"], 'nah  nah'

    # TODO test with string (especially unterminated string)
    #field = VarArgs("var", String("str"))

def test_SubParser():
    class is_enabled:
        def __call__(self, editor):
            return False
        def __repr__(self):
            return "is_enabled()"
    sub = SubArgs("val", Int("num"), abc="xyz")
    su2 = SubArgs("str", Choice(('yes', True), ('no', False)), abc="mno")
    su3 = SubArgs("stx", String("args"), abc="pqr")
    su4 = SubArgs("hid", String("not"), is_enabled=is_enabled())
    field = SubParser("var", sub, su2, su3, su4)
    eq_(str(field), 'var')
    eq_(repr(field),
        "SubParser('var', SubArgs('val', Int('num'), abc='xyz'), "
        "SubArgs('str', Choice(('yes', True), ('no', False)), abc='mno'), "
        "SubArgs('stx', String('args'), abc='pqr'), "
        "SubArgs('hid', String('not'), is_enabled=is_enabled()))")

    field = field.with_context(TestConfig(text_view=object))
    sub = field.args[1]
    su2 = field.args[2]

    test = make_completions_checker(field)
    yield test, "", ["str", "stx", "val"]
    yield test, "v", ["val"]
    yield test, "v ", []
    yield test, "val", ["val"]
    yield test, "val ", []
    yield test, "val v", []
    yield test, "st", ["str", "stx"]
    yield test, "str ", ["yes", "no"], 4
    yield test, "str y", ["yes"], 4

    test = make_placeholder_checker(field)
    yield test, "", 0, "var ..."
    yield test, "v", 0, "al num"
    yield test, "v ", 0, "num"
    yield test, "val", 0, " num"
    yield test, "val ", 0, "num"
    yield test, "val 1", 0, ""
    yield test, "val x", 0, ""
    yield test, "s", 0, "..."
    yield test, "s ", 0, None
    yield test, "st", 0, "..."
    yield test, "str", 0, " yes"
    yield test, "str ", 0, "yes"
    yield test, "str y", 0, "es"
    yield test, "str yes", 0, ""
    yield test, "str n", 0, "o"
    yield test, "str x", 0, ""
    yield test, "str x ", 0, ""

    test = make_consume_checker(field)
    yield test, '', 0, (None, 1)
    yield test, 'x', 0, ParseError("'x' does not match any of: str, stx, val", field, 0, 1)
    yield test, 'v 1', 0, ((sub, Options(num=1)), 4)
    yield test, 'val 1', 0, ((sub, Options(num=1)), 6)
    yield test, 'val 1 2', 0, ((sub, Options(num=1)), 6)
    yield test, 'val x 2', 0, ArgumentError("invalid arguments: val x 2",
        Options(num=Arg(None, 'x', 0, Options())), [
            ParseError("invalid literal for int() with base 10: 'x'",
                       Int("num"), 4, 5)], 4)

    test = make_arg_string_checker(field)
    yield test, (sub, Options(num=1)), "val 1"
    yield test, (su2, Options(yes=True)), "str "
    yield test, (su2, Options(yes=False)), "str no"

Args = lambda *a, **k: (a, k)

def make_consume_checker(field):
    def type_checker_test(text, start, expect):
        if isinstance(expect, Exception):
            def check(err):
                eq_(err, expect)
            with assert_raises(type(expect), msg=check):
                field.consume(text, start)
        else:
            eq_(field.consume(text, start), expect)
    return type_checker_test

def make_placeholder_checker(field):
    def test_get_placeholder(text, index, result):
        arg = mod.Arg(field, text, index, None)
        eq_(field.get_placeholder(arg), result)
    return test_get_placeholder

def make_completions_checker(field):
    def test_get_completions(input, output, start=None):
        arg = mod.Arg(field, input, 0, None)
        result = field.get_completions(arg)
        eq_(result, output)
        if start is not None:
            eq_([w.start for w in result], [start] * len(result), result)
    return test_get_completions

def make_arg_string_checker(field):
    def test_get_argstring(value, argstr, index=None):
        if isinstance(argstr, Exception):
            def check(err):
                eq_(err, argstr)
            with assert_raises(type(argstr), msg=check):
                field.arg_string(value)
        else:
            if index is not False:
                if index is None:
                    index = len(argstr) + 1
                eq_(field.consume(argstr, 0), (value, index))
            else:
                assert field.consume(argstr, 0) != (value, len(argstr))
    return test_get_argstring
