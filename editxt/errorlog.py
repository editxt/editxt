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
from AppKit import NSTextStorage, NSDocument, NSChangeDone, NSChangeCleared

import editxt.constants as const

log = logging.getLogger(__name__)

_log = None

class ErrorLog(object):
    """Error log controller
    
    implements the portion of the file protocol needed by logging.StreamHandler
    """

    def __init__(self):
        self.text = NSTextStorage.alloc().initWithString_attributes_(u"", {})
        self._document = None
    
    @property
    def document(self):
        if self._document is None:
            def close():
                self._document = None
            self._document = doc = create_error_log_document(close)
            doc.text_storage = self.text
            doc.setLastComponentOfFileName_(const.LOG_NAME)
            doc.setHasUndoManager_(False)
        return self._document
    
    def write(self, value):
        range = (self.text.length(), 0)
        self.text.replaceCharactersInRange_withString_(range, value)
        if self._document is not None:
            self._document.updateChangeCount_(NSChangeDone)

    def flush(self):
        pass

    @staticmethod
    def unexpected_error():
        """error handler function for objc.AppHelper.runEventLoop"""
        from editxt import app
        log.error("unexpected error", exc_info=True)
        try:
            app.open_error_log(set_current=False)
        except Exception:
            log.error("cannot open error log", exc_info=True)
        return True

def create_error_log_document(closefunc):
    """create an error document
    
    This must be called after editxt.app is installed so editxt.document can be
    imported (editxt.document imports app from editxt).
    """
    from editxt.document import TextDocument
    if "ErrorLogDocument" not in globals():
        global ErrorLogDocument
        class ErrorLogDocument(TextDocument):
            def addWindowController_(self, value):
                self.updateChangeCount_(NSChangeCleared)
                super(ErrorLogDocument, self).addWindowController_(value)
            def close(self):
                closefunc()
                super(ErrorLogDocument, self).close()
    return ErrorLogDocument.alloc().init()

errlog = ErrorLog()
