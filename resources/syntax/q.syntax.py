# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: q.js
name = 'Q'
file_patterns = ['*.q', '*.k', '*.kdb']

built_in = """
    neg not null string reciprocal floor ceiling signum mod xbar xlog
    and or each scan over prior mmu lsq inv md5 ltime gtime count first
    var dev med cov cor all any rand sums prds mins maxs fills deltas
    ratios avgs differ prev next rank reverse iasc idesc asc desc msum
    mcount mavg mdev xrank mmin mmax xprev rotate distinct group where
    flip type key til get value attr cut set upsert raze union inter
    except cross sv vs sublist enlist read0 read1 hopen hclose hdel hsym
    hcount peach system ltrim rtrim trim lower upper ssr view tables
    views cols xcols keys xkey xcol xasc xdesc fkeys meta lj aj aj0 ij
    pj asof uj ww wj wj1 fby xgroup ungroup ej save load rsave rload
    show csv parse eval min max avg wavg wsum sin cos tan sum
    """.split()

keyword = ['do', 'while', 'select', 'delete', 'by', 'update', 'from']

literal = ['0b', '1b']

type = """
    `float `double int `timestamp `timespan `datetime `time `boolean
    `symbol `char `byte `short `long `real `month `date `minute `second
    `guid
    """.split()

number = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

class string:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('literal', literal),
    ('type', type),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('number', number),
]
