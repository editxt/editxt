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
import os
import re
from functools import partial
from os.path import dirname, isdir, join, sep
from urllib.parse import quote

from editxt.command.base import command, CommandError
from editxt.command.parser import (CommandParser, Choice, File, Options,
    Regex, RegexPattern)
from editxt.command.util import has_editor, get_selection
from editxt.platform.markdown import markdown
from editxt.util import user_path

log = logging.getLogger(__name__)


def base_path(editor=None):
    if editor is None:
        return None
    path = editor.project.file_path
    if not path and editor.file_path and isdir(dirname(editor.file_path)):
        path = dirname(editor.file_path)
    return path


@command(arg_parser=CommandParser(
    Regex("path-pattern", default=get_selection),
    File("search-path", default=base_path),
    Choice(
        "open-single-match",
        "display-matched-paths",
        "open-first-match first",
        name="open"
    ),
), is_enabled=has_editor, hotkey="Command+Alt+p")
def pathfind(editor, args):
    """Find file by path"""
    if args is None and editor is not None:
        args = Options(
            path_pattern=get_selection(editor),
            search_path=base_path(editor),
            open="open-single-match",
        )
    if not (args and args.path_pattern):
        from editxt.commands import show_command_bar
        return show_command_bar(editor, "pathfind ")
    pattern = args.path_pattern
    search_path = args.search_path
    regex = re.compile(pattern, pattern.flags)
    if not search_path:
        return "please specify search path"
    paths = []
    for dirpath, dirnames, filenames in os.walk(search_path):
        for name in filenames:
            path = join(dirpath, name)
            if regex.search(path):
                paths.append(path)
    if len(paths) == 1 and args.open == "open-single-match":
        editor.project.window.open_paths(paths, focus=True)
    elif paths and args.open == "open-first-match":
        editor.project.window.open_paths(paths[:1], focus=True)
    elif paths:
        link = partial(path_link, editor=editor)
        message = markdown("\n".join(link(path) for path in paths), pre=True)
        editor.message(message)
    else:
        return "no match for pattern: {}".format(args.path_pattern)


def short_path(path, editor):
    project_path = editor.project.path
    if project_path and path.startswith(project_path + sep):
        return path[len(project_path) + 1:]
    return user_path(path)


def path_link(path, editor):
    return "[{rel}](xt://open/{path})".format(
        rel=short_path(path, editor),
        path=quote(path),
    )
