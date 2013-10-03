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
import glob
import os
import shutil
import sys

from datetime import datetime
from setuptools import setup
from subprocess import Popen, PIPE

if hasattr(sys, 'real_prefix'):
    # HACK fixes for py2app + virtualenv
    if sys.prefix.endswith("/.."):
        sys.prefix = os.path.normpath(sys.prefix)
    if sys.exec_prefix.endswith("/.."):
        sys.exec_prefix = os.path.normpath(sys.exec_prefix)

import py2app

from editxt import __version__ as version
revision = datetime.now().strftime("%Y%m%d")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# handle -A switch (dev build)
if "-A" in sys.argv:
    dev = True
    appname = "EditXTDev"
else:
    dev = False
    appname = "EditXT"

package = ('--package' in sys.argv)
if package:
    assert not dev, 'cannot package dev build'
    sys.argv.remove('--package')

# get git revision information
def proc_out(cmd):
    proc = Popen(cmd, stdout=PIPE, close_fds=True)
    for line in proc.stdout:
        yield line.decode("utf8") # HACK
gitrev = next(proc_out(["git", "rev-parse", "HEAD"]))[:7]
changes = 0
for line in proc_out(["git", "status"]):
    if line.startswith("# Changed but not updated"):
        changes += 1
    if line.startswith("# Changes to be committed"):
        changes += 1
if changes:
    gitrev += "+"
    if not dev:
        response = input("Build with uncommitted changes? [Y/n] ").strip()
        if response and response.lower() not in ["y", "yes"]:
            print("aborted.")
            sys.exit()
print("building %s %s %s.%s" % (appname, version, revision, gitrev))

# remove old build
if "--noclean" in sys.argv:
    sys.argv.remove("--noclean")
else:
    def rmtree(path):
        print("removing", path)
        if os.path.exists(path):
            shutil.rmtree(path)
    thisdir = os.path.dirname(os.path.abspath(__file__))
    rmtree(os.path.join(thisdir, "build"))
    rmtree(os.path.join(thisdir, "dist", appname + ".app"))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
setup(
    name=appname,
    app=['boot.py'],
    version=version,
    options=dict(py2app=dict(
        # argv_emulation causes the app to launch in a strange mode that does
        # not play nicely with Exposé (the window does not come to the front
        # when switching to EditXT with Exposé). Luckily everything seems to
        # work as expected without it!!
        argv_emulation=True,
        packages=["editxt"],
        #frameworks=["lib/Frameworks/NDAlias.framework"],
        plist=dict(
            CFBundleGetInfoString = "%s %s.%s" % (version, revision, gitrev),
            CFBundleShortVersionString = version,
            CFBundleVersion = revision + "." + gitrev,
            NSHumanReadableCopyright = '© 2012 Daniel Miller',
            CFBundleIdentifier = "org.editxt." + appname,
            CFBundleIconFile = "PythonApplet.icns",
            CFBundleDocumentTypes = [
                dict(
                    CFBundleTypeName="All Documents",
                    CFBundleTypeRole="Editor",
                    NSDocumentClass="TextDocument",
                    LSHandlerRank="Alternate",
                    LSIsAppleDefaultForType=False,
                    LSItemContentTypes=["public.data"],
                    LSTypeIsPackage=False,
                    CFBundleTypeExtensions=["*"],
                    CFBundleTypeOSTypes=["****"],
                ),
                dict(
                    CFBundleTypeName="Text Document",
                    CFBundleTypeRole="Editor",
                    NSDocumentClass="TextDocument",
                    LSHandlerRank="Owner",
                    LSItemContentTypes=["public.plain-text", "public.text"],
                    CFBundleTypeExtensions=["txt", "text"],
                    CFBundleTypeOSTypes=["TEXT"],
                ),
#               dict(
#                   CFBundleTypeName="EditXT Project",
#                   CFBundleTypeRole="Editor",
#                   #NSDocumentClass="Project",
#                   LSHandlerRank="Owner",
#                   LSItemContentTypes=["org.editxt.project"],
#                   CFBundleTypeExtensions=["edxt"],
#               ),
            ],
#           UTExportedTypeDeclarations = [
#               dict(
#                   UTTypeIdentifier="org.editxt.project",
#                   UTTypeDescription="EditXT project format",
#                   UTTypeConformsTo=["public.plain-text"],
#                   #UTTypeIconFile=???,
#                   UTTypeTagSpecification={
#                       "public.finename-extension": ["edxt"]
#                   },
#               ),
#           ],
        ),
    )),
    data_files=[
        'resources/PythonApplet.icns',
        'resources/MainMenu.nib',
        'resources/EditorWindow.nib',
        'resources/FindPanel.nib',
        'resources/OpenPath.nib',
        'resources/SortLines.nib',
        'resources/WrapLines.nib',
        'resources/ChangeIndentation.nib',
        'resources/images/close-hover.png',
        'resources/images/close-normal.png',
        'resources/images/close-pressed.png',
        'resources/images/close-selected.png',
        'resources/images/close-dirty-hover.png',
        'resources/images/close-dirty-normal.png',
        'resources/images/close-dirty-pressed.png',
        'resources/images/close-dirty-selected.png',
        'resources/images/docsbar-blank.png',
        'resources/images/docsbar-menu.png',
        'resources/images/docsbar-plus.png',
        'resources/images/docsbar-props-down.png',
        'resources/images/docsbar-props-up.png',
        'resources/images/docsbar-sizer.png',
        'resources/mytextcommand.py',
        ("syntax", glob.glob("resources/syntax/*")),
        #("../Frameworks", ("lib/Frameworks/NDAlias.framework",)),
    ],
    entry_points={
        'nose.plugins': [
            'skip-slow = editxt.test.noseplugins:SkipSlowTests',
            'list-slowest = editxt.test.noseplugins:ListSlowestTests',
        ]
    },
)

if dev and hasattr(sys, 'real_prefix'):
    # HACK patch __boot__.py to work with virtualenv
    bootfile = os.path.join("dist", appname + ".app",
        "Contents/Resources/__boot__.py")
    with open(bootfile, "rb") as file:
        original = file.read()
    sitepaths = [p for p in sys.path if p.startswith(sys.real_prefix)]
    bootfunc = "import sys; sys.path[:0] = %r\n\n" % sitepaths
    with open(bootfile, "wb") as file:
        file.write(bootfunc.encode('utf-8') + original)

if package:
    from contextlib import closing
    from os.path import join
    from zipfile import ZipFile, ZIP_DEFLATED
    distpath = join(thisdir, 'dist')
    zip_file = '%s-v%s-%s.zip' % (appname, version, gitrev)
    print('packaging for distribution: %s' % zip_file)
    zip_path = join(distpath, zip_file)
    zip = ZipFile(zip_path, "w", ZIP_DEFLATED)
    with closing(zip):
        zip.write(join(thisdir, 'changelog.txt'), 'changelog.txt')
        zip.write(join(thisdir, 'COPYING'), 'COPYING')
        zip.write(join(thisdir, 'README.txt'), 'README.txt')
        zip.write(join(thisdir, 'bin/xt.py'), 'xt')
        app_path = join(thisdir, 'dist', appname + '.app')
        trimlen = len(distpath) + 1
        for dirpath, dirnames, filenames in os.walk(app_path):
            zpath = dirpath[trimlen:]
            for filename in filenames:
                zip.write(join(dirpath, filename), join(zpath, filename))

