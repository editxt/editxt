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
import re
from subprocess import Popen, PIPE, STDOUT, TimeoutExpired
from tempfile import NamedTemporaryFile
from traceback import format_exc

import editxt.constants as const
from editxt.command.base import command, CommandError
from editxt.command.parser import CommandParser, File, Regex, String, VarArgs
from editxt.command.util import has_editor

log = logging.getLogger(__name__)
ACK_LINE = re.compile(r"(.*?):(\d+:.*)")


@command(arg_parser=CommandParser(
    Regex("pattern"),
    File("path"),
    VarArgs("options", String("options")),
    # TODO SubParser with dynamic dispatch based on pattern matching
    # (if it starts with a "-" it's an option, otherwise a file path)
), is_enabled=has_editor)
def ack(editor, sender, args):
    """Search for files matching pattern"""
    if args is None:
        from editxt.commands import show_command_bar
        show_command_bar(editor, sender, "ack ")
        return
    elif args.pattern is None:
        raise CommandError("please specify a pattern to match")
    cwd = args.path or editor.dirname()
    command = ["ack", args.pattern] + [o for o in args.options if o]
    result = exec_shell(command, cwd=cwd)
    msg_type = const.INFO if result.returncode == 0 else const.ERROR
    editor.message("\n".join(ack_lines(result)), msg_type=msg_type)


def ack_lines(result):
    if not result:
        yield result.err or "no output"
        return
    prev_filepath = None
    for line in result.split("\n"):
        match = ACK_LINE.match(line)
        if match:
            filepath = match.group(1)
            if filepath != prev_filepath:
                if prev_filepath:
                    yield ""
                yield filepath
                prev_filepath = filepath
            yield match.group(2)
        else:
            yield line


def exec_shell(command, cwd=None, timeout=60):
    """Execute shell command

    :param command: A list of command name and arguments.
    :returns: `CommandResult`, which is a string containing the sdtout
    output from the command. See `CommandResult` docs for more details.
    """
    try:
        proc = Popen(command, cwd=cwd, stdout=PIPE, stderr=STDOUT)
        out, err = proc.communicate(timeout=timeout)
        returncode = proc.returncode
    except TimeoutExpired:
        proc.kill()
        out, err = proc.communicate().decode("utf-8")
        returncode = proc.returncode
    except Exception as exc:
        out = "{}: {}\n{}".format(type(exc).__name__, exc, format_exc())
        err = ""
        returncode = None
    if isinstance(out, bytes):
        out = out.decode("utf-8")
    if isinstance(err, bytes):
        err = err.decode("utf-8")
    return CommandResult(out, err, returncode)


class CommandResult(str):

    __slots__ = ["err", "returncode"]

    def __new__(cls, out, err="", returncode=None):
        self = super().__new__(cls, out)
        self.err = err
        self.returncode = returncode
        return self
