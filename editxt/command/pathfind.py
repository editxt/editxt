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
from fnmatch import fnmatch
from functools import partial
from os.path import basename, dirname, isdir, join, sep
from urllib.parse import quote

import editxt.config as config
from editxt.command.base import command, CommandError
from editxt.command.parser import (CommandParser, Choice, File, Options,
    Regex, RegexPattern)
from editxt.command.util import has_editor, get_selection
from editxt.platform.markdown import markdown
from editxt.util import short_path

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
            "open-single-match",
            "display-matched-paths",
            "open-first-match first",
            "all-matched-paths",  # do not hide pathfind.exclude_patterns
            name="open"
        ),
    ),
    config={"exclude_patterns": config.List(["*.pyc", ".git", ".svn", ".hg"])},
    is_enabled=has_editor, hotkey="Command+Alt+p"
)
def pathfind(editor, args):
    """Find file by path"""
    if args is None and editor is not None:
        args = Options(
            path_pattern=get_selection_regex(editor),
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
    exclude = editor.app.config.for_command("pathfind")["exclude_patterns"]
    if args.open == "all-matched-paths":
        is_excluded = lambda path: False
    else:
        excluders = [make_matcher(pattern) for pattern in exclude]
        def is_excluded(path):
            filename = basename(path)
            return any(x(filename) for x in excluders)
    for dirpath, dirnames, filenames in os.walk(search_path):
        if is_excluded(dirpath):
            continue
        for name in filenames:
            path = join(dirpath, name)
            if regex.search(path) and not is_excluded(path):
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


def path_link(path, editor):
    return "[{rel}](xt://open/{path})".format(
        rel=short_path(path, editor),
        path=quote(path),
    )


def make_matcher(pattern):
    if is_literal(pattern):
        return lambda value: value == pattern
    if pattern.startswith("*") and is_literal(pattern[1:]):
        tail = pattern[1:]
        return lambda value: value.endswith(tail)
    if pattern.endswith("*") and is_literal(pattern[:-1]):
        head = pattern[:-1]
        return lambda value: value.startswith(head)
    return partial(fnmatch, pattern=pattern)


def is_literal(pattern):
    return not any(char in pattern for char in "*?[")
