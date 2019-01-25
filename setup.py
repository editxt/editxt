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
import glob
import os
import re
import shutil
import sys
import time
from os.path import isdir, join

from datetime import datetime
from setuptools import setup
from subprocess import check_output, Popen, PIPE

import commonmark


if hasattr(sys, 'real_prefix'):
    # HACK fixes for py2app + virtualenv
    if sys.prefix.endswith("/.."):
        sys.prefix = os.path.normpath(sys.prefix)
    if sys.exec_prefix.endswith("/.."):
        sys.exec_prefix = os.path.normpath(sys.exec_prefix)

import py2app

from editxt import __version__ as version
build_date = datetime.now()
revision = build_date.strftime("%Y%m%d%H%M")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def _fix_py2app_plistlib():
    # Fix py2app 0.11 on Python 3.7
    import plistlib

    class Plist(dict):

        @classmethod
        def fromFile(cls, filename):
            with open(filename, "rb") as fp:
                value = plistlib.load(fp)
            plist = cls()
            plist.update(value)
            return plist

        def write(self, path):
            with plistlib._maybe_open(path, 'wb') as fp:
                plistlib.dump(self, fp)

    plistlib.Dict = type("Dict", (dict,), {})
    plistlib.Plist = Plist


_fix_py2app_plistlib()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# handle -A switch (dev build)
if "-A" in sys.argv:
    dev = True
    appname = "EditXTDev"
else:
    dev = False
    appname = "EditXT"

install = "--install" in sys.argv
if install:
    assert not dev, "refusing to install dev build"
    sys.argv.remove("--install")

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

thisdir = os.path.dirname(os.path.abspath(__file__))

def rmtree(path):
    if os.path.exists(path):
        print("removing", path)
        shutil.rmtree(path)

def clean():
    # remove old build
    if "--noclean" in sys.argv:
        sys.argv.remove("--noclean")
    else:
        rmtree(join(thisdir, "build"))
        rmtree(join(thisdir, "dist", appname + ".app"))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
setup_args = dict(
    name=appname,
    app=['boot.py'],
    version=version,
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3'
    ],
    options=dict(py2app=dict(
        # argv_emulation causes the app to launch in a strange mode that does
        # not play nicely with Exposé (the window does not come to the front
        # when switching to EditXT with Exposé). Luckily everything seems to
        # work as expected without it!!
        #argv_emulation=True,
        packages=["editxt"],
        frameworks=["resources/Sparkle-1.18.1/Sparkle.framework"],
        plist=dict(
            CFBundleGetInfoString = "%s %s.%s" % (version, revision, gitrev),
            CFBundleShortVersionString = version,
            CFBundleVersion = revision + "." + gitrev,
            NSHumanReadableCopyright = '© Daniel Miller',
            CFBundleIdentifier = "org.editxt." + appname,
            CFBundleIconFile = "PythonApplet.icns",
            SUPublicDSAKeyFile = "dsa_pub.pem",
            SUFeedURL = "https://github.com/editxt/editxt/raw/master/resources/updater/updates.xml",
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
        'resources/images/popout-button.png',
        'resources/images/popout-button-alt.png',
        'resources/mytextcommand.py',
        'resources/updater/dsa_pub.pem',
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

def fix_virtualenv_boot():
    # TODO remove this unused function
    if dev and hasattr(sys, 'real_prefix'):
        # HACK patch __boot__.py to work with virtualenv
        bootfile = join("dist", appname + ".app",
            "Contents/Resources/__boot__.py")
        with open(bootfile, "rb") as file:
            original = file.read()
        sitepaths = [p for p in sys.path if p.startswith(sys.real_prefix)]
        bootfunc = "import sys; sys.path[:0] = %r\n\n" % sitepaths
        with open(bootfile, "wb") as file:
            file.write(bootfunc.encode('utf-8') + original)

def prepare_sparkle_update(zip_path):
    sig = check_output([
        join(thisdir, "resources/Sparkle-1.18.1/bin/sign_update"),
        zip_path,
        join(thisdir, "resources/updater/dsa_priv.pem"),
    ], universal_newlines=True).strip()

    with open(join(thisdir, "resources/updater/item-template.xml")) as fh:
        template = fh.read()
    item = template.format(
        title="Version {}".format(version),
        changesHTML=get_latest_changes(version),
        pubDate=build_date.strftime("%a, %d %b %Y %H:%M:%S " + timezone(build_date)),
        url="https://github.com/editxt/editxt/releases/download/{}/{}".format(
                version, os.path.basename(zip_path)),
        version=revision + "." + gitrev,
        shortVersion=version,
        dsaSignature=sig,
        length=os.stat(zip_path).st_size,
    )

    with open(join(thisdir, "resources/updater/updates.xml")) as fh:
        updates = fh.read()
    i = updates.rfind("  </channel>")
    assert i > 0, updates
    with open(join(thisdir, "resources/updater/updates.xml"), "w") as fh:
        fh.write(updates[:i])
        fh.write(item)
        fh.write(updates[i:])

    update_change_log_html()


def timezone(local_datetime):
    """Get timezone in +HHMM format"""
    ts = time.mktime(local_datetime.replace(microsecond=0).timetuple())
    utc_offset = local_datetime - datetime.utcfromtimestamp(ts)
    assert -1 <= utc_offset.days <= 0, utc_offset
    assert utc_offset.seconds % 900 == 0, utc_offset
    total_minutes = (utc_offset.days * 24 * 3600 + utc_offset.seconds) // 60
    assert total_minutes % 15 == 0, (utc_offset, total_minutes)
    hours, minutes = divmod(total_minutes, 60)
    assert minutes >= 0, (hours, minutes, total_minutes)
    if hours < 0 and minutes > 0:
        hours += 1
        minutes = 60 - minutes
    assert 0 <= abs(hours) <= 14, (utc_offset, hours, minutes)
    assert 0 <= minutes < 60, (utc_offset, hours, minutes)
    return "%+03i%02i" % (hours, minutes)


def get_latest_changes(version):
    regex = re.compile((
        r"\n## \d{{4}}-..-.. - {}\n" # date/version tag for current version
        r"([\s\S]+?)"           # changes
        r"\n## \d{{4}}-..-.. - "    # older version tag
    ).format(re.escape(version)))
    with open(join(thisdir, "changelog.md")) as fh:
        data = fh.read()
    match = regex.search(data)
    if not match:
        print("recent changes not found in changelog.md")
        return ""
    value = match.group(1)
    parser = commonmark.Parser()
    renderer = commonmark.HtmlRenderer()
    return renderer.render(parser.parse(value))


def update_change_log_html():
    regex = re.compile(r"## \d{4}-..-.. - ")
    lines = []
    with open(join(thisdir, "changelog.md")) as fh:
        for line in fh:
            if lines:
                lines.append(line)
            elif regex.match(line):
                lines.append("\n")
                lines.append(line)
    if not lines:
        print("Change Log header not found in changelog.md")
        return False
    value = "".join(lines)
    parser = commonmark.Parser()
    renderer = commonmark.HtmlRenderer()
    updates_html = renderer.render(parser.parse(value))
    with open(join(thisdir, "resources/updater/updates-template.html")) as fh:
        template = fh.read()
    html = template % {"body": updates_html}
    with open(join(thisdir, "resources/updater/updates.html"), "w") as fh:
        fh.write(html)
    return True


def build_zip():
    from contextlib import closing
    from itertools import chain
    from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
    distpath = join(thisdir, 'dist')
    zip_file = '%s-v%s-%s.zip' % (appname, version, gitrev)
    print('packaging for distribution: %s' % zip_file)
    zip = ZipFile(join(distpath, zip_file), "w", ZIP_DEFLATED)
    with closing(zip):
        zip.write(join(thisdir, 'changelog.md'), 'changelog.md')
        zip.write(join(thisdir, 'COPYING'), 'COPYING')
        zip.write(join(thisdir, 'README.md'), 'README.md')
        zip.write(join(thisdir, 'bin/xt.py'), 'xt')
        app_path = join(thisdir, 'dist', appname + '.app')
        trimlen = len(distpath) + 1
        for dirpath, dirnames, filenames in os.walk(app_path):
            zpath = dirpath[trimlen:]
            if filenames or dirnames:
                dirs = ((item, True) for item in dirnames)
                files = ((item, False) for item in filenames)
                for filename, isdir in chain(dirs, files):
                    filepath = join(dirpath, filename)
                    zip_path = join(zpath, filename)
                    if os.path.islink(filepath):
                        info = ZipInfo(zip_path)
                        info.create_system = 3
                        info.external_attr = 2716663808
                        linkdest = os.readlink(filepath)
                        assert not os.path.isabs(linkdest), linkdest
                        zip.writestr(info, linkdest)
                    elif not isdir:
                        zip.write(filepath, zip_path)
            else:
                # write empty directory
                info = ZipInfo(zpath + os.path.sep)
                zip.writestr(info, '')
    return zip.filename


def fix_app_site_packages():
    # HACK for py2app with Python 3 in venv
    pyver = f"python{sys.version_info.major}.{sys.version_info.minor}"
    site_packages = join(os.environ["VIRTUAL_ENV"], f"lib/{pyver}/site-packages")
    app_site_packages = join(thisdir, 'dist', appname + '.app',
        f"Contents/Resources/lib/{pyver}/site-packages")
    assert os.path.exists(site_packages), site_packages
    assert not os.path.exists(app_site_packages), app_site_packages
    assert not os.path.exists(app_site_packages + ".zip"), app_site_packages
    os.symlink(site_packages, app_site_packages)


if "--html-only" in sys.argv:
    update_change_log_html()
    sys.exit()

clean()
setup(**setup_args)
if "-A" in sys.argv:
    fix_app_site_packages()
if package:
    zip_path = build_zip()
    prepare_sparkle_update(zip_path)

if install:
    # expects ./dist/Applications to be a symlink to
    # Applications folder where the app is installed
    apps_dir = join(thisdir, "dist", "Applications")
    if isdir(apps_dir):
        installed_app = join(apps_dir, appname + ".app")
        rmtree(installed_app)
        built_app = join(thisdir, "dist", appname + ".app")
        print("mv {} -> {}".format(built_app, installed_app))
        os.rename(built_app, installed_app)
    else:
        print("cannot install: {} not found".format(apps_dir))

