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
from textwrap import dedent
from urllib.parse import quote

import editxt.constants as const
import editxt.config as config
from editxt.command.base import command, CommandError
from editxt.command.parser import CommandParser, File, Regex, RegexPattern, String, VarArgs
from editxt.command.util import exec_shell, get_selection, has_editor
from editxt.platform.app import beep
from editxt.platform.markdown import markdown

log = logging.getLogger(__name__)
AG_LINE = re.compile(r"""
    (?P<num>\d*)                    # line number
    (?P<ranges>;(?:\d+\ \d+,?)*)?   # matched ranges
    (?P<delim>:)                    # delimiter
    (?P<text>.*)                    # line content
""", re.VERBOSE)
DEFAULT_OPTIONS = [
    "--ackmate",
    "--nopager",
    "--nocolor",
    "--print0",
]


def get_selection_regex(editor=None):
    text = get_selection(editor)
    return RegexPattern(re.escape(text), default_flags=0) if text else None


def editor_dirname(editor=None):
    return None if editor is None else editor.dirname()


@command(
    name="ag ack",
    arg_parser=CommandParser(
        Regex("pattern", default=get_selection_regex),
        File("path", default=editor_dirname),
        VarArgs("options", String("options")),
        # TODO SubParser with dynamic dispatch based on pattern matching
        # (if it starts with a "-" it's an option, otherwise a file path)
    ),
    config={
        "path": config.String("ag"),
        "options": config.String(""),
    },
    is_enabled=has_editor,
)
def ag(editor, args):
    """Search for files matching pattern"""
    if args is None:
        from editxt.commands import show_command_bar
        show_command_bar(editor, "ag ")
        return
    elif args.pattern is None:
        raise CommandError("please specify a pattern to match")
    pattern = args.pattern
    if "-i" in args.options or "--ignore-case" in args.options:
        pattern = RegexPattern(pattern, pattern.flags | re.IGNORECASE)
    elif pattern.flags & re.IGNORECASE:
        args.options.append("--ignore-case")
    ag_path = editor.app.config.for_command("ag")["path"]
    options = editor.app.config.for_command("ag")["options"].split()
    options = [o for o in args.options if o] + DEFAULT_OPTIONS + options
    cwd = args.path or editor.dirname()
    command = [ag_path, pattern] + options
    result = exec_shell(command, cwd=cwd)
    if result.returncode == 0:
        msg_type = const.INFO
        lines = ag_lines(result, pattern, cwd)
        message = markdown("\n".join(lines), pre=True)
    elif not is_ag_installed(ag_path):
        msg_type = const.ERROR
        message = markdown(dedent("""
            [ag](https://github.com/ggreer/the_silver_searcher#the-silver-searcher)
            does not appear to be installed

            It may be necessary to set `command.ag.path` in
            [Preferences](xt://preferences).

            Current setting: `{}`
        """.format(ag_path)))
    else:
        msg_type = const.ERROR
        message = result or result.err
    if message:
        editor.message(message, msg_type=msg_type)
    else:
        return "no match for pattern: {}".format(args.pattern)


ack = ag


def ag_lines(result, pattern, cwd):
    if not result:
        yield result.err or "no output"
        return
    regex = re.compile(pattern + r"""|(['"(\[`_])""", pattern.flags)
    print(repr(result))
    for i, file_and_lines in enumerate(result.split("\n\n:")):
        if i:
            yield ""
        filepath, lines = file_and_lines.split("\0", 1)
        lines = lines.rstrip("\0").split("\n")
        if i == 0:
            assert filepath.startswith(":"), filepath
            filepath = filepath[1:]
        #if not lines:
        #    yield filepath
        #    continue
        absfilepath = os.path.join(cwd, filepath)
        yield open_link(filepath, absfilepath)
        for line in lines:
            match = AG_LINE.match(line)
            if match:
                yield link_matches(absfilepath, **match.groupdict(''))
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


def link_matches(filepath, num, ranges, delim, text):
    def iter_parts(ranges):
        end = 0
        if ranges:
            for rng in ranges.split(","):
                start, length = [int(n) for n in rng.split()]
                if start > end:
                    yield text[end:start]
                end = start + length
                goto = "{}.{}.{}".format(num, start, length)
                yield open_link(text[start:end], filepath, goto)
        yield text[end:]
    prefix = open_link(num, filepath, num) + delim
    line_text = "".join(iter_parts(ranges.lstrip(";")))
    return open_link(num, filepath, num) + delim + line_text


def is_ag_installed(ag_path="ag", recheck=False, result={}):
    if result.get(ag_path) is not None and not recheck:
        return result.get(ag_path)
    result[ag_path] = exec_shell([ag_path, "--version"]).returncode == 0
    return result[ag_path]
