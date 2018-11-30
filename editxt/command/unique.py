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

from editxt.command.base import command
from editxt.command.parser import Choice, CommandParser
from editxt.command.util import has_selection
from editxt.commands import iterlines

log = logging.getLogger(__name__)


def get_default_range(editor=None):
    return editor is None or has_selection(editor)


@command(name='unique', title="Unique Lines", arg_parser=CommandParser(
    Choice(('selection', True), ('all', False), default=get_default_range),
))
def unique_lines(editor, args):
    """Remove duplicate lines"""
    text = editor.text
    if args.selection:
        range = text.line_range(editor.selection)
    else:
        range = (0, len(text))
    output = "".join(unique(iterlines(text, range)))
    editor.put(output, range, select=args.selection)


def unique(lines):
    seen = set()
    for line in lines:
        if line not in seen:
            seen.add(line)
            yield line
