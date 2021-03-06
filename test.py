#! /usr/bin/env python
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
import logging
import sys
import timeit
import traceback

sys.path.append("src")

logging.basicConfig(
    format='%(levelname)s - %(message)s',
    level=logging.DEBUG
)
log = logging.getLogger("test")

def eq(v0, v1):
    if v0 != v1:
        print("WARNING trial cases do not yield equal results")
        print(v0)
        print(v1)
        print()

a = ("\"abc\"" + '\'def\'' + "" + '' + '\\' + "\\", eq)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# isinstance vs callable

init = r"""
import re
from string import ascii_letters

body = "!@#$%^&*()_+=-" * 100000

r0 = re.compile("(?=%s)" % "|".join(c + '123' for c in ascii_letters))
r1 = re.compile("|".join("(?=%s123)" % c for c in ascii_letters))
r0.search(body)
r1.search(body)

def lookahead_or():
    r0.search(body)

def or_lookahead():
    r1.search(body)

"""

trials = [

'lookahead_or',
'or_lookahead',

]
n = 1000000

# 1000000 iterations
# trial 0: 0.02432469598716125 - lookahead_or
# trial 1: 0.02439560100901872 - or_lookahead

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#try:
#    exec(init)
#    v0 = eval(trials[0])
#    v1 = eval(trials[1])
#    eq(v0, v1)
#except Exception:
#    log.error("trial equality test failed", exc_info=True)
#    print()

print("# %s iterations" % n)
for i, trial in enumerate(trials):
    try:
        t = timeit.Timer(trial, init)
        #v1 = min(t.repeat(n, 1)) * n # if setup is needed for each timing
        v1 = t.timeit(n)
    except Exception as ex:
        print("# trial %i failed: %s - %s" % (i, ex, trial))
        traceback.print_exc()
    else:
        print("# trial %i:" % i, v1, '-', trial)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

'''
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# isinstance vs callable

init = r"""

class Yes:
    def __call__(self):
        pass

class No:
    pass

no = No()
yes = Yes()

assert not isinstance(no, Yes)
assert isinstance(yes, Yes)
assert not callable(no)
assert callable(yes)

def check_isinstance_no():
    isinstance(no, Yes)

def check_isinstance_yes():
    isinstance(yes, Yes)

def check_callable_no():
    callable(no)

def check_callable_yes():
    callable(yes)

"""

trials = [

'check_isinstance_no',
'check_isinstance_yes',
'check_callable_no',
'check_callable_yes',

]
n = 1000000

# 1000000 iterations
# trial 0: 0.026139621972106397 - check_isinstance_no
# trial 1: 0.025082350010052323 - check_isinstance_yes
# trial 2: 0.02559216000372544 - check_callable_no
# trial 3: 0.025074468983802944 - check_callable_yes

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 2x + vs str.join() (already copied below)

init = r"""
import re

ws_str = " \r\n\t\u2028\u2029"
ws_re = re.compile(r"[\s]")

a = "copyright"
b = "objc/_lazyimport.py"
c = " "
d = "\u2029"

def ta():
    for char in a:
        char in ws_str

def tb():
    for char in b:
        char in ws_str

def tc():
    for char in c:
        char in ws_str

def td():
    for char in d:
        char in ws_str

def ra():
    for char in a:
        ws_re.match(char)

def rb():
    for char in b:
        ws_re.match(char)

def rc():
    for char in c:
        ws_re.match(char)

def rd():
    for char in d:
        ws_re.match(char)

"""

trials = [

'ta',
'tb',
'tc',
'td',
'ra',
'rb',
'rc',
'rd',

]
n = 1000000

# 1000000 iterations
# trial 0: 0.026700152026023716 - ta
# trial 1: 0.027585859992541373 - tb
# trial 2: 0.02444710402050987 - tc
# trial 3: 0.02553490101126954 - td
# trial 4: 0.025960476021282375 - ra
# trial 5: 0.029181770980358124 - rb
# trial 6: 0.02470924297813326 - rc
# trial 7: 0.029455544019583613 - rd

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 2x + vs str.join()

init = """
a = "copyright"
b = "objc/_lazyimport.py"

def plus_x2():
    a + " " + b

def str_join():
    " ".join([a, b])

"""

trials = [

'plus_x2()',
'str_join()',

]
n = 1000000

# 1000000 iterations
# trial 0: 0.430229454068467 - plus_x2()
# trial 1: 0.4744787639938295 - str_join()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# contains vs setattr

init = """
x = {}
y = {0: 1, 10: 2, 20: 3}

keys = [0, 5, 10, 15, 20, 35]

def empty_contains_setattr():
    cache = x
    for i, k in enumerate(keys):
        if k not in cache:
            cache[k] = i

def filled_contains_setattr():
    cache = y
    for i, k in enumerate(keys):
        if k not in cache:
            cache[k] = i

def empty_setattr():
    cache = x
    for i, k in enumerate(keys):
        cache[k] = i

def filled_setattr():
    cache = y
    for i, k in enumerate(keys):
        cache[k] = i

"""

trials = [

'empty_contains_setattr()',
'filled_contains_setattr()',
'empty_setattr()',
'filled_setattr()',

]
n = 1000000

# 1000000 iterations
# trial 0: 2.249958924949169 - empty_contains_setattr()
# trial 1: 2.1139858290553093 - filled_contains_setattr()
# trial 2: 1.8919818103313446 - empty_setattr()
# trial 3: 1.8649734556674957 - filled_setattr()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

print("# %s iterations" % n)
for i, trial in enumerate(trials):
    try:
        t = timeit.Timer(trial, init)
        v1 = min(t.repeat(n, 1)) * n
    except Exception as ex:
        print("# trial %i failed: %s - %s" % (i, ex, trial))
        traceback.print_exc()
    else:
        print("# trial %i:" % i, v1, '-', trial)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# if x vs try vs if x is y

init = """
class X(object):
    def __init__(self):
        self.slots = None
x = X()

def control():
    return x.slots

def t0():
    try:
        return x.slots
    except AttributeError:
        pass

def t1(create=True):
    if create:
        return x.slots

def t2(create=True):
    if create is True:
        return x.slots

"""

trials = [

'control()',
't0()',
't1()',
't2()',

]
n = 1000000

# trial 0: 0.220976114273
# trial 1: 0.262070178986
# trial 2: 0.248097896576
# trial 3: 0.299978971481

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# if [] vs if x == ['y']

init = """
def t0(row=['a', 'b', 'c', 'd']):
    if row:
        pass

def t1(row=['a', 'b', 'c', 'd'], check=['y']):
    if row == check:
        pass

"""

trials = [

't0()',
't1()',

]
n = 100000

# trial 0: 0.0194828510284
# trial 1: 0.0232598781586

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# if x vs try vs if x is y

init = """
class X(object):
    def __init__(self):
        self.slots = None
x = X()

def control():
    return x.slots

def t0():
    try:
        return x.slots
    except AttributeError:
        pass

def t1(create=True):
    if create:
        return x.slots

def t2(create=True):
    if create is True:
        return x.slots

"""

trials = [

'control()',
't0()',
't1()',
't2()',

]
n = 1000000

# trial 0: 0.220976114273
# trial 1: 0.262070178986
# trial 2: 0.248097896576
# trial 3: 0.299978971481

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# issubclass(x, y) vs x in (m, n) vs not (x is m or x is n)

init = """
class End(object): pass
class LastLine(End): pass
class NewParagraph(End): pass
values = ["", "abc", LastLine, NewParagraph]

t0 = lambda v: issubclass(v, End)
t1 = lambda v: v in (LastLine, NewParagraph)
t2 = lambda v: not (v is LastLine or v is NewParagraph)
"""

trials = [

'[t0(v) for v in values]',
'[t1(v) for v in values]',
'[t2(v) for v in values]',

]
n = 100000

# trial 0 failed: TypeError: issubclass() arg 1 must be a class
# trial 1: 0.241290092468
# trial 2: 0.187973022461

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# if vs strcat

init = """
import string, random
lines = ["".join(random.choice(string.letters) for i in xrange(80)) for j in xrange(100)]

f0 = lambda line, leading: (leading + line) if leading else line
f1 = lambda line, leading: leading + line
"""

trials = [

'[f0(line, "    ") for line in lines]',
'[f1(line, "    ") for line in lines]',

'[f0(line, "") for line in lines]',
'[f1(line, "") for line in lines]',

]
n = 100000

# trial 0: 4.61961889267
# trial 1: 4.24296498299

# trial 2: 3.24405217171
# trial 3: 3.34566116333

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# prime generator

init = """
import itertools

def prime_gen_0():
    yield 2
    n = 3
    yield n
    prime_list = [(2, 4), (3, 9)]
    it = itertools.count(4)
    for n in it:
        n = it.next()
        for p,p2 in prime_list:
            if n % p == 0:
                break
            elif p2 > n:
                prime_list.append((n, n*n))
                yield n
                break
        else:
            raise RuntimeError("Shouldn't have run out of primes!")


def prime_gen_1():
    prime_list = [2, 3]
    for p in prime_list: yield p
    for n in itertools.count(prime_list[-1] + 2):
        for p in prime_list:
            if p * p > n:
                prime_list.append(n)
                yield n
                break
            elif n % p == 0:
                break
        else:
            raise Exception("Shouldn't have run out of primes!")

pg0 = prime_gen_0()
pg1 = prime_gen_1()

"""

trials = [

"[pg0.next() for i in xrange(1000)]",

"[pg1.next() for i in xrange(1000)]",

]
n = 50

# trial 0: 4.21483492851
# trial 1: 0.391325950623

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# string.rfind(u"\n", ...) vs NSString.lineRangeForRange_(...).location

init = """
from Foundation import NSString

us = (u"a " * 400 + u"\\n") * 3000
ns = NSString.stringWithString_(us)

indices = [20, 300, 799, 1200, 2000 * 800, 2000 * 800 + 400, 3000 * 800 - 2, 3000 * 800 - 400]
"""

trials = [

"""
[ns.rfind(u"\\n", 0, i) + 1 for i in indices]
""",

"""
[ns.lineRangeForRange_((i, 0)).location for i in indices]
""",

]
n = 100000

# trial 0: 1.40011692047
# trial 1: 7.51187491417

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# while-loop-search vs NSString.lineRangeForRange_(...).location

init = """
from Foundation import NSString

us = (u"a " * 400 + u"\\n") * 3000
ns = NSString.stringWithString_(us)

indices = [20, 300, 799, 1200, 2000 * 800, 2000 * 800 + 400, 3000 * 800 - 2, 3000 * 800 - 400]

def find0(text, i):
    while i > 0 and text[i-1] not in u"\\n\\r\\u2028":
        i -= 1
    return i

def find1(text, i):
    return text.lineRangeForRange_((i, 0)).location

"""

trials = [

"[find0(ns, i) for i in indices]",

"[find1(ns, i) for i in indices]",

]
n = 5000

# trial 0: 4.21483492851
# trial 1: 0.391325950623

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# NSRange.location/.length vs subscript notation

init = """
from Foundation import NSMakeRange

r = NSMakeRange(0, 2)
"""

trials = [

"r[0], r[1]",

"r.location, r.length",

]
n = 1000000

# trial 0: 0.246095895767
# trial 1: 0.268185138702

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
'''
