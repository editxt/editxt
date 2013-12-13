#! /usr/bin/env python
# Put this file somewhere on your path if you wish to interact with EditXT from
# the command line.
import os
import sys
from optparse import OptionParser, SUPPRESS_HELP
from subprocess import call

APP_NAME = 'EditXT'

TELL_EDITXT = """
tell application "%s"
    open %s
end tell
"""

def main(args):
    parser = OptionParser(
        description='%s command line interface' % APP_NAME,
        usage="usage: %prog [options] [files]",
    )
    parser.add_option('--dev', action='store_true', help=SUPPRESS_HELP)
    parser.add_option('--debug-osascript', action='store_true',
        help="Print AppleScript prior to executing it.")

    options, filenames = parser.parse_args(args)

    if options.dev:
        app_name = APP_NAME + 'Dev'
    else:
        app_name = APP_NAME

    script = make_script(app_name, filenames)

    if options.debug_osascript:
        print(script)

    if filenames and os.fork() != 0:
        # HACK send stdout to /dev/null to suppress "missing value" message
        with open('/dev/null', 'w') as devnull:
            try:
                call(['osascript', '-e', script], stdout=devnull)
            except KeyboardInterrupt:
                pass
    else:
        # HACK activate app without bringing all windows to front
        call(['open', '-a', app_name + '.app'])

def as_string(value):
    return '"%s"' % value.replace('"', '\\"')

def as_list(names):
    return '{%s}' % ', '.join(as_string(name) for name in names)

def iter_files(filenames):
    cwd = os.getcwd()
    for filename in filenames:
        if os.path.isabs(filename):
            yield filename
        else:
            yield os.path.join(cwd, filename)

def make_script(app_name, filenames):
    return TELL_EDITXT % (app_name, as_list(iter_files(filenames)))

if __name__ == '__main__':
    main(sys.argv[1:])
