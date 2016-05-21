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
import os
import platform
import sys
import traceback
from subprocess import check_output, CalledProcessError

import objc
from AppKit import NSObject
from ExceptionHandling import NSExceptionHandler, NSStackTraceKey
from ExceptionHandling import NSLogAndHandleEveryExceptionMask as DEFAULTMASK
from PyObjCTools.Debugging import isPythonException, LOGSTACKTRACE

from editxt import log

is_debugging = False


def log_python_exception(exception):
    userInfo = exception.userInfo()
    try:
        tb = userInfo['__pyobjc_exc_traceback__']
    except KeyError:
        tb = userInfo['__pyobjc_exc_value__'].__traceback__
    log.error('Python exception discarded\n' +
        ''.join(traceback.format_exception(
            userInfo['__pyobjc_exc_type__'],
            userInfo['__pyobjc_exc_value__'],
            tb)))
    if tb is None and NSStackTraceKey in userInfo:
        return log_objc_exception(exception)
    # we logged it, so don't log it for us
    return False


def log_objc_exception(exception):
    stack = get_objc_traceback(exception)
    stack = "\n{}".format(stack) if stack else ""
    log.error("ObjC exception discarded: %s: %s%s",
        exception.name(), exception.reason(), stack)
    return False  # tell pyobjc not to log exception


def get_objc_traceback(exception, cache={}):
    def symbolize(pid, stack, atos=['/usr/bin/atos', '-p']):
        return (
            "Use this command while process {} is running "
            "to symbolize Objective-C stack trace: {}"
        ).format(pid, " ".join(atos + [str(pid)] + stack.split()))
    userInfo = exception.userInfo()
    stack = userInfo.get(NSStackTraceKey)
    return symbolize(os.getpid(), stack) if stack else None


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
            log.exception("Error in exception handler")
            sys.stderr.write("Error in exception handler\n")
            sys.stderr.write(traceback.format_exc())
            return bool(self.verbosity & LOGSTACKTRACE)

    @objc.typedSelector(b'c@:@@I')
    def exceptionHandler_shouldHandleException_mask_(self, sender, exception, aMask):
        return False

def install_exception_handler(verbosity=LOGSTACKTRACE, mask=DEFAULTMASK):
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
