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
import logging
from AppKit import NSTextStorage, NSDocument, NSChangeDone, NSChangeCleared

import editxt.constants as const
from editxt import log as root_log
from editxt.platform.text import Text
from editxt.util import WeakProperty

log = logging.getLogger(__name__)


class ErrorLog(object):
    """Error log controller
    
    Implements the portion of the file protocol needed by
    ``logging.StreamHandler``. Manages a document that can
    be opened by the application.
    """

    app = WeakProperty()

    def __init__(self, app):
        self.app = app
        self.text = Text()
        self._document = None
    
    @property
    def document(self):
        if self._document is None:
            def close():
                self._document = None
            self._document = doc = create_error_log_document(self.app, close)
            doc.text_storage = self.text
            doc.file_path = const.LOG_NAME
        return self._document
    
    def write(self, value):
        range = (self.text.length(), 0)
        # HACK str(value) because objc.pyobjc_unicode -> EXC_BAD_ACCESS
        self.text.replaceCharactersInRange_withString_(range, str(value))
        if self._document is not None:
            self._document.clear_dirty()

    def flush(self):
        pass

    @staticmethod
    def unexpected_error():
        """error handler function for objc.AppHelper.runEventLoop"""
        root_log.error("unexpected error", exc_info=True)
        return True


class LogViewHandler(logging.StreamHandler):
    """A logging handler that opens the error log in its app on error
    """

    app = WeakProperty()

    def __init__(self, app, **kw):
        super().__init__(stream=app.errlog, **kw)
        self.app = app

    def emit(self, record):
        try:
            return super().emit(record)
        finally:
            if record.levelno > logging.WARNING:
                if self.app.launching:
                    self.app.launch_fault = True
                else:
                    try:
                        self.app.open_error_log(set_current=False)
                    except Exception:
                        log.warn("cannot open error log", exc_info=True)


def create_error_log_document(app, closefunc):
    """create an error document"""
    from editxt.document import TextDocument
    if "ErrorLogDocument" not in globals():
        global ErrorLogDocument # HACK TODO create app-specific class
        class ErrorLogDocument(TextDocument):
            def check_for_external_changes(self, window):
                self.clear_dirty()
            def update_syntaxer(self):
                # optimization work-around: color on set_main_view_of_window
                self.syntax_needs_color = True
                super().update_syntaxer()
            def on_text_edit(self, range):
                # optimization: do not update syntax color on edit text
                pass
            def close(self):
                closefunc()
                super(ErrorLogDocument, self).close()
    document = ErrorLogDocument(app)
    return document
