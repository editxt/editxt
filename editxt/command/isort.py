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
import time
from os.path import abspath, dirname

import objc
from isort import SortImports

from editxt.command.base import command
from editxt.command.parser import Choice, CommandParser, Options
from editxt.command.util import has_selection


def default_scope(editor=None):
    return editor is not None and has_selection(editor)


@command(name='isort', title="Sort imports...",
    arg_parser=CommandParser(
        Choice(('selection', True), ('all', False), default=default_scope),
    ))
def sort_imports(editor, args):
    if args is None:
        args = Options(
            selection=False,
        )
    if editor is not None and editor.file_path:
        settings_path = dirname(abspath(editor.file_path))
    else:
        settings_path = None
    sel = editor.selection if args.selection else (0, len(editor.text))
    src = editor.text[sel]
    txt = SortImports(
        file_contents=src,
        settings_path=settings_path,
    ).output
    editor.put(txt, sel, select=args.selection)
