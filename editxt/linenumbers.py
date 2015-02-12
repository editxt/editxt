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
from bisect import bisect

from editxt.constants import EOLS as _EOLS

EOLS = tuple(_EOLS.values())


class LineNumbers(object):

    def __init__(self, text):
        self.text = text
        self.lines = [0]
        self.end = None
        self.newline_at_end = None
        def process_edit(edit_range):
            del self[edit_range[0]]
        self.close = text.on_edit(process_edit)

    def __getitem__(self, index):
        """Get line number for character at index"""
        line = next(self.iter_from(index), (None, None))[0]
        if line is None:
            raise IndexError(index)
        return line

    def __delitem__(self, index):
        """Invalidate line numbers beyond the character at index"""
        if index < self.lines[-1]:
            line = max(1, bisect(self.lines, index) - 1)
            del self.lines[line:]
        if self.end is not None:
            self.end = None
            self.newline_at_end = None

    def __len__(self):
        """Get the highest known line number

        This will always return less than or equal to the total number of
        lines in text.
        """
        return len(self.lines) + (1 if self.newline_at_end else 0)

    def iter_from(self, start):
        """Generate `(line_number, char_index)` pairs from start index

        `char_index` in each generated pair is the index of the first
        character of the line at the corresponding `line_number`.
        """
        lines = self.lines
        index = lines[-1]
        if start <= index:
            line = bisect(lines, start)
            for line, index in enumerate(lines[line - 1:], start=line):
                yield line, index
            start = index
            prev_line = line
        else:
            line = len(lines)
            prev_line = line - 1
        if self.end is None or start < self.end:
            text = ""
            for line, text in enumerate(self.text.iterlines(index), start=line):
                next = index + len(text)
                if index > start or (next > start and prev_line < line):
                    yield line, index
                lines.append(next)
                index = next
            self.end = lines.pop(-1)
            self.newline_at_end = text.endswith(EOLS)
