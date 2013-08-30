# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2012 Daniel Miller <millerdev@gmail.com>
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
from nose import with_setup
import nose.tools

from editxt.util import untested

log = logging.getLogger(__name__)


def todo_remove(obj):
    log.debug("TODO remove %r", obj)
    return obj

def unittest_print_first_failures_last():
    """monkeypatch unittest to print errors in reverse order
    which is more convenient for viewing in the console
    """
    import unittest
    old_printErrorList = unittest._TextTestResult.printErrorList
    def printErrorList(self, flavor, errors):
        return old_printErrorList(self, flavor, reversed(errors))
    unittest._TextTestResult.printErrorList = printErrorList

def eq_(a, b, text=None):
    if a != b:
        if isinstance(a, basestring):
            if text is None:
                text = "not equal"
            err = "%s\n%r\n%r" % (text, a, b)
        else:
            text = (str(text) + " : ") if text is not None else ""
            err = "%s%r != %r" % (text, a, b)
        raise AssertionError(err)

def install_nose_tools_better_eq():
    nose.tools.eq_ = eq_

def install_pdb_trace_for_nose():
    import pdb
    import sys
    def set_trace():
        """nose-compatible trace function
        
        uses default stdout, which is not consumed by nose
        """
        pdb.Pdb(stdout=sys.__stdout__).set_trace(sys._getframe().f_back)
    pdb.set_trace = set_trace


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
        nose.tools.eq_(rval, returns)

class TestConfig(object):
    def __init__(self, *args, **kw):
        self.__dict__.update(*args, **kw)
    def __iter__(self):
        return self.__dict__.iteritems()
    def __call__(self, **kw):
        return TestConfig(self.__dict__, **kw)
    def __contains__(self, name):
        return name in self.__dict__
    def __getitem__(self, name):
        return self.__dict__[name]
    def _get(self, name, default):
        return getattr(self, name, default)
    def __len__(self):
        return len(self.__dict__)
    def __repr__(self):
        val = ", ".join("%s=%r" % kv for kv in sorted(self.__dict__.items()))
        return "(%s)" % val

@contextmanager
def replattr(*args, **kw):
    sigchk = kw.pop('sigcheck', True)
    dict_replace = kw.pop('dict', False)
    if kw:
        raise ValueError('unrecognized keyword arguments: %s' % ', '.join(kw))
    if len(args) == 3 and isinstance(args[1], basestring):
        args = [args]
    errors = []
    temps = []
    for obj, attr, value in args:
        try:
            temp = obj[attr] if dict_replace else getattr(obj, attr)
            if sigchk and (inspect.isfunction(temp) or inspect.ismethod(temp)):
                as0 = inspect.getargspec(temp)
                as1 = inspect.getargspec(value)
                if as0 != as1:
                    errors.append("%s%s != %s%s" % (
                        temp.__name__, inspect.formatargspec(*as0),
                        value.__name__, inspect.formatargspec(*as1),
                    ))
            temps.append(temp)
            if dict_replace:
                obj[attr] = value
            else:
                setattr(obj, attr, value)
        except Exception, ex:
            rtype = 'key' if dict_replace else 'attribute'
            log.error("cannot replace %s: %s", rtype, attr, exc_info=True)
            errors.append(str(ex))
    try:
        yield
    finally:
        for (obj, attr, value), temp in zip(args, temps):
            if dict_replace:
                obj[attr] = temp
                if obj[attr] is not temp:
                    errors.append("%r is not %r" % (obj[attr], temp))
            else:
                setattr(obj, attr, temp)
                if getattr(obj, attr) is not temp:
                    errors.append("%r is not %r" % (getattr(obj, attr), temp))
    assert not errors, "\n".join(errors)


def assert_raises(*args, **kw):
    if len(args) == 1:
        msg = kw.pop('msg', None)
        if kw:
            raise AssertionError('invalid kwargs: {!r}'.format(kwargs))
        @contextmanager
        def raises():
            try:
                yield
                raise AssertionError('{} not raised'.format(args[0]))
            except args[0] as err:
                if isinstance(msg, basestring):
                    nose.tools.eq_(str(err), msg)
                elif hasattr(msg, 'search'):
                    assert msg.search(str(err)), \
                        '{!r} does not match {!r}'.foramt(msg.pattern, str(err))
                elif msg is not None:
                    msg(err)
        return raises()
    else:
        nose.tools.assert_raises(*args, **kw)


class CaptureLog(object):

    def __init__(self, module):
        self.log = module.log
        self.module = module
        self.data = defaultdict(list)

    def __getattr__(self, name):
        def log(message, *args, **kw):
            getattr(self.log, name)(message, *args, **kw)
            exc_info = kw.pop("exc_info", None)
            assert not kw, "unrecognized keyword args: {}".format(kw)
            if args:
                message = message % args
            if exc_info is not None:
                message += "\nexc_info = {!r}".format(exc_info)
            self.data[name].append(message)
        log.__name__ = name
        return log

    def __enter__(self):
        self.context = replattr(self.module, "log", self)
        self.context.__enter__()
        return self

    def __exit__(self, *args):
        self.context.__exit__(*args)


class Regex(object):

    def __init__(self, expression, *args, **kw):
        self.expr = re.compile(expression, *args, **kw)
        self.expression = expression

    def __repr__(self):
        return "Regex({!r})".format(self.expression)

    def __str__(self):
        return self.expression

    def __eq__(self, other):
        return self.expr.search(other)

    def __ne__(self, other):
        return not self.__eq__(other)


def check_app_state(test):
    def checker(when):
        def check_app_state():
            from editxt.application import DocumentController
            dc = DocumentController.sharedDocumentController()
            assert not dc.documents(), "app state was dirty %s %s: %r" \
                % (when, test.__name__, dc.documents())
        return check_app_state
    return with_setup(checker("before"), checker("after"))(test)

def profile(test, *args):
    import cProfile
    import sys
    def prof_test(test=test, args=args):
        stdout = sys.stdout
        sys.stdout = sys.__stdout__
        try:
            print "\n%s%r" % (test.__name__, args)
            cProfile.runctx("test(*args)", {}, dict(test=test, args=args))
        finally:
            sys.stdout = stdout
    return (prof_test, test, args)


@contextmanager
def tempdir(*args, **kw):
    delete = kw.pop("delete", True)
    path = tempfile.mkdtemp(*args, **kw)
    try:
        yield path
    finally:
        if delete and os.path.exists(path):
            shutil.rmtree(path)
