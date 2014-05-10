# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2013 Daniel Miller <millerdev@gmail.com>
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
from __future__ import absolute_import

import inspect
import logging
import os
import re
import shutil
import tempfile
from collections import defaultdict
from contextlib import contextmanager
from functools import wraps
from nose import with_setup
import nose.tools

from editxt.util import untested

try:
    basestring
except NameError:
    basestring = str

log = logging.getLogger(__name__)


def todo_remove(obj):
    log.debug("TODO remove %r", obj)
    return obj

from testil import (
    unittest_print_first_failures_last,
    eq_,
    Config as TestConfig,
    replattr,
    assert_raises,
    CaptureLogging as CaptureLog,
    Regex,
    tempdir,
    patch_nose_tools,
)

patch_nose_tools()


def do_method_pass_through(attr, inner_obj_class, outer_obj, token, method,
        ext_args=(), int_args=None, returns=None):
    from mocker import Mocker # late import so mockerext is installed
    def inject_wc(args):
        return [(outer_obj if a is token else a) for a in args]
    if int_args is None:
        int_args = ext_args
    ext_args = inject_wc(ext_args)
    int_args = inject_wc(int_args)
    m = Mocker()
    if isinstance(method, basestring):
        method = (method, method)
    outer_method, inner_method = method
    inner_obj = m.replace(outer_obj, attr, spec=inner_obj_class)
    setattr(outer_obj, attr, inner_obj)
    getattr(inner_obj, inner_method)(*int_args) >> returns
    with m:
        rval = getattr(outer_obj, outer_method)(*ext_args)
        eq_(rval, returns)


@nose.tools.nottest
class test_app(object):
    """A context manager that creates an Application object for testing purposes

    :param config: A string with details about the app configuration.
    The string is a space-delimited list of the following names:

        window project editor

    These names can be used to pre-configure the application with
    windows, projects, and editors to minimize the amount of setup
    needed in the test. Editors can be suffixed with parens containing a
    name to configure multiple views of the same document. For example:

        window
            project
                editor(doc1)
                editor
            project
                editor(doc1)

    In this case the first and third editor are editing the same
    document. By default each unnamed editor will contain a new,
    untitled document.

    A window or project omitted from the config is implied since it is
    not possible to have an editor without a project or a project
    without a window. For example, the following two configs result in
    identical configurations:

        window project editor

        editor

    Usage:

        with test_app("window project editor") as app:
            ...
            eq_(test_app.config(app), "<expected config>")

    Alternate usage:

        @test_app
        def test(app, other, args):
            ...
        test("other", "args")

    """

    editor_re = re.compile("(-?)(window|project|editor)((?:\([a-zA-Z0-9-]+\))?)(\*?)$")

    def __new__(cls, config=None):
        self = super(test_app, cls).__new__(cls)
        if callable(config):
            self.__init__()
            return self(config)
        return self

    def __init__(self, config=None):
        self.config = config

    def __call__(self, func):
        @wraps(func)
        def decorator(*args, **kw):
            with self as app:
                return func(app, *args, **kw)
        return decorator

    def __enter__(self):
        from editxt.application import Application
        self.tempdir = tempdir()
        app = Application(self.tempdir.__enter__())
        self.items = {}
        self.news = 0
        self._setup(app)
        app.__test_app = self
        self.app = app
        return app

    def __exit__(self, exc_type, exc_value, tb):
        self.tempdir.__exit__(exc_type, exc_value, tb)
        for document in self.app.documents:
            document.close()
        assert not self.app.documents, list(self.app.documents)
        del self.app

    @classmethod
    def self(cls, app):
        return app.__test_app

    def _setup(self, app):
        from editxt.editor import Editor
        from editxt.project import Project
        from editxt.window import Window
        config = self.config
        docs_by_name = {}
        items = self.items
        if config is None:
            return
        window = project = None
        for i, item in enumerate(config.split()):
            match = self.editor_re.match(item)
            assert match and (
                    match.group(2) == "project" or not match.group(1)
                ), "unknown config item: {}".format(item)
            collapsed, item, name, current = match.groups()
            if not name:
                name = "<{}>".format(i)
            if item == "window" or window is None:
                window = Window(app)
                project = None
                app.windows.append(window)
                if item == "window":
                    items[window] = "window" + name
                    continue
                else:
                    items[window] = "window<{}>".format(i)
            if item == "project" or project is None:
                project = Project(window)
                if collapsed:
                    project.expanded = False
                window.projects.append(project)
                if item == "project":
                    items[project] = "project" + name
                    if current:
                        window.current_editor = project
                    continue
                else:
                    items[project] = "project<{}>".format(i)
            document = docs_by_name.get(name)
            if document is None:
                document = app.document_with_path(None)
                docs_by_name[name] = document
            editor = Editor(project, document=document)
            items[editor] = "editor" + name
            items[document] = "document" + name
            project.editors.append(editor)
            if current:
                window.current_editor = editor

    @classmethod
    def config(cls, app):
        """Get a string representing the app window/project/editor/document config

        Documents that were created after the app was initialized are
        delimited with square brackets rather than parens. For example:

            window project editor[Untitled 0]

        Documents not associated with any window (this is a bug) are listed
        at the end of the config string after a pipe (|) character. Example:

            window project editor | editor[Untitled 0]
        """
        name_re = re.compile("(window|project|editor)<")
        def iter_items(app):
            def name(item):
                name = cls.name(item, app)
                match = name_re.match(name)
                return match.group(1) if match else name
            seen = set()
            for window in app.windows:
                yield name(window)
                current = window.current_editor
                for project in window.projects:
                    star = "*" if project is current else ""
                    collapsed = "" if project.expanded else "-"
                    yield collapsed + name(project) + star
                    for editor in project.editors:
                        star = "*" if editor is current else ""
                        yield name(editor) + star
                        seen.add(editor.document)
            documents = set(app.documents) - seen
            if documents:
                # documents not associated with any window (should not get here)
                yield "|"
                for document in documents:
                    yield cls.name(document, app)
        return " ".join(iter_items(app))

    @classmethod
    def name(cls, item, app):
        """Get the name of a window, project, or editor/document"""
        from editxt.document import TextDocument
        from editxt.editor import Editor
        from editxt.project import Project
        from editxt.window import Window
        self = cls.self(app)
        name = self.items.get(item)
        if name is None:
            if isinstance(item, (Window, Project)):
                name = "[{}]".format(self.news)
            else:
                name = "[{} {}]".format(item.name, self.news)
            ident = name
            prefix = "document" if isinstance(item, TextDocument) \
                                else type(item).__name__.lower()
            name = prefix + name
            self.news += 1
            self.items[item] = name
            if isinstance(item, Editor):
                self.items[item.document] = "document" + ident
        return name

    @classmethod
    def get(cls, name, app):
        """Get the item for the given name

        :param name: The name of the item to get. Example: ``"editor(1)"``
        """
        self = cls.self(app)
        items_by_name = {v: k for k, v in self.items.items()}
        print(items_by_name)
        return items_by_name[name]


def check_app_state(test):
    def checker(when):
        def check_app_state():
            import editxt
            assert not hasattr(editxt, "app"), editxt.app
        return check_app_state
    return with_setup(checker("before"), checker("after"))(test)


def profile(test, *args):
    import cProfile
    import sys
    def prof_test(test=test, args=args):
        stdout = sys.stdout
        sys.stdout = sys.__stdout__
        try:
            print("\n%s%r" % (test.__name__, args))
            cProfile.runctx("test(*args)", {}, dict(test=test, args=args))
        finally:
            sys.stdout = stdout
    return (prof_test, test, args)
