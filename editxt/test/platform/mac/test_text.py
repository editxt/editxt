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
    TEXT = "the quick brown fox"
    def test(rng, expect, string=TEXT):
        text = mod.Text(string)
        with assert_raises(expect if not isinstance(expect, str) else None):
            if callable(rng):
                result = rng(text)
            else:
                result = text[rng]
        if isinstance(expect, str):
            eq_(result, expect)

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

    # TODO test unicode
#    yield test, 'ab', 2
#    yield test, '\u00e9', 1
#    yield test, 'e\u0301', 2
#    yield test, '\U0001f612', 2, 1


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
