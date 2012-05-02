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
import logging
import nose
import nose.tools
import pdb
import os
import sys
from os.path import abspath, dirname

import editxt
import editxt.test
import editxt.test.mockerext as mockerext
from editxt.application import Application
from editxt.test.util import unittest_print_first_failures_last, \
    install_nose_tools_better_eq, install_pdb_trace_for_nose

log = logging.getLogger(__name__)


def run(argv=None):
    """run tests using nose

    one or more module names may be present in argv after the --test switch,
    which specifies that the tests for those modules should be run first. If
    there are errors in that set of tests then stop, otherwise run all tests.

    options
     --with-test-timer : print the ten slowest tests after the test run
     --test-all-on-pass : run all tests if specified tests pass
    """
    srcpath = dirname(dirname(abspath(editxt.__file__)))

    editxt.testing = True # for editxt.utils.untested
    unittest_print_first_failures_last()
    install_nose_tools_better_eq()
    install_pdb_trace_for_nose()
    mockerext.install()
    os.chdir(srcpath)

    if argv is None:
        argv = list(sys.argv)
    index = argv.index("--test")
    argv.remove("--test")
    testmods = set()
    while True:
        try:
            rawmod = mod = argv.pop(index)
        except IndexError:
            break
        if mod.startswith("-"):
            argv.insert(index, mod)
            break
        if mod.endswith(("__init__", "runner")):
            continue
        if mod.startswith("editxt.test."):
            pkg, name = mod.rsplit(".", 1)
            if not name.startswith("test_"):
                mod = pkg + ".test_" + name
        elif mod.startswith("editxt."):
            mod = ".test.test_".join(mod.rsplit(".", 1))
        else:
            continue
        path = os.path.join(srcpath, mod.replace(".", os.sep) + ".py")
        if os.path.exists(path):
            testmods.add(mod)
        else:
            log.warn("test module not found: %s", mod)
            argv.insert(index, rawmod)
            index += 1

    #augment_checks(testmods)
    plugins = [TestTimerPlugin()]

    testall = "--test-all-on-pass" in argv
    if testall:
        argv.remove("--test-all-on-pass")

    if testmods and len(testmods) < 4:
        testmods = sorted(testmods)
        sys.__stdout__.write("pre-testing modules: \n\t%s\n" % "\n\t".join(testmods))
        success = nose.run(argv=argv, defaultTest=testmods, addplugins=plugins)
        if not success or not testall:
            return success

        sys.stdout.write("\n")

    return nose.run(argv=argv, addplugins=plugins)


class TestApplication(Application):

    def __init__(self, argv):
        self.argv = argv
        super(TestApplication, self).__init__()

    def application_will_finish_launching(self, app, doc_ctrl):
        try:
            run(self.argv)
        finally:
            from AppKit import NSApp
            NSApp().terminate_(NSApp())

    def app_will_terminate(self, app):
        pass # do not call super, which saves document settings


skipdebug = [""]

def augment_checks(testmods):
    """temporary test augmentation to track down errors that only show up
    when tests were run in a nondeterministic order
    """
    def mods():
        import editxt.test.test_application as mod; yield mod
        import editxt.test.test_editor as mod; yield mod
        import editxt.test.test_project as mod; yield mod
        import editxt.test.test_document as mod; yield mod
    def wrap(test, mod):
        def func():
            def dc_test(when):
                from editxt.application import DocumentController
                dc = DocumentController.sharedDocumentController()

                global skipdebug
                if not skipdebug:
                    import pdb; pdb.set_trace()

                assert isinstance(dc, DocumentController), \
                    "shared document controller has wrong type %s %s.%s" \
                    % (when, mod.__name__, test.__name__)
                assert not dc.documents(), "(%s) %s.%s : %r" % \
                    (when, mod.__name__, test.__name__, dc.documents())
            dc_test("before")
            r = test()
            if r is not None:
                for t in r:
                    yield t
                yield dc_test, "after"
            else:
                dc_test("after")
        func.__name__ = test.__name__
        return func
    for mod in mods():
        log.debug("mod setup: %s", mod)
        for name in dir(mod):
            if name.startswith("test_"):
                setattr(mod, name, wrap(getattr(mod, name), mod))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Nose plugins
import time

class TestTimerPlugin(nose.plugins.Plugin):

    name = "test-timer"

    def configure(self, options, conf):
        super(TestTimerPlugin, self).configure(options, conf)
        self.results = []

    def beforeTest(self, test):
        self.start = time.clock()

    def afterTest(self, test):
        stop = time.clock()
        self.results.append((str(test), stop - self.start))
        del self.start

    def finalize(self, result):
        print "Ten slowest tests:"
        key = lambda it: it[1]
        for test, time in sorted(self.results, key=key, reverse=True)[:10]:
            print test, "...", time
