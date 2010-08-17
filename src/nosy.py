# By Jeff Winkler, http://jeffwinkler.net
# Adapted for EditXT by Daniel Miller
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
import glob,os,stat,time
import subprocess
import sys

import nose

from datetime import datetime

CHECK_EXTS = (".py",) # ".nib")

def check(root, status):
    """recursively check for changes in root, yielding each changed file path"""
    for dirpath, dirnames, filenames in os.walk(root):
        for filename in (n for n in filenames if n.endswith(CHECK_EXTS)):
            filepath = os.path.join(dirpath, filename)
            stats = os.stat(filepath)
            fstat = stats[stat.ST_SIZE] + stats[stat.ST_MTIME]
            if status.get(filepath) != fstat:
                status[filepath] = fstat
                yield filepath

def modulize(paths, relto):
    rlen = len(relto)
    for path in paths:
        yield path[rlen:-3].replace(os.sep, ".")

def set_title(value):
    sys.stdout.write('\033]0;%s\007' % value)

def start(root=None, wait=2):
    status = {}
    if root is None:
        root = os.getcwd()
    srcpath = root + os.sep
    assert os.path.exists(srcpath)
    val=0
    try:
        while (True):
            testmods = list(modulize(check(root, status), srcpath))
            if testmods:
                set_title('testing...')
                testmods.append("--test-all-on-pass")
                print "\n" + "#" * 70
                result = subprocess.call(sys.argv + testmods)
                set_title('FAIL' if result else 'OK')
                print datetime.now().strftime("%m/%d/%Y %H:%M:%S").rjust(70), " ",
                sys.stdout.flush()
            time.sleep(wait)
    finally:
        set_title('')

if __name__ == "__main__":
    start()
