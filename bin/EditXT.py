#!/usr/local/bin/python
# encoding: utf-8
# 
# Quicksilver action to open files with EditXT
# 
# place this script in ~/Library/Application Support/Quicksilver/Actions/
# then restart Quicksilver

import os
import subprocess
import sys
import traceback

EDITXT = "/Users/Shared/Applications/EditXT.app"

def main(argv=None):
    try:
        if argv is None:
            argv = sys.argv
        files = []
        if argv and len(argv) > 1:
            for filename in argv[1:]:
                try:
                    if os.path.isfile(filename):
                        files.append(filename)
                    elif not os.path.exists(filename):
                        print("file not found: " + filename)
                    else:
                        print("refusing to edit: " + filename)
                except Exception:
                    print("cannot edit: " + filename)
                    print(traceback.format_exc())
        if files:
            subprocess.call(["open", "-a", EDITXT] + files)
        else:
            print("EditXT edits files")
    except Exception:
        print("EditXT action failed!\n" + traceback.format_exc())

if __name__ == "__main__":
    sys.exit(main())
