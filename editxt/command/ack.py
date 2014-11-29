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
from textwrap import dedent
from traceback import format_exc
from urllib.parse import quote

import editxt.constants as const
import editxt.config as config
from editxt.command.base import command, CommandError
from editxt.command.parser import CommandParser, File, Regex, String, VarArgs
from editxt.command.util import has_editor
from editxt.platform.markdown import markdown

log = logging.getLogger(__name__)
ACK_LINE = re.compile(r"(.*?):(\d+:.*)")


@command(arg_parser=CommandParser(
    Regex("pattern"),
    File("path"),
    VarArgs("options", String("options")),
    # TODO SubParser with dynamic dispatch based on pattern matching
    # (if it starts with a "-" it's an option, otherwise a file path)
), config={"path": config.String("ack")}, is_enabled=has_editor)
def ack(editor, sender, args):
    """Search for files matching pattern"""
    if args is None:
        from editxt.commands import show_command_bar
        show_command_bar(editor, sender, "ack ")
        return
    elif args.pattern is None:
        raise CommandError("please specify a pattern to match")
    ack_path = editor.app.config.for_command("ack")["path"]
    cwd = args.path or editor.dirname()
    command = [ack_path, args.pattern] + [o for o in args.options if o]
    result = exec_shell(command, cwd=cwd)
    if result.returncode == 0:
        msg_type = const.INFO
        lines = ack_lines(result, args.pattern, cwd)
        message = markdown("\n".join(lines), pre=True)
    elif not is_ack_installed(ack_path):
        msg_type = const.ERROR
        message = markdown(dedent("""
            [ack](http://beyondgrep.com/) does not appear to be installed

            It may be necessary to set `command.ack.path` in
            [Preferences](xt://preferences).

            Current setting: `{}`
        """.format(ack_path)))
    else:
        msg_type = const.ERROR
        message = result or result.err
    editor.message(message, msg_type=msg_type)


def ack_lines(result, pattern, cwd):
    if not result:
        yield result.err or "no output"
        return
    regex = re.compile(pattern + """|(['"(\[`_])""")
    prev_filepath = None
    for line in result.split("\n"):
        match = ACK_LINE.match(line)
        if match:
            filepath = match.group(1)
            if filepath != prev_filepath:
                abspath = os.path.join(cwd, filepath)
                if prev_filepath:
                    yield ""
                yield open_link(filepath, abspath)
                prev_filepath = filepath
            yield link_matches(match.group(2), abspath, regex)
        else:
            yield line


def open_link(text, path, goto=None):
    """Create markdown "open" link

    :param text: The link text.
    :param path: The path of the file to open.
    :param goto: Optional goto parameter: line number or
    `"{line_num}.{select_start}.{select_len}"`
    """
    url = "xt://open/" + quote(path)
    if goto is not None:
        url += "?goto={}".format(goto)
    return markdown_link(text, url)


def markdown_link(text, url):
    return "[{}]({})".format(
        text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]"),
        url
    )


def link_matches(line, filepath, regex, split=re.compile("(\d+):")):
    def link(match):
        if match.groups()[-1]:
            return "\\" + match.groups()[-1]
        start, end = match.span()
        if start > -1:
            goto = "{}.{}.{}".format(num, start, end - start)
        else:
            goto = num
        return open_link(match.group(0), filepath, goto)
    num_match = split.match(line)
    if num_match:
        num = num_match.group(1)
        line = line[len(num) + 1:]
        prefix = open_link(num, filepath, num) + ":"
    else:
        num = None
        prefix = ""
    return prefix + regex.sub(link, line)


def is_ack_installed(ack_path="ack", recheck=False, result={}):
    if result.get(ack_path) is not None and not recheck:
        return result.get(ack_path)
    result[ack_path] = exec_shell([ack_path, "--version"]).returncode == 0
    return result[ack_path]


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
