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
import os
import sys
import traceback

import objc
from AppKit import NSObject
from ExceptionHandling import NSExceptionHandler, NSStackTraceKey
from PyObjCTools.Debugging import (isPythonException,
    DEFAULTVERBOSITY, DEFAULTMASK, LOGSTACKTRACE)

log = logging.getLogger(__name__)


def log_python_exception(exception):
    userInfo = exception.userInfo()
    log.error('*** Python exception discarded!\n' +
        ''.join(traceback.format_exception(
            userInfo['__pyobjc_exc_type__'],
            userInfo['__pyobjc_exc_value__'],
            userInfo['__pyobjc_exc_traceback__'])))
    # we logged it, so don't log it for us
    return False


def log_objc_exception(exception):
    userInfo = exception.userInfo()
    stack = userInfo.get(NSStackTraceKey)
    if not stack or not os.path.exists('/usr/bin/atos'):
        return True
    pipe = os.popen('/usr/bin/atos -p %d %s' % (os.getpid(), stack))
    stacktrace = pipe.readlines()
    stacktrace.reverse()
    stack = ''.join([('  '+line) for line in stacktrace])
    log.error("ObjC exception %s (reason: %s) discarded\n"
        "Stack trace (most recent call last):\n%s",
        exception.name(), exception.reason(), stack)
    # we logged it, so don't log it for us
    return False


class DebuggingDelegate(NSObject):
    verbosity = objc.ivar('verbosity', b'i')

    def initWithVerbosity_(self, verbosity):
        self = self.init()
        self.verbosity = verbosity
        return self

    @objc.typedSelector(b'c@:@@I')
    def exceptionHandler_shouldLogException_mask_(self, sender, exception, aMask):
        try:
            if isPythonException(exception):
                return log_python_exception(exception)
            elif self.verbosity & LOGSTACKTRACE:
                return log_objc_exception(exception)
            else:
                return False # don't log it for us
        except:
            print("*** Exception occurred during exception handler ***",
                    file=sys.stderr)
            traceback.print_exc(sys.stderr)
            return True

    @objc.typedSelector(b'c@:@@I')
    def exceptionHandler_shouldHandleException_mask_(self, sender, exception, aMask):
        return False

def install_exception_handler(verbosity=DEFAULTVERBOSITY, mask=DEFAULTMASK):
    """
    Install the exception handling delegate that will log every exception
    matching the given mask with the given verbosity.
    """
    if _installed:
        return
    delegate = DebuggingDelegate.alloc().initWithVerbosity_(verbosity)
    NSExceptionHandler.defaultExceptionHandler().setExceptionHandlingMask_(mask)
    NSExceptionHandler.defaultExceptionHandler().setDelegate_(delegate)
    # we need to retain this, because the handler doesn't
    _installed.append(delegate)

_installed = []
