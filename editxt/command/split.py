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
import re

from editxt.command.base import command
from editxt.command.parser import CommandParser, Regex, String
from editxt.command.util import has_editor, has_selection, iterlines
from editxt.command.wraplines import WHITESPACE
from editxt.platform.app import beep

log = logging.getLogger(__name__)


@command(name='split', title="Split text into lines...",
    arg_parser=CommandParser(Regex('pattern', default=r'\s+')),
    is_enabled=has_editor)
def split_text(editor, args):
    """Split the current line of (or selected) text into separate lines

    The current line is split if there is no selection. If there is a
    selection then all lines touched by the selection are split. The
    indentation level of the first line is used for all new lines.
    """
    if args is None:
        args = split_text.arg_parser.default_options()
    eol = editor.document.eol
    rng = editor.text.line_range(editor.selection)
    lines = iterlines(editor.text, rng)
    text = eol.join(_split(lines, args.pattern, eol)) + eol
    editor.put(text, rng, select=True)


@command(name="join unsplit", title="Join (unsplit) lines...",
    arg_parser=CommandParser(String("delimiter", default=' ')),
    is_enabled=has_selection)
def join_lines(editor, args):
    """Join selected lines into a single line"""
    if args is None:
        args = join_lines.arg_parser.default_options()
    eol = editor.document.eol
    if not editor.selection[1]:
        beep()
        return
    rng = editor.text.line_range(editor.selection)
    lines = iterlines(editor.text, rng)
    text = args.delimiter.join(_unsplit(lines, eol)) + eol
    editor.put(text, rng, select=True)


def _split(lines, pattern, eol):
    regex = re.compile(pattern, pattern.flags)
    leading = None
    for line in lines:
        if not line:
            continue
        if leading is None:
            leading = WHITESPACE.match(line).group(0)
            assert isinstance(leading, str), repr(leading)
        line = line.rstrip(eol)
        for item in regex.split(line):
            if item:
                yield leading + item


def _unsplit(lines, eol):
    def lstrip(text):
        leading = len(WHITESPACE.match(text).group(0))
        return text[leading:]
    line = next(lines, None)
    if line is None:
        return
    line = line.rstrip(eol)
    if line:
        yield line
    for line in lines:
        if not line:
            continue
        line = lstrip(line).rstrip(eol)
        if line:
            yield line
