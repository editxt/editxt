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
from __future__ import print_function
import glob,os,stat,time
import nose
import subprocess
import sys
import threading
from datetime import datetime
from nose.tools import nottest

try:
    import fsevents
except ImportError:
    fsevents = None

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

def polling_fs_runner(root, callback, rate=2):
    status = {}
    val=0
    try:
        while True:
            testfiles = list(check(root, status))
            if testfiles:
                callback(testfiles)
            time.sleep(rate)
    except KeyboardInterrupt:
        pass

def mac_fs_events_runner(root, callback):
    monitor_mask = (
        fsevents.IN_MODIFY |
        fsevents.IN_CREATE |
        fsevents.IN_DELETE |
        fsevents.IN_MOVED_FROM |
        fsevents.IN_MOVED_TO
    )
    def set_callback_event(event):
        if event.mask & monitor_mask and event.name.endswith(CHECK_EXTS):
            files.append(event.name)
            callback_event.set()
    files = []
    callback_event = threading.Event()
    stream = fsevents.Stream(set_callback_event, root, file_events=True)
    observer = fsevents.Observer()
    observer.schedule(stream)
    observer.start()
    callback_event.set() # set initially to invoke callback immediately
    try:
        while True:
            if callback_event.wait(5):
                callback_event.clear()
                testfiles, files = files, []
                callback(testfiles)
    except:
        observer.unschedule(stream)
        observer.stop()
        observer.join()

@nottest
def make_test_callback(srcpath):
    def run_tests(testfiles):
        testmods = list(modulize(testfiles, srcpath))
        set_title('testing...')
        testmods.append("--test-all-on-pass")
        print("\n" + "#" * 70)
        result = subprocess.call(sys.argv + testmods)
        set_title('FAIL' if result else 'OK')
        print(datetime.now().strftime("%m/%d/%Y %H:%M:%S").rjust(70) + " ")
        sys.stdout.flush()
    return run_tests

def start(root=None, wait=2):
    if root is None:
        root = os.getcwd()
    srcpath = root + os.sep
    assert os.path.exists(srcpath), srcpath

    if fsevents is not None:
        print('using MacFSEvents to watch %s' % root)
        test_runner = mac_fs_events_runner
    else:
        print('using (slow) polling test runner to watch %s' % root)
        test_runner = polling_fs_runner
    run_tests = make_test_callback(srcpath)
    try:
        test_runner(root, run_tests)
    finally:
        set_title('')
        print()

if __name__ == "__main__":
    start()
