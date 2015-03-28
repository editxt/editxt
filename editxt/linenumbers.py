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
        This will not generate a line number/index pair for the last
        line if its length is zero (i.e., if there is a newline at the
        end of the text).
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
            text = self.text
            next = 0
            for line, rng in enumerate(text.iter_line_ranges(index), start=line):
                index = rng[0]
                next = sum(rng)
                if index > start or (next > start and prev_line < line):
                    yield line, index
                lines.append(next)
            self.end = lines.pop() if next else 0
            self.newline_at_end = bool(text) and text.ends_with_newline()

    def index_of(self, line):
        """Return the character index of the given line number

        :param line: A line number.
        :returns: Index of the first character of line.
        :raises: `ValueError` if line is out of bounds (greater or less than
        the number of lines in the text).
        """
        if line < 1:
            raise ValueError(line)
        lines = self.lines
        if len(lines) >= line:
            return lines[line - 1]
        for lno, index in self.iter_from(lines[-1]):
            if line == lno:
                return index
            assert lno < line, (line, lno)
        if self.newline_at_end and len(lines) + 1 == line:
            return self.end
        raise ValueError(line)
