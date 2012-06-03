#! /usr/bin/python
# Do it with python because bash escaping is too painful.
# The 'open' command only works with existing files:
#   #! /bin/bash
#   open -a EditXT.app "$@"
import os
import sys
from optparse import OptionParser
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
    parser.add_option('--dev', action='store_true',
        help="Target %sDev rather than %s." % (APP_NAME, APP_NAME))
    parser.add_option('--debug-osascript', action='store_true',
        help="Print applescript prior to executing it.")

    options, filenames = parser.parse_args(args)

    if options.dev:
        app_name = APP_NAME + 'Dev'
    else:
        app_name = APP_NAME

    script = make_script(app_name, filenames)

    if options.debug_osascript:
        print script

    if filenames:
        # HACK send stdout to /dev/null to suppress "missing value" message
        with open('/dev/null', 'w') as devnull:
            call(['osascript', '-e', script], stdout=devnull)

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
