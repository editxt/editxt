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
import re
import time
from collections import namedtuple
from os.path import dirname, isabs, isdir, join, sep
from subprocess import check_output, CalledProcessError

from editxt.command.base import command, CommandError
from editxt.command.parser import CommandParser, DynamicList, String
from editxt.platform.markdown import html_string

_cache = None
log = logging.getLogger(__name__)
GitInfo = namedtuple("GitInfo", "git_dir remotes expires file_path")
DEFAULT_GIT_INFO = GitInfo(None, [], None, None)
NEWLINE_CHARS = '\n\r\u2028\u2029'


class Remote(namedtuple("Remote", "name user repo")):

    def __str__(self):
        return self.name


def get_git_info(editor=None):
    global _cache
    if not (editor and editor.file_path):
        return DEFAULT_GIT_INFO
    if (_cache is None or _cache.expires < time.time() or
            not editor.file_path.startswith(_cache.git_dir[:-len(".git")])):
        git_dir = get_git_dir(editor.file_path)
        if not git_dir:
            return DEFAULT_GIT_INFO
        remotes = get_remotes(git_dir)
        _cache = GitInfo(git_dir, remotes, time.time() + 60, editor.file_path)
        log.debug('update cache: %s', _cache)
    return _cache


def get_git_dir(path):
    if path and isabs(path):
        last = None
        while last != path:
            last = path
            path = dirname(path)
            if isdir(join(path, ".git")):
                return path
    return None


def git_relative_path(file_path, git_info):
    git_dir = git_info.git_dir
    assert file_path.startswith(git_dir + sep), (file_path, git_info)
    if git_dir == sep:
        git_dir = ""
    return file_path[len(git_dir) + 1:]


def get_remotes(git_dir):

    def remote_info(line, seen=set()):
        name, url, ignore = line.split()
        info = re.search("github.com[:/]([^/]+)/(.+)\.git", url)
        if info:
            user, repo = info.group(1, 2)
        else:
            user = repo = None
        if name in seen:
            return Remote(None, None, None)
        seen.add(name)
        return Remote(name, user, repo)

    def remote_key(info):
        return (0 if info.name == "origin" else 1), info.name

    try:
        output = check_output(
            "git remote -v".split(),
            cwd=git_dir,
            universal_newlines=True,
        )
    except CalledProcessError:
        return []
    remotes = (remote_info(r) for r in output.split("\n") if r.split())
    remotes = (r for r in remotes if r.user)
    remotes = sorted(remotes, key=remote_key)
    return remotes


def rev_parse(git_dir, opts=""):
    return check_output(
        "git rev-parse {} HEAD".format(opts).split(),
        cwd=git_dir,
        universal_newlines=True,
    ).strip()


def default_remote(editor=None):
    info = get_git_info(editor)
    return info.remotes[0] if info.remotes else None


def get_selected_lines(editor=None):
    if editor and editor.selection:
        index, length = editor.selection
        first = editor.line_numbers[index]
        lines = str(first)
        if length:
            text = editor.document.text_storage
            while length and text[index + length - 1] in NEWLINE_CHARS:
                length -= 1
            last = editor.line_numbers[index + length]
            if last != first:
                lines += ":{}".format(last)
        return lines
    return ""


def has_file_path(editor=None):
    return bool(editor and editor.file_path)


@command(arg_parser=CommandParser(
    String("lines", default=get_selected_lines),
    DynamicList(
        "remote",
        get_items=(lambda editor=None: get_git_info(editor).remotes),
        name_attribute="name",
        default=default_remote,
    ),
), is_enabled=has_file_path, name="github-url")
def github_url(editor, args):
    """Get GitHub URL"""
    if not args:
        from editxt.commands import show_command_bar
        return show_command_bar(editor, "github-url ")
    if not (editor and editor.file_path):
        raise CommandError("cannot get github URL without path")
    if not args.remote:
        raise CommandError("cannot get github URL without remote name")
    info = get_git_info(editor)
    rev = rev_parse(info.git_dir, "--abbrev-ref")
    if rev == "HEAD":
        rev = rev_parse(info.git_dir)
    lines = get_selected_lines(editor)
    if lines:
        if ":" in lines:
            lines = lines.replace(":", "-L")
        lines = "#L" + lines
    link = "https://github.com/{user}/{repo}/blob/{rev}/{path}{line}".format(
        user=args.remote.user,
        repo=args.remote.repo,
        rev=rev,
        path=git_relative_path(editor.file_path, info),
        line=lines,
    )
    editor.message(html_string("<a href='{0}'>{0}</a>".format(link)))
