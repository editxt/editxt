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
from editxt.command.parser import Choice, Regex, RegexPattern, CommandParser, Options

log = logging.getLogger(__name__)


@command
def diff(textview, sender, args):
    """Diff with original"""
    # TODO accept (optional) path of file to diff with (instead of original file)
    editor = textview.editor
    file_path = editor.file_path
    if file_path is None:
        raise CommandError("file has not been saved")
    elif not os.path.exists(file_path):
        raise CommandError("file not found: {}".format(file_path))
    else:
        name = os.path.basename(file_path)
        diff_program = editor.app.config["diff_program"]
        external_diff(file_path, textview.string(), name, diff_program)


def external_diff(filepath, text, name, diff_program):
    """Use an external diff program to compare a file with the given text

    :param filepath: A file path.
    :param text: Text to be compared to the content of the file at `filepath`.
    :param name: A filename (not path) to use when saving text to disk.
    :param diff_program: The diff program to run. All output from this
    command (stdout and stderr) is ignored.
    """
    name, ext = os.path.splitext(name)
    with NamedTemporaryFile("w",
         encoding="UTF-8", prefix=name + "-", suffix=ext, delete=False) as fh:
        fh.write(text)
        command = [filepath, fh.name]
    cmd = "{} {}; {}".format(
        diff_program,
        list2cmdline(command),
        list2cmdline(["rm", "-v", command[-1]]),
    )
    with open("/dev/null", mode="w") as null:
        Popen(cmd, shell=True,
              stdin=None, stdout=null, stderr=null, close_fds=True)
