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

from editxt.constants import Constant
from editxt.linenumbers import LineNumbers
from editxt.platform.text import Text

from editxt.test.util import assert_raises, eq_, gentest

END = Constant("END")

TEXT = (
    "abc\n"  # 1    0     3
    "def\n"  # 2    4     7
    "\n"     # 3    8     8
    "ghij\n" # 4    9     13
    "jkl\n"  # 5    14    17
)

def test_getitem():
    @gentest
    def test(i, line, text, preset=None):
        text = Text(text)
        lines = LineNumbers(text)
        if preset is END:
            lines[len(text) - 1]
        elif preset is not None:
            lines[preset]
        if isinstance(line, int):
            eq_(lines[i], line)
        else:
            with assert_raises(line):
                lines[i]
    base_test = test

    yield test(0, 1, "")
    yield test(0, 1, "a")
    yield test(1, IndexError, "a")
    yield test(1, 1, "ab")
    yield test(2, IndexError, "ab")
    yield test(0, 1, "abc")
    yield test(1, 1, "abc")
    yield test(2, 1, "abc")
    yield test(3, IndexError, "abc")

    def unicode_suite(text, length, breaks={}):
        eq_(len(Text(text)), length, text)
        line = 1
        for i in range(length):
            if i in breaks:
                line = breaks[i]
            yield test(i, line, text);
        yield test(length, IndexError, text);

    yield from unicode_suite("a\n", 2)
    yield from unicode_suite("\u00e9\n", 2)
    yield from unicode_suite("e\u0301\n", 3)
    yield from unicode_suite("\U0001f612\n", 3)

    for preset in [None, END] + list(range(7, 15)):
        test = partial(base_test, text=TEXT, preset=preset)
        yield test(0, 1)
        yield test(1, 1)
        yield test(2, 1)
        yield test(3, 1)
        yield test(4, 2)
        yield test(7, 2)
        yield test(8, 3)
        yield test(9, 4)
        yield test(13, 4)
        yield test(14, 5)
        yield test(17, 5)
        yield test(18, IndexError)

def test_delitem():
    @gentest
    def test(i, output, text, preset=END, start=1):
        text = Text(text)
        lines = LineNumbers(text)
        if preset is END:
            list(lines.iter_from(0))
            assert lines.end is not None
        elif preset is not None:
            lines[preset]
        del lines[i]
        eq_(lines.end, None)
        eq_(lines.newline_at_end, None)
        len_text = len(text)
        text[len_text:] = "\nend"
        if not output:
            output.append(0)
        output.append(len_text + 1)
        print(repr(text))
        eq_(list(lines.iter_from(i)), list(enumerate(output, start=start)))
    base_test = test

    yield test(0, [0], "")
    yield test(0, [0], "a")
    yield test(1, [], "a")
    yield test(1, [0], "ab")
    yield test(2, [], "ab")
    yield test(0, [0], "abc")
    yield test(1, [0], "abc")
    yield test(2, [0], "abc")
    yield test(3, [], "abc")

    for preset in [None, END] + list(range(7, 15)):
        test = partial(base_test, text=TEXT, preset=preset)
        yield test(0, [0, 4, 8, 9, 14, 18])
        yield test(1, [0, 4, 8, 9, 14, 18])
        yield test(2, [0, 4, 8, 9, 14, 18])
        yield test(3, [0, 4, 8, 9, 14, 18])
        yield test(4, [4, 8, 9, 14, 18], start=2)
        yield test(7, [4, 8, 9, 14, 18], start=2)
        yield test(8, [8, 9, 14, 18], start=3)
        yield test(9, [9, 14, 18], start=4)
        yield test(13, [9, 14, 18], start=4)
        yield test(14, [14, 18], start=5)
        yield test(17, [14, 18], start=5)
        yield test(18, [18], start=6)

def test_delitem_len_bug():
    eq_(list(LineNumbers(Text("\n")).iter_from(0)), [(1, 0)]) # sanity check

    text = Text("\nx")
    lines = LineNumbers(text)
    # sanity check
    eq_(list(lines.iter_from(0)), [(1, 0), (2, 1)])
    eq_(len(lines), 2, repr(text))

    text[1:] = ""
    eq_(list(lines.iter_from(0)), [(1, 0)])
    assert lines.newline_at_end, 'no newline at end: ' + repr(text)
    eq_(len(lines), 2, repr(text))

def test_len():
    @gentest
    def test(expect, text, iter_to_line=None):
        text = Text(text)
        lines = LineNumbers(text)
        if iter_to_line is not None:
            for line, index in lines.iter_from(0):
                if line >= iter_to_line:
                    break
        eq_(len(lines), expect)
    base_test = test

    yield test(1, "")
    yield test(1, "", 1)
    yield test(1, "", 2)
    yield test(1, "a")
    yield test(1, "a", 1)
    yield test(1, "a", 2)

    test = partial(base_test, text=TEXT)
    yield test(1, iter_to_line=0)
    yield test(1, iter_to_line=1)
    yield test(3, iter_to_line=3)
    yield test(4, iter_to_line=4)
    yield test(5, iter_to_line=5)
    yield test(6, iter_to_line=6)

def test_iter_from():
    @gentest
    def test(i, output, text, preset=None, start=1):
        text = Text(text)
        lines = LineNumbers(text)
        if preset is END:
            lines[len(text) - 1]
        elif preset is not None:
            lines[preset]
        eq_(list(lines.iter_from(i)), list(enumerate(output, start=start)))
    base_test = test

    yield test(0, [0], "")
    yield test(0, [0], "a")
    yield test(1, [], "a")
    yield test(1, [0], "ab")
    yield test(2, [], "ab")
    yield test(0, [0], "abc")
    yield test(1, [0], "abc")
    yield test(2, [0], "abc")
    yield test(3, [], "abc")

    yield test(0, [0, 1, 2], "\n\n\n")

    for preset in [None, END] + list(range(7, 15)):
        test = partial(base_test, text=TEXT, preset=preset)
        yield test(0, [0, 4, 8, 9, 14])
        yield test(1, [0, 4, 8, 9, 14])
        yield test(2, [0, 4, 8, 9, 14])
        yield test(3, [0, 4, 8, 9, 14])
        yield test(4, [4, 8, 9, 14], start=2)
        yield test(7, [4, 8, 9, 14], start=2)
        yield test(8, [8, 9, 14], start=3)
        yield test(9, [9, 14], start=4)
        yield test(13, [9, 14], start=4)
        yield test(14, [14], start=5)
        yield test(17, [14], start=5)
        yield test(18, [])

def test_newline_at_end():
    @gentest
    def test(expect, text, iter_to_line=None):
        text = Text(text)
        lines = LineNumbers(text)
        if iter_to_line is not None:
            for line, index in lines.iter_from(0):
                if line >= iter_to_line:
                    break
        eq_(lines.newline_at_end, expect)
    base_test = test

    yield test(None, "")
    yield test(None, "", 1)
    yield test(False, "", 2)
    yield test(None, "a")
    yield test(None, "a", 1)
    yield test(False, "a", 2)

    test = partial(base_test, text=TEXT)
    yield test(None, iter_to_line=0)
    yield test(None, iter_to_line=1)
    yield test(None, iter_to_line=3)
    yield test(None, iter_to_line=4)
    yield test(None, iter_to_line=5)
    yield test(True, iter_to_line=6)

def test_index_of_line():
    LINE = Constant("LINE")

    @gentest
    def test(num, expect, text, iter_to_line=None):
        text = Text(text)
        lines = LineNumbers(text)
        if iter_to_line is END:
            list(lines.iter_from(0))
            assert lines.end is not None
        elif iter_to_line is not None:
            if iter_to_line is LINE:
                iter_to_line = num
            for line, index in lines.iter_from(0):
                if line >= iter_to_line:
                    break
        if isinstance(expect, int):
            eq_(lines.index_of(num), expect)
        else:
            with assert_raises(expect):
                lines.index_of(num)
    base_test = test

    yield test(-1, ValueError, "")
    yield test(0, ValueError, "")
    yield test(1, 0, "")
    yield test(1, 0, "", 1)
    yield test(1, 0, "", 2)
    yield test(1, 0, "a")
    yield test(1, 0, "a", 1)
    yield test(1, 0, "a", 2)
    yield test(2, ValueError, "")
    yield test(2, ValueError, "", 2)

    test = partial(base_test, text=TEXT)
    for to in [None, 0, LINE, END]:
        yield test(1, 0, iter_to_line=to)
        yield test(2, 4, iter_to_line=to)
        yield test(3, 8, iter_to_line=to)
        yield test(4, 9, iter_to_line=to)
        yield test(5, 14, iter_to_line=to)
        yield test(6, 18, iter_to_line=to)
        yield test(7, ValueError, iter_to_line=to)
