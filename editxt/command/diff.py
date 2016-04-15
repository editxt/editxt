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
import os
from tempfile import NamedTemporaryFile
from subprocess import Popen, list2cmdline

import editxt.constants as const
from editxt.command.base import command, CommandError
from editxt.command.parser import CommandParser, String

log = logging.getLogger(__name__)


@command(arg_parser=CommandParser(String("file")))
def diff(editor, args):
    """Diff with original"""
    remove = []
    if args and args.file:
        path1 = args.file
        path2 = get_text_path(editor, remove)
    elif len(editor.project.window.selected_items) == 2:
        path1 = get_text_path(editor, remove)
        path2 = get_text_path(editor.project.window.selected_items[1], remove)
    elif editor.document.has_real_path():
        path1 = editor.file_path
        path2 = get_text_path(editor, remove)
    else:
        raise CommandError("file has not been saved")
    if not os.path.exists(path1):
        raise CommandError("file not found: {}".format(path1))
    name = os.path.basename(editor.file_path)
    diff_program = editor.app.config["diff_program"]
    external_diff(path1, path2, diff_program, remove)


def external_diff(path1, path2, diff_program, remove=None):
    """Use an external diff program to compare a file with the given text

    :param path1: Path of first file to compare.
    :param path2: Path of second file to compare.
    :param diff_program: The diff program to run. All output from this
    command (stdout and stderr) is ignored.
    :param remove: A list of file paths to remove once diff is complete.
    """
    cmd = diff_program + " " + list2cmdline([path1, path2])
    if remove:
        cmd += "; " + list2cmdline(["rm", "-v"] + remove)
    # TODO should use editor encoding?
    with open("/dev/null", mode="w", encoding="utf-8") as null:
        Popen(cmd, shell=True,
              stdin=None, stdout=null, stderr=null, close_fds=True)


def get_text_path(editor, remove):
    if editor.document.has_real_path() and not editor.is_dirty:
        return editor.file_path
    name, ext = os.path.splitext(editor.file_path or "untitled")
    with NamedTemporaryFile("w", encoding="UTF-8",
                            prefix=name + "-", suffix=ext, delete=False) as fh:
        fh.write(editor.text_view.string())
        remove.append(fh.name)
        return fh.name
