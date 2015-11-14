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
import logging
import os

import editxt.constants as const
from editxt.command.ack import exec_shell
from editxt.command.base import command
from editxt.command.parser import CommandParser, Choice, File, String, VarArgs

log = logging.getLogger(__name__)


def default_range(editor=None):
    if editor and editor.selection and editor.selection[1]:
        return "selection"
    return "all"


@command(arg_parser=CommandParser(
    File("executable"),
    Choice("all", "selection", name="scope", default=default_range),
    VarArgs("options", String("options")),
), title="Run Python code")
def python(editor, args):
    """Run the contents of the editor or selection in Python"""
    if args is None:
        from editxt.commands import show_command_bar
        show_command_bar(editor, "python ")
        return
    if not args.executable:
        try:
            python = editor.app.config.for_command("python")["executable"]
        except KeyError:
            python = "python"
    else:
        python = args.executable
    if args.scope == "selection":
        code = editor.document.text_storage[editor.selection]
    else:
        code = editor.document.text
    cwd = editor.dirname()
    command = [python] + [o for o in args.options if o] + ["-c", code]
    env = dict(os.environ)
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONDONTWRITEBYTECODE", None)
    env.pop("EXECUTABLEPATH", None)
    env.pop("RESOURCEPATH", None)
    result = exec_shell(command, cwd=cwd, env=env)
    if result.returncode == 0:
        msg_type = const.INFO
        message = str(result)
    else:
        msg_type = const.ERROR
        message = result or result.err
    if message:
        editor.message(message, msg_type=msg_type)
    else:
        return "no output"
