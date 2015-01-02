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
from editxt.command.parser import CommandParser, File, Regex, RegexPattern, String, VarArgs
from editxt.command.util import has_editor
from editxt.platform.app import beep
from editxt.platform.markdown import markdown

log = logging.getLogger(__name__)
ACK_LINE = re.compile(r"(\d+)([:-])(.*)")
DEFAULT_OPTIONS = [
    "--heading",
    "--group",
    "--break",
    "--nopager",
    "--nocolor",
    "--print0",
]


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
    pattern = args.pattern
    if "-i" in args.options or "--ignore-case" in args.options:
        pattern = RegexPattern(pattern, pattern.flags | re.IGNORECASE)
    elif pattern.flags & re.IGNORECASE:
        args.options.append("--ignore-case")
    ack_path = editor.app.config.for_command("ack")["path"]
    cwd = args.path or editor.dirname()
    command = [ack_path, pattern] + [o for o in args.options if o] + DEFAULT_OPTIONS
    result = exec_shell(command, cwd=cwd)
    if result.returncode == 0:
        msg_type = const.INFO
        lines = ack_lines(result, pattern, cwd)
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
    if message:
        editor.message(message, msg_type=msg_type)
    else:
        return "no match for pattern: {}".format(args.pattern)


def ack_lines(result, pattern, cwd):
    if not result:
        yield result.err or "no output"
        return
    regex = re.compile(pattern + r"""|(['"(\[`_])""", pattern.flags)
    for file_and_lines in result.split("\n"):
        filepath, *lines = file_and_lines.split("\x00")
        if not lines:
            yield filepath
            continue
        abspath = os.path.join(cwd, filepath)
        yield open_link(filepath, abspath)
        for line in lines:
            match = ACK_LINE.match(line)
            if match:
                yield link_matches(match, abspath, regex)
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
        text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]").replace("_", "\\_"),
        url
    )


def link_matches(match, filepath, regex, split=re.compile("(\d+):")):
    def link(match):
        if match.groups()[-1]:
            return "\\" + match.groups()[-1]
        start, end = match.span()
        if start > -1:
            goto = "{}.{}.{}".format(num, start, end - start)
        else:
            goto = num
        return open_link(match.group(0), filepath, goto)
    num, delim, line = match.group(1, 2, 3)
    prefix = open_link(num, filepath, num) + delim
    if delim == "-":
        return prefix + line
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
