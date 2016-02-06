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
from os.path import isabs, realpath, samefile

import AppKit as ak


class FileRef:
    """A persistent file reference

    A `FileRef` for an absolute path usually remains valid even if the
    target file's path changes on disk (e.g., if the file is moved).
    """

    def __init__(self, path):
        self.path = path

    @property
    def path(self):
        if self.url is None:
            path = None
        else:
            assert self.url.isFileURL(), self.url.absoluteString()
            path = self.url.path()
        if path is None:
            path = self.original_path
        elif path != self.original_path:
            try:
                if samefile(path, self.original_path):
                    path = self.original_path
            except FileNotFoundError:
                pass
        return path
    @path.setter
    def path(self, path):
        self.original_path = path
        if isabs(path):
            self.url = ak.NSURL.fileURLWithPath_(path).fileReferenceURL()
        else:
            self.url = None
