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
from editxt.test.util import assert_raises, replattr, TestConfig

from editxt.command.parser import (Choice, Int, String, Regex, RegexPattern,
    File, CommandParser, SubArgs, SubParser, VarArgs, CompleteWord,
    identifier, Options, Error, ArgumentError, ParseError)

log = logging.getLogger(__name__)


yesno = Choice(('yes', True), ('no', False))
arg_parser = CommandParser(yesno)

def test_CommandParser():
    def test_parser(argstr, options, parser):
        if isinstance(options, Exception):
            def check(err):
                eq_(err, options)
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
        String("name"), #, quoted=True),
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
    yield test, "high '' yes", ArgumentError('unexpected argument(s): yes',
        Options(volume=50, equalizer=None, name='', level=4), [], 8)

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

    def make_completions_checker(argstr, expected, parser=radio_parser):
        eq_(parser.get_completions(argstr), expected)
    test = make_completions_checker
    yield test, "", ['manual', 'preset']
    yield test, "  ", []
    yield test, "  5", []
    yield test, "  5 ", []
    yield test, "  high", []
    yield test, " ", ["off", "high", "medium", "low"]
    yield test, " hi", ["high"]

    parser = CommandParser(
        level, Int("value"), Choice("highlander", "tundra", "4runner"))
    test = partial(make_completions_checker, parser=parser)
    yield test, "h", ["high"]
    yield test, "t", ["tundra"]
    yield test, "high", ["high"]
    yield test, "high ", []
    yield test, "high 4", []
    yield test, "high x", []
    yield test, "high  4", ["4runner"]

def test_CommandParser_empty():
    eq_(arg_parser.parse(''), Options(yes=True))

def test_CommandParser_too_many_args():
    with assert_raises(ArgumentError, msg="unexpected argument(s): unexpected"):
        arg_parser.parse('yes unexpected')

def test_CommandParser_incomplete():
    parser = CommandParser(Choice('arg', 'all'))
    def check(err):
        eq_(err.options, Options(arg="arg"))
        eq_(err.errors, [ParseError("'a' is ambiguous: arg, all", Choice('arg', 'all'), 0, 1)])
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

    def test(text, result):
        eq_(parser.get_completions(text), result)
    yield test, "", ["num"]
    yield test, " ", ["yes", "no"]
    yield test, "  ", []
    yield test, "n", ["num"]
    yield test, "n ", []
    yield test, "num ", []
    yield test, "num  ", ["yes", "no"]

def test_CommandParser_with_SubParser_errors():
    sub = SubArgs("num", Int("num"), abc="xyz")
    arg = SubParser("var", sub)
    parser = CommandParser(arg)
    def check(err):
        eq_(str(err), "invalid arguments: num x\n"
                      "invalid literal for int() with base 10: 'x'")
        eq_(err.options, Options(var=None))
        eq_(err.errors,
            [ParseError("invalid literal for int() with base 10: 'x'",
                        Int("num"), 4, 5)])
    with assert_raises(ArgumentError, msg=check):
        parser.parse('num x')

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

    test = make_consume_checker(arg)
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

    test = make_arg_string_checker(arg)
    yield test, "arg-ument", ""
    yield test, "nope", "nope"
    yield test, "nah", "nah"
    yield test, "arg", Error("invalid value: arg_ument='arg'")

    arg = Choice(('arg-ument', True), ('nope', False), ('nah', ""))
    test = make_consume_checker(arg)
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

    test = make_placeholder_checker(arg)
    yield test, '', 0, ("arg-ument", 0)
    yield test, 'a', 0, ("rg-ument", 1)
    yield test, 'n', 0, ("...", 1)

    arg = Choice("argument parameter", "find search")
    test = make_consume_checker(arg)
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
    test = make_consume_checker(arg)
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
    arg = Choice(('true on', True), ('false off', False))
    eq_(str(arg), 'true')
    eq_(arg.name, 'true')
    eq_(repr(arg), "Choice(('true on', True), ('false off', False))")

    test = make_consume_checker(arg)
    yield test, '', 0, (True, 0)
    yield test, 't', 0, (True, 1)
    yield test, 'true', 0, (True, 4)
    yield test, 'false', 0, (False, 5)
    yield test, 'f', 0, (False, 1)
    yield test, 'True', 0, \
        ParseError("'True' does not match any of: true, false", arg, 0, 4)
    yield test, 'False', 0, \
        ParseError("'False' does not match any of: true, false", arg, 0, 5)

    test = make_placeholder_checker(arg)
    yield test, '', 0, ("true", 0)
    yield test, 't', 0, ("rue", 1)
    yield test, 'true', 0, ("", 4)
    yield test, 'false', 0, ("", 5)
    yield test, 'f', 0, ("alse", 1)
    yield test, 'o', 0, ("...", 1)
    yield test, 'on', 0, ("", 2)
    yield test, 'of', 0, ("f", 2)

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

    test = make_consume_checker(arg)
    yield test, '', 0, (None, 0)
    yield test, '3', 0, (3, 1)
    yield test, '42', 0, (42, 2)
    yield test, '100 99', 0, (100, 4)
    yield test, '1077 ', 1, (77, 5)
    yield test, 'a 99', 0, \
        ParseError("invalid literal for int() with base 10: 'a'", arg, 0, 2)

    test = make_arg_string_checker(arg)
    yield test, 42, "42"
    yield test, -42, "-42"
    yield test, None, ""
    yield test, "arg", Error("invalid value: num='arg'")

def test_String():
    arg = String('str')
    eq_(str(arg), 'str')
    eq_(repr(arg), "String('str')")

    test = make_consume_checker(arg)
    yield test, '', 0, (None, 0)
    yield test, 'a', 0, ('a', 1)
    yield test, 'abc', 0, ('abc', 3)
    yield test, 'abc def', 0, ('abc', 4)
    yield test, 'abc', 1, ('bc', 3)
    yield test, 'a"c', 0, ('a"c', 3)
    yield test, '\\"c', 0, ('"c', 3)
    yield test, 'a\\ c', 0, ('a c', 4)
    yield test, '"a c"', 0, ('a c', 5)
    yield test, "'a c'", 0, ('a c', 5)
    yield test, "'a c' ", 0, ('a c', 6)
    yield test, "'a c", 0, ParseError("unterminated string: 'a c", arg, 0, 4)
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
    yield test, '\\', 0, ParseError("unterminated string: \\", arg, 0, 1)
    yield test, '\\\\', 0, ("\\", 2)
    yield test, '\\\\\\', 0, ParseError("unterminated string: \\\\\\", arg, 0, 3)
    yield test, '\\\\\\\\', 0, ("\\\\", 4)
    yield test, '""', 0, ("", 2)
    yield test, '"\\"', 0, ParseError('unterminated string: "\\"', arg, 0, 3)
    yield test, '"\\\\"', 0, ("\\", 4)
    yield test, '"\\\\\\"', 0, ParseError('unterminated string: "\\\\\\"', arg, 0, 5)
    yield test, '"\\\\\\\\"', 0, ("\\\\", 6)

    test = make_arg_string_checker(arg)
    yield test, "str", "str"
    yield test, "a b", '"a b"'
    yield test, "a 'b", '''"a 'b"'''
    yield test, 'a "b', """'a "b'"""
    yield test, """a"'b""", """a"'b"""
    yield test, """a "'b""", '''"a \\"'b"'''
    yield test, "'ab", '''"'ab"'''
    yield test, '"ab', """'"ab'"""
    yield test, "ab'", "ab'"
    yield test, 'ab"', 'ab"'
    yield test, "\u0168", "\u0168"
    yield test, '\u0168" \u0168', """'\u0168" \u0168'"""
    yield test, "\u0168' \u0168", '''"\u0168' \u0168"'''
    for char, esc in String.ESCAPES.items():
        if char not in "\"\\'":
            yield test, esc, "\\" + char
    yield test, "\\x", "\\\\x"
    yield test, "\\", '\\\\'
    yield test, "\\\\", '\\\\\\\\'
    yield test, "\\\\\\", '\\\\\\\\\\\\'
    yield test, None, ""
    yield test, 5, Error("invalid value: str=5")

def test_File():
    from editxt.test.util import test_app
    arg = File('path')
    eq_(str(arg), 'path')
    eq_(repr(arg), "File('path')")

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

        test = make_consume_checker(arg)
        yield test, "relative.txt", 0, Error("cannot make absolute path (no context): relative.txt")

        test = make_completions_checker(arg)
        yield test, "", ([], 0)
        yield test, "../", (None, 0)

        textview=TestConfig(editor=app.windows[0].projects[0].editors[0])
        arg = arg.with_context(textview)

        test = make_arg_string_checker(arg)
        yield test, "/str", "/str"
        yield test, "/a b", '"/a b"'
        yield test, os.path.expanduser("~/a b"), '"~/a b"'
        yield test, join(tmp, "dir/file"), "file"
        yield test, join(tmp, "dir/a b"), '"a b"'
        yield test, join(tmp, "file"), join(tmp, "file")
        yield test, "arg/", Error("not a file: path='arg/'")

        test = make_consume_checker(arg)
        yield test, '', 0, (None, 0)
        yield test, 'a', 0, (join(tmp, 'dir/a'), 1)
        yield test, 'abc', 0, (join(tmp, 'dir/abc'), 3)
        yield test, 'abc/', 0, ParseError("not a file: abc/", arg, 0, 4)
        yield test, 'abc ', 0, (join(tmp, 'dir/abc'), 4)
        yield test, 'file.txt', 0, (join(tmp, 'dir/file.txt'), 8)
        yield test, '../file.txt', 0, (join(tmp, 'dir/../file.txt'), 11)
        yield test, '/file.txt', 0, ('/file.txt', 9)
        yield test, '~/file.txt', 0, (os.path.expanduser('~/file.txt'), 10)
        yield test, '"ab c"', 0, (join(tmp, 'dir/ab c'), 6)
        yield test, "'ab c'", 0, (join(tmp, 'dir/ab c'), 6)
        yield test, "'ab c/'", 0, ParseError("not a file: ab c/", arg, 0, 7)

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
                output = (output[0], output[1] + len(tmp))
            with replattr(os.path, "expanduser", expanduser):
                eq_(arg.parse_completions(input, 0), output)
        yield test, "", (["a.txt", "B\\ file", "b.txt"], 0)
        yield test, "a", (["a.txt"], 1)
        yield test, "a ", (None, 2)
        yield test, "a.txt", (["a.txt"], 5)
        yield test, "a.txt ", (None, 6)
        yield test, "b", (["B\\ file", "b.txt"], 1)
        yield test, "B", (["B\\ file"], 1)
        yield test, "..", (["../"], 2)
        yield test, "../", (["dir", "file.doc", "file.txt"], 3)
        yield test, "../.", ([".hidden"], 4)
        yield test, "../dir", (["dir/"], 6)
        yield test, "../dir/", (["a.txt", "B\\ file", "b.txt"], 7)
        yield test, "val", ([], 3)
        yield test, "/", (["dir", "file.doc", "file.txt"], 1)
        yield test, "~", (["~/"], 1)
        yield test, "~/", (["dir", "file.doc", "file.txt"], 2)

        # delimiter completion
        def test(input, output, overlap=None):
            words = arg.get_completions(input)
            assert all(isinstance(w, CompleteWord) for w in words), \
                repr([w for w in words if not isinstance(w, CompleteWord)])
            eq_([w.complete() for w in words], output)
            if overlap is not None:
                eq_([w.overlap for w in words], [overlap] * len(words), words)
        yield test, "", ["a.txt ", "B\\ file ", "b.txt "], 0
        yield test, "x", []
        yield test, "..", ["../"], 2
        yield test, "../", ["dir/", "file.doc ", "file.txt "], 0
        yield test, "../dir", ["dir/"], 3
        yield test, "~", ["~/"], 1

        arg = File('dir', directory=True)
        eq_(str(arg), 'dir')
        eq_(repr(arg), "File('dir', directory=True)")
        arg = arg.with_context(textview)

        test = make_completions_checker(arg)
        yield test, "", ([], 0)
        yield test, "a", ([], 1)
        yield test, "..", (["../"], 2)
        yield test, "../", (["dir"], 3)

def test_Regex():
    arg = Regex('regex')
    eq_(str(arg), 'regex')
    eq_(repr(arg), "Regex('regex')")

    def regex_test(text, start, expect, flags=0):
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
            got = ((expr, replace), index)
        else:
            got = (expr, index)
        eq_(got, expect)
        eq_(expr.flags, flags | re.UNICODE | re.MULTILINE)

    test = regex_test
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

    test = make_placeholder_checker(arg)
    yield test, "", 0, ("regex", 0)
    yield test, "/", 0, ("/", 2)
    yield test, "//", 0, ("", 2)
    yield test, "// ", 0, (None, 3)

    test = make_arg_string_checker(arg)
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

    arg = Regex('regex', replace=True)
    eq_(repr(arg), "Regex('regex', replace=True)")
    test = regex_test
    yield test, '', 0, ((None, None), 0)
    yield test, '/abc', 0, (('abc', None), 5)
    yield test, '/abc ', 0, (('abc ', None), 6)
    yield test, '/\\\\', 0, (('\\\\', None), 4)
    yield test, '/\\/', 0, (('\\/', None), 4)
    yield test, '"abc', 0, (('abc', None), 5)
    yield test, '"abc"', 0, (('abc', ''), 6)
    yield test, '"abc""', 0, (('abc', ''), 6)
    yield test, '/abc def', 0, (('abc def', None), 9)
    yield test, '/abc/def', 0, (('abc', 'def'), 9)
    yield test, '/abc/def/', 0, (('abc', 'def'), 9)
    yield test, '/abc/def/ def', 0, (('abc', 'def'), 10)
    yield test, '/abc/def/  def', 0, (('abc', 'def'), 10)
    yield test, '/abc/def/i  def', 0, (('abc', 'def'), 11), re.I
    yield test, '/abc/def/is  def', 0, (('abc', 'def'), 12), re.I | re.S
    yield test, '/(', 0, (("(", None), 3)
    yield test, 'abc', 0, \
        ParseError("invalid search pattern: 'abc'", arg, 0, 3)
    yield test, 'abc def', 0, \
        ParseError("invalid search pattern: 'abc def'", arg, 0, 7)
    yield test, '/abc/def/y  def', 0, \
        ParseError('unknown flag: y', arg, 9, 9)
    msg = 'invalid regular expression: unbalanced parenthesis'

    test = make_placeholder_checker(arg)
    yield test, "", 0, ("regex", 0)
    yield test, "/", 0, ("//", 2)
    yield test, "/x/", 0, ("/", 4)
    yield test, "/\\//", 0, ("/", 5)
    yield test, "/x//", 0, ("", 4)

    arg = Regex('regex', replace=True, default=("", ""))
    test = make_placeholder_checker(arg)
    yield test, "", 0, ("regex", 0)
    yield test, "/", 0, ("//", 2)
    yield test, "/x/", 0, ("/", 4)
    yield test, "/\\//", 0, ("/", 5)
    yield test, "/x//", 0, ("", 4)

    test = make_arg_string_checker(arg)
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
    arg = VarArgs("var", Choice('arg', 'nope', 'nah'))
    eq_(str(arg), 'arg ...')
    eq_(repr(arg), "VarArgs('var', Choice('arg', 'nope', 'nah'))")

    test = make_completions_checker(arg)
    yield test, "", (['arg', 'nope', 'nah'], 0)
    yield test, "a", (["arg"], 1)
    yield test, "a ", (['arg', 'nope', 'nah'], 2)
    yield test, "b ", (None, 0)
    yield test, "nah", (["nah"], 3)
    yield test, "nah ", (['arg', 'nope', 'nah'], 4)
    yield test, "arg a", (['arg'], 5)
    yield test, "arg b", (None, 4)

    test = make_placeholder_checker(arg)
    yield test, "", 0, ("arg ...", 0)
    yield test, "a", 0, ("rg ...", 1)
    yield test, "a ", 0, ("arg ...", 2)
    yield test, "a ", 2, ("arg ...", 2)
    yield test, "arg", 0, (" ...", 3)
    yield test, "arg ", 0, ("arg ...", 4)
    yield test, "arg a", 0, ("rg ...", 5)
    yield test, "arg x", 0, (None, 4)
    yield test, "x", 0, (None, None)
    yield test, "x ", 0, (None, None)

    test = make_consume_checker(arg)
    yield test, '', 0, (['arg'], 0)
    yield test, 'x', 0, ParseError("'x' does not match any of: arg, nope, nah", arg.field, 0, 1)
    yield test, 'a', 0, (['arg'], 1)
    yield test, 'a na no', 0, (['arg', 'nah', 'nope'], 7)

    test = make_arg_string_checker(arg)
    yield test, ["arg"], ""
    yield test, ["nope"], "nope"
    yield test, ["nah", "arg", "nah"], 'nah  nah'

    # TODO test with string (especially unterminated string)
    #arg = VarArgs("var", String("str"))

def test_SubParser():
    sub = SubArgs("val", Int("num"), abc="xyz")
    su2 = SubArgs("str", Choice(('yes', True), ('no', False)), abc="mno")
    su3 = SubArgs("stx", String("args"), abc="pqr")
    arg = SubParser("var", sub, su2, su3)
    eq_(str(arg), 'var')
    eq_(repr(arg),
        "SubParser('var', SubArgs('val', Int('num'), abc='xyz'), "
        "SubArgs('str', Choice(('yes', True), ('no', False)), abc='mno'), "
        "SubArgs('stx', String('args'), abc='pqr'))")

    test = make_completions_checker(arg)
    yield test, "", (["str", "stx", "val"], 0)
    yield test, "v", (["val"], 1)
    yield test, "v ", ([], 2)
    yield test, "val", (["val"], 3)
    yield test, "val ", ([], 4)
    yield test, "val v", (None, 4)
    yield test, "st", (["str", "stx"], 2)
    yield test, "str ", (["yes", "no"], 4)
    yield test, "str y", (["yes"], 5)

    test = make_placeholder_checker(arg)
    yield test, "", 0, ("var ...", 0)
    yield test, "v", 0, ("al num", 1)
    yield test, "v ", 0, ("num", 2)
    yield test, "val", 0, (" num", 3)
    yield test, "val ", 0, ("num", 4)
    yield test, "val 1", 0, ("", 5)
    yield test, "val x", 0, (None, None)
    yield test, "s", 0, ("...", 1)
    yield test, "s ", 0, (None, None)
    yield test, "st", 0, ("...", 2)
    yield test, "str", 0, (" yes", 3)
    yield test, "str ", 0, ("yes", 4)
    yield test, "str y", 0, ("es", 5)
    yield test, "str yes", 0, ("", 7)
    yield test, "str n", 0, ("o", 5)
    yield test, "str x", 0, (None, None)
    yield test, "str x ", 0, (None, None)

    test = make_consume_checker(arg)
    yield test, '', 0, (None, 0)
    yield test, 'x', 0, ParseError("'x' does not match any of: str, stx, val", arg, 0, 1)
    yield test, 'v 1', 0, ((sub, Options(num=1)), 3)
    yield test, 'val 1', 0, ((sub, Options(num=1)), 5)
    yield test, 'val 1 2', 0, ((sub, Options(num=1)), 6)
    yield test, 'val x 2', 0, ArgumentError("invalid arguments: val x 2",
        Options(num=None), [
            ParseError("invalid literal for int() with base 10: 'x'",
                       Int("num"), 4, 6)], 4)

    test = make_arg_string_checker(arg)
    yield test, (sub, Options(num=1)), "val 1"
    yield test, (su2, Options(yes=True)), "str "
    yield test, (su2, Options(yes=False)), "str no"

Args = lambda *a, **k: (a, k)

def make_consume_checker(arg):
    def type_checker_test(text, start, expect):
        if isinstance(expect, Exception):
            def check(err):
                eq_(err, expect)
            with assert_raises(type(expect), msg=check):
                arg.consume(text, start)
        else:
            eq_(arg.consume(text, start), expect)
    return type_checker_test

def make_placeholder_checker(arg):
    def test_get_placeholder(text, index, result):
        eq_(arg.get_placeholder(text, index), result)
    return test_get_placeholder

def make_completions_checker(arg):
    def test_parse_completions(input, output):
        eq_(arg.parse_completions(input, 0), output)
    return test_parse_completions

def make_arg_string_checker(arg, round_trip_equal=True):
    def test_get_argstring(value, argstr, round_trip_equal=round_trip_equal):
        if isinstance(argstr, Exception):
            def check(err):
                eq_(err, argstr)
            with assert_raises(type(argstr), msg=check):
                arg.arg_string(value)
        else:
            eq_(arg.arg_string(value), argstr)
            if round_trip_equal:
                eq_(arg.consume(argstr, 0), (value, len(argstr)))
            else:
                assert arg.consume(argstr, 0) != (value, len(argstr))
    return test_get_argstring
