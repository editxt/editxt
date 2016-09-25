# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2016 Daniel Miller <millerdev@gmail.com>
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
import subprocess
from os.path import dirname, isfile, realpath

from editxt.command.base import command, CommandError
from editxt.command.parser import CommandParser, File
from editxt.command.util import has_editor

log = logging.getLogger(__name__)


def file_path(editor=None):
    return editor.file_path if editor is not None else None


@command(arg_parser=CommandParser(
    File("path", default=file_path),
), is_enabled=has_editor)
def blame(editor, args):
    """Invoke git gui blame on file path"""
    if not args:
        from editxt.commands import show_command_bar
        return show_command_bar(editor, "blame ")
    if not (args.path and isfile(args.path)):
        raise CommandError("cannot blame file without path")
    subprocess.Popen(
        ["git", "gui", "blame", args.path],
        cwd=dirname(realpath(args.path)),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
