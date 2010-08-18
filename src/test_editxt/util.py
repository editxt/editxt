# -*- coding: utf-8 -*-
# EditXT
# Copyright (c) 2007-2010 Daniel Miller <millerdev@gmail.com>
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
from __future__ import with_statement

import inspect
import logging
from contextlib import contextmanager
from mocker import Mocker
from nose import with_setup
import nose.tools

from editxt.util import untested

log = logging.getLogger("test_editxt.util")


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

def install_nose_tools_better_eq():
    def better_eq(a, b, text=None):
        if a != b:
            if isinstance(a, basestring):
                if text is None:
                    text = "not equal"
                err = "%s\n%r\n%r" % (text, a, b)
            else:
                text = (str(text) + " : ") if text is not None else ""
                err = "%s%r != %r" % (text, a, b)
            raise AssertionError(err)
    nose.tools.eq_ = better_eq

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
    inner_obj = m.replace(getattr(outer_obj, attr), inner_obj_class, passthrough=False)
    setattr(outer_obj, attr, inner_obj)
    getattr(inner_obj, inner_method)(*int_args) >> returns
    with m:
        rval = getattr(outer_obj, outer_method)(*ext_args)
        nose.tools.eq_(rval, returns)

class TestConfig(object):
    def __init__(self, *args, **kw):
        self.__dict__["_TestConfig__data"] = dict(*args, **kw)
    def __iter__(self):
        return self.__data.iteritems()
    def __call__(self, *args, **kw):
        new = TestConfig(self.__data)
        new.__data.update(*args, **kw)
        return new
    def __contains__(self, name):
        return name in self.__data
    def __getattr__(self, name):
        try:
            return self.__data[name]
        except KeyError:
            raise AttributeError(name)
    def __getitem__(self, name):
        return self.__data[name]
    def _get(self, name, default):
        return self.__data.get(name, default)
    def __len__(self):
        return len(self.__data)
    def __setattr__(self, name, value):
        self.__data[name] = value
    def __repr__(self):
        val = ", ".join("%s=%r" % (k, v) for k, v in sorted(self.__data.items()))
        return "(%s)" % val

@contextmanager
def replattr(*args):
    if len(args) == 3 and isinstance(args[1], basestring):
        args = [args]
    errors = []
    temps = []
    for obj, attr, value in args:
        try:
            temp = getattr(obj, attr)
            if (inspect.isfunction(temp) or inspect.ismethod(temp)):
                as0 = inspect.getargspec(temp)
                as1 = inspect.getargspec(value)
                if as0 != as1:
                    errors.append("%s%s != %s%s" % (
                        temp.__name__, inspect.formatargspec(*as0),
                        value.__name__, inspect.formatargspec(*as1),
                    ))
            temps.append(temp)
            setattr(obj, attr, value)
        except Exception, ex:
            log.error("cannot replace attribute: %s", attr, exc_info=True)
            errors.append(str(ex))
    try:
        yield
    finally:
        for (obj, attr, value), temp in zip(args, temps):
            setattr(obj, attr, temp)
            if getattr(obj, attr) is not temp:
                errors.append("%r is not %r" % (getattr(obj, attr), temp))
    assert not errors, "\n".join(errors)

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

