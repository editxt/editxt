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
import html
import os
import re
import shlex
from os.path import basename, expanduser, splitext
from tempfile import NamedTemporaryFile
from urllib.parse import quote

import editxt.config as config
import editxt.constants as const
from editxt.command.base import command
from editxt.command.parser import CommandParser, Options, String, VarArgs
from editxt.command.util import exec_shell, has_editor, threaded_exec_shell
from editxt.platform.markdown import html_string, markdown

CMD = "flake8"
CMD_OPTIONS = ["--exit-zero"]
OUTPUT_LINE = re.compile(r"""
    (?P<path>.+):       # file path
    (?P<line>\d+):      # line number
    (?P<pos>-?\d+):     # line position
    \s*
    (?P<text>.+)        # text
""", re.VERBOSE)
NOT_INSTALLED = """
[flake8](https://gitlab.com/pycqa/flake8)
does not appear to be installed

It may be necessary to set `command.flake8.path` in [Preferences](xt://preferences).

Current setting: `{}`
"""


@command(name="flake8", title="Check Python code quality",
    arg_parser=CommandParser(
        VarArgs("options", String("options")),
    ),
    config={
        "path": config.String(CMD),
        "options": config.String(""),
    },
    is_enabled=has_editor,
)
def flake8(editor, args):
    if args is None:
        args = Options(options=[])
    cmd_path = expanduser(editor.app.config.for_command(CMD)["path"])
    options = editor.app.config.for_command(CMD)["options"]
    options = CMD_OPTIONS + shlex.split(options)
    if editor.document.has_real_path() and not editor.is_dirty:
        filepath = editor.file_path
        tmp_path = None
    else:
        filepath = tmp_path = get_temp_path(editor)
    view = editor.get_output_view()
    line_processor = make_line_processor(view, cmd_path, tmp_path)
    command = [cmd_path, filepath] + [o for o in args.options if o] + options
    view.process = threaded_exec_shell(command, cwd="/", **line_processor)


def make_line_processor(view, cmd_path, tmp_path):

    def iter_output(lines):
        br = "<br />"
        for line in lines:
            line = line.rstrip("\n")
            match = OUTPUT_LINE.match(line)
            if match:
                yield output_line(view.editor, **match.groupdict('')) + br
            else:
                yield html.escape(line) + br

    def got_output(text, returncode):
        if text is not None:
            view.append_message(html_string(text, pre=True))
        if returncode:
            if is_installed(cmd_path):
                message = "exit code: {}".format(returncode)
            else:
                message = markdown(NOT_INSTALLED.format(cmd_path))
            view.append_message(message, msg_type=const.ERROR)
        if returncode is not None:
            if not view.has_output:
                view.append_message("Clean code")
            if tmp_path is not None:
                os.remove(tmp_path)
            view.process_completed()

    return {"iter_output": iter_output, "got_output": got_output}


def output_line(editor, path, line, pos, text):
    if path != editor.file_path:
        path = None
    return "{}  {}".format(
        link(path, line, 1, line),
        link(path, line, pos, text),
    )


def link(path, line, pos, text):
    pos = max(int(pos) - 1, 0)
    goto = "{}.{}.0".format(line, pos)
    if path is None:
        url = "xt://goto/{}".format(goto)
    else:
        url = "xt://open/{}?goto={}".format(quote(path), goto)
    return "<a href='{}'>{}</a>".format(url, html.escape(text))


def get_temp_path(editor):
    """Get editor content in a temporary file"""
    name, ext = splitext(basename(editor.file_path) or "untitled")
    with NamedTemporaryFile("w", encoding="UTF-8",
                            prefix=name + "-", suffix=ext, delete=False) as fh:
        fh.write(editor.text_view.string())
        return fh.name


def is_installed(cmd_path=CMD, recheck=False, result={}):
    if result.get(cmd_path) is not None and not recheck:
        return result.get(cmd_path)
    result[cmd_path] = exec_shell([cmd_path, "--version"]).returncode == 0
    return result[cmd_path]
