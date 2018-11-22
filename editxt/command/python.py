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
import ast
import logging
import os
from distutils.spawn import find_executable
from textwrap import dedent

import editxt.config as config
import editxt.constants as const
from editxt.command.base import command, CommandError
from editxt.command.parser import CommandParser, Choice, File, String, VarArgs
from editxt.command.util import exec_shell

log = logging.getLogger(__name__)


def get_python_executable(editor=None):
    if editor is not None:
        try:
            value = editor.app.config.for_command("python")["executable"]
        except KeyError:
            pass
    else:
        value = "python"
    if os.path.sep in value:
        return value
    return find_executable(value)


def default_range(editor=None):
    if editor and editor.selection and editor.selection[1]:
        return "selection"
    return "all"


@command(
    arg_parser=CommandParser(
        File("executable", default=get_python_executable),
        Choice("all", "selection", name="scope", default=default_range),
        VarArgs("options", String("options")),
    ),
    config={"executable": config.String("python")},
    title="Run Python code",
)
def python(editor, args):
    """Run the contents of the editor or selection in Python

    executable may be a python interpreter executable or a directory
    such as a virtualenv containing `bin/python`.
    """
    if args is None:
        from editxt.commands import show_command_bar
        show_command_bar(editor, "python ")
        return
    python = args.executable
    if not python:
        raise CommandError("please specify python executable")
    if os.path.isdir(python):
        bin = os.path.join(python, "bin", "python")
        if os.path.exists(bin):
            python = bin
        else:
            raise CommandError("not found: %s" % bin)
    if args.scope == "selection":
        code = editor.document.text_storage[editor.selection]
    else:
        code = editor.document.text
    code = print_last_line(dedent(code))
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
        if message.endswith("\n"):
            message = message[:-1]
    else:
        msg_type = const.ERROR
        message = result or result.err
    if message:
        editor.message(message, msg_type=msg_type)
    else:
        return "no output"


def print_last_line(code):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code
    if tree.body and isinstance(tree.body[-1], ast.Expr):
        offset = get_node_offset(tree.body[-1], code)
        code = "".join([
            code[:offset],
            "__result__ = ",
            code[offset:],
            "\nif __result__ is not None: print(__result__)",
        ])
    return code


def get_node_offset(node, code):
    if node.lineno == 1:
        return node.col_offset
    total = 0
    for num, line in enumerate(code.splitlines(True), start=1):
        if num == node.lineno:
            return total + node.col_offset
        total += len(line)
    raise ValueError("line out of bounds: {}".format(node.lineno))
