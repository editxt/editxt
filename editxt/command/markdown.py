# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2019 Daniel Miller <millerdev@gmail.com>
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
import objc

from editxt.command.base import command
from editxt.command.parser import Choice, CommandParser, Options
from editxt.command.util import has_selection
from editxt.platform.markdown import markdown as format_markdown


def default_scope(editor=None):
    return editor is not None and has_selection(editor)


@command(name='markdown', title="Render markdown",
    arg_parser=CommandParser(
        Choice(('selection', True), ('all', False), default=default_scope),
    ))
def markdown(editor, args):
    if args is None:
        args = Options(selection=False)
    sel = editor.selection if args.selection else (0, len(editor.text))
    return format_markdown(editor.text[sel])
