# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2015 Daniel Miller <millerdev@gmail.com>
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
import re
from functools import partial

import Foundation as fn

import editxt.platform.mac.text as mod
from editxt.test.util import assert_raises, eq_, gentest, TestConfig


def test_Text_len():
    def test(string, length, pylen=None):
        eq_(len(mod.Text(string)), length, string)
        eq_(len(string), length if pylen is None else pylen, string)

    yield test, 'a', 1
    yield test, 'ab', 2
    yield test, '\u00e9', 1
    yield test, 'e\u0301', 2
    yield test, '\U0001f612', 2, 1


def test_Text_getitem():
    def test(rng, expect):
        with assert_raises(expect if not isinstance(expect, str) else None):
            if callable(rng):
                result = rng(text)
            else:
                result = text[rng]
        if isinstance(expect, str):
            eq_(result, expect)

    text = mod.Text("the quick brown fox")
    yield test, 0, 't'
    yield test, 1, 'h'
    yield test, 18, 'x'
    yield test, 19, IndexError

    yield test, (lambda s: s[:3]), "the"
    yield test, (lambda s: s[0:3]), "the"
    yield test, (lambda s: s[-3:]), "fox"
    yield test, (lambda s: s[-3:-1]), "fo"

    yield test, (0, 0), ""
    yield test, (0, 3), "the"
    yield test, (1, 3), "he "
    yield test, (16, 3), "fox"

    Range = fn.NSMakeRange
    yield test, Range(0, 0), ""
    yield test, Range(0, 3), "the"
    yield test, Range(1, 3), "he "
    yield test, Range(16, 3), "fox"

    text = mod.Text("lol \U0001f612 awe\u0301 \U0001f34c")
    yield test, (0, 3), 'lol'
    #yield test, (4, 1), '?'
    yield test, (4, 2), '\U0001f612'
    #yield test, (5, 1), '?'
    yield test, 10, '\u0301'
    #yield test, 12, '?'
    yield test, (12, 2), '\U0001f34c'


def test_Text_search():
    text = mod.Text("WATCHOUT! \U0001f34c don't slip eee\u0301e")
    def test(pattern, expect_span, *args):
        match = text.search(re.compile(pattern), *args)
        print(repr(match))
        eq_(text[match.range()], match[0])
        eq_(match.span(), expect_span)

    yield test, r"AT", (1, 3)
    yield test, r" . ", (9, 13)
    yield test, r"e*.e", (25, 29), 25
    yield test, r"o", (14, 15), 10, 15

    text = mod.Text("plain text")
    yield test, r"xt", (8, 10)
    assert text._surrogates is None, text._surrogates


def test_Text_finditer():
    text = mod.Text("lol \U0001f612 \U0001f34c slipping awe\u0301 \U0001f34c")
    def test(pattern, expect_spans, *args):
        spans = []
        texts = []
        matches = []
        for match in text.finditer(re.compile(pattern), *args):
            print(repr(match))
            span = match.span()
            spans.append(span)
            texts.append(text[span[0]:span[1]])
            matches.append(match[0])
        eq_(texts, matches)
        eq_(spans, expect_spans)

    yield test, r" [^ ]+", [(3, 6), (6, 9), (9, 18), (18, 23), (23, 26)]
    yield test, r" .(?= |$)", [(6, 9), (23, 26)], 4
    yield test, r" .(?= |$)", [(6, 9)], 4, 9


def test_composed_length():
    def test(text, length, enumerate=False):
        string = str(mod.Text(text))
        eq_(mod.composed_length(string, enumerate), length)

    yield test, '\u00e9', 1
    yield test, 'e\u0301', 1
    yield test, 'e\u0301 e\u0301', 3
    yield test, '\U0001f612', 1

    # TODO find an example where enumerate produces a different result
    yield test, '\u00e9', 1, True
    yield test, 'e\u0301', 1, True
    yield test, 'e\u0301 e\u0301', 3, True
    yield test, '\U0001f612', 1, True
