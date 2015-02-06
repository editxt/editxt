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

    TEXT = (
        "abc\n"  # 0     3   1
        "def\n"  # 4     7   2
        "\n"     # 8     8   3
        "ghij\n" # 9     13  4
        "jkl\n"  # 14    17  5
    )
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

    TEXT = (
        "abc\n"  # 0     3   1
        "def\n"  # 4     7   2
        "\n"     # 8     8   3
        "ghij\n" # 9     13  4
        "jkl\n"  # 14    17  5
    )
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

    TEXT = (
        "abc\n"  # 0     3   1
        "def\n"  # 4     7   2
        "\n"     # 8     8   3
        "ghij\n" # 9     13  4
        "jkl\n"  # 14    17  5
    )
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

    TEXT = (
        "abc\n"  # 0     3   1
        "def\n"  # 4     7   2
        "\n"     # 8     8   3
        "ghij\n" # 9     13  4
        "jkl\n"  # 14    17  5
    )
    test = partial(base_test, text=TEXT)
    yield test(None, iter_to_line=0)
    yield test(None, iter_to_line=1)
    yield test(None, iter_to_line=3)
    yield test(None, iter_to_line=4)
    yield test(None, iter_to_line=5)
    yield test(True, iter_to_line=6)
