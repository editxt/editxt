#! /usr/bin/env python
# Monitor process memory usage
import sys
import time
from subprocess import Popen, PIPE

def usage():
    sys.exit("usage: %s PID" % sys.argv[0])

def mem(cmd):
    proc = Popen(cmd, stdout=PIPE)
    value = proc.communicate()[0].split('\n')[1]
    return int(value)

def main():
    if len(sys.argv) != 2:
        usage()
    try:
        int(sys.argv[1])
    except (TypeError, ValueError):
        usage()

    pid = sys.argv[1]
    cmd = 'ps -o rss="" -p'.split() + [pid]

    print(' '.join(cmd))
    original = mem(cmd)

    while True:
        val = mem(cmd)
        print('%s  %+g' % (val, val - original))
        time.sleep(1)

if __name__ == '__main__':
    main()
