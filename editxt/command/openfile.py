# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2014 Daniel Miller <millerdev@gmail.com>
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
import os
from tempfile import NamedTemporaryFile
from subprocess import Popen, list2cmdline

import editxt.constants as const
from editxt.command.base import command, CommandError
from editxt.command.parser import CommandParser, File
from editxt.editor import Editor

log = logging.getLogger(__name__)


@command(name="open", arg_parser=CommandParser(File("path")))
def open_(textview, sender, args):
    """Open file"""
    if args is None:
        from editxt.commands import show_command_bar
        show_command_bar(textview, sender, "open ")
    elif args.path is None:
        raise CommandError("please specify a file path")
    else:
        open_files([args.path], textview.editor.project)


def open_files(paths, project, index=-1):
    """Open files in project

    :param paths: A list of file paths.
    :param project: The project in which to open paths.
    :param index: The index at which to insert new editors in the project's list
    of editors. Use `-1` to insert at the end; `'current'` will insert
    after the current editor.
    """
    #if index == 'current':
    #    raise NotImplementedError
    editors = [Editor(project, path=path) for path in paths]
    project.insert_items(editors, index)
    project.window.current_editor = editors[-1]
