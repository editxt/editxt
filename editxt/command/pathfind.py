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
from os.path import join

from editxt.command.ag import make_line_processor, open_link
from editxt.command.base import command
from editxt.command.parser import (CommandParser, Choice, File, Options,
    Regex, RegexPattern)
from editxt.command.util import has_editor, get_selection, threaded_exec_shell

log = logging.getLogger(__name__)


def get_selection_regex(editor=None):
    text = get_selection(editor)
    return RegexPattern(text, default_flags=0) if text else None


def base_path(editor=None):
    if editor is None:
        return None
    return editor.project.file_path or editor.dirname()


@command(
    arg_parser=CommandParser(
        Regex("path-pattern", default=get_selection_regex),
        File("search-path", default=base_path),
        Choice(
            ("source-files", False),
            ("unrestricted", True),
            name="unrestricted",
        ),
    ),
    is_enabled=has_editor,
    hotkey="Command+Alt+p",
)
def pathfind(editor, args):
    """Find file by path"""
    if args is None and editor is not None:
        args = Options(
            path_pattern=get_selection_regex(editor),
            search_path=base_path(editor),
            unrestricted=False,
        )
    if not (args and args.path_pattern):
        from editxt.commands import show_command_bar
        return show_command_bar(editor, "pathfind ")
    pattern = args.path_pattern
    search_path = args.search_path
    if not search_path:
        return "please specify search path"
    ag_path = editor.app.config.for_command("ag")["path"]
    view = editor.get_output_view()
    line_proc = make_path_processor(view, pattern, ag_path, search_path, editor)
    command = [
        ag_path,
        '--files-with-matches',
        '--file-search-regex', pattern,
        '.',  # match every file (even empty files when unrestricted)
    ]
    if args.unrestricted:
        command.insert(-1, "--unrestricted")
    view.process = threaded_exec_shell(command, cwd=search_path, **line_proc)


def make_path_processor(view, pattern, ag_path, search_path, editor):

    def iter_path_lines(lines):
        br = "<br />"
        for line in lines:
            line = line.rstrip("\n")
            line = line.rstrip("\0")  # bug in ag adds null char to some lines?
            path = join(search_path, line)
            yield open_link(line, path) + br

    kw = make_line_processor(view, pattern, ag_path, search_path)
    kw["iter_output"] = iter_path_lines
    return kw
