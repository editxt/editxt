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
import time
from nose.plugins import Plugin
from nose.plugins.skip import SkipTest


class SkipSlowTests(Plugin):
    """Skip tests decorated with @slow"""

    name = 'skip-slow'

    def options(self, parser, env):
        env_opt = 'NOSE_%s' % self.name.upper()
        env_opt = env_opt.replace('-', '_')
        parser.add_option(
            "--%s" % self.name,
            action="store_true",
            dest=self.enableOpt,
            default=env.get(env_opt),
            help="Enable plugin %s: %s [%s]" %
            (self.__class__.__name__, self.help(), env_opt))

    def configure(self, options, config):
        if hasattr(options, self.enableOpt):
            slow_skip.enabled = getattr(options, self.enableOpt)
#        if hasattr(options, self.enableOpt):
#            self.enabled = getattr(options, self.enableOpt)
#            if self.enabled:
#                self.attribs = [[('slow', False)]]
                

def slow_skip():
    if slow_skip.enabled:
        raise SkipTest('too slow')
slow_skip.enabled = False

class ListSlowestTests(Plugin):
    """List the slowest N tests"""

    name = 'list-slowest'

    def options(self, parser, env):
        env_opt = 'NOSE_%s' % self.name.upper()
        env_opt = env_opt.replace('-', '_')
        parser.add_option(
            "--%s" % self.name,
            type="int",
            dest='list_slowest',
            metavar='N',
            default=env.get(env_opt),
            help="Enable plugin %s: %s [%s]" %
            (self.__class__.__name__, self.help(), env_opt))

    def configure(self, options, config):
        self.list_num = getattr(options, 'list_slowest', 0)
        if self.list_num:
            self.enabled = True
            self.unknown_start = []
            self.finished = []

    def beforeTest(self, test):
        test.__start_time = time.time()

    def afterTest(self, test):
        try:
            elapsed = time.time() - test.__start_time
        except AttributeError:
            self.unknown_start.append((test))
        else:
            self.finished.append((test, elapsed))

    def finalize(self, result):
        print('')
        if self.unknown_start:
            print('Tests with no start time (this should not happen):')
            for test in self.unknown_start:
                print('  %s' % test)
        print('%s slowest tests:' % self.list_num)
        key = lambda v:v[1]
        slowest = sorted(self.finished, key=key, reverse=True)[:self.list_num]
        for test, elapsed in slowest:
            print('  %s : %0.3fms' % (test, elapsed * 1000))
        print('')
