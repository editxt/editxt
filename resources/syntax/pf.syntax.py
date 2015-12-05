# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: pf.js
name = 'pf'
file_patterns = ['*.pf', '*.pf.conf']

built_in = """
    block match pass load anchor antispoof set table
    """.split()

keyword = """
    in out log quick on rdomain inet inet6 proto from port os to
    routeallow-opts divert-packet divert-reply divert-to flags group
    icmp-typeicmp6-type label once probability recieved-on rtable prio
    queuetos tag tagged user keep fragment for os dropaf-to binat-to
    nat-to rdr-to bitmask least-stats random round-robinsource-hash
    static-portdup-to reply-to route-toparent bandwidth default min max
    qlimitblock-policy debug fingerprints hostid limit loginterface
    optimizationreassemble ruleset-optimization basic none profile skip
    state-defaultsstate-policy timeoutconst counters persistno modulate
    synproxy state floating if-bound no-sync pflow sloppysource-track
    global rule max-src-nodes max-src-states
    max-src-connmax-src-conn-rate overload flushscrub max-mss min-ttl
    no-df random-id
    """.split()

literal = ['all', 'any', 'no-route', 'self', 'urpf-failed', 'egress', 'unknown']

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [
        # {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

number = [RE(r"\b\d+(?:\.\d+)?")]

class string:
    default_text = DELIMITER
    rules = [
        # {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

variable = [RE(r"\$[\w\d#@][\w\d_]*")]

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('literal', literal),
    ('comment', RE(r"#"), [RE(r"$")], comment),
    ('number', number),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('variable', variable),
    ('variable', RE(r"<"), [RE(r">")]),
]

# TODO merge "word_groups" and "delimited_ranges" into "rules" in editxt.syntax
assert "__obj" not in globals()
assert "__fixup" not in globals()
def __fixup(obj):
    groups = []
    ranges = []
    rules = getattr(obj, "rules", [])
    for i, rng in reversed(list(enumerate(rules))):
        if len(rng) == 2:
            groups.append(rng)
        else:
            assert len(rng) > 2, rng
            ranges.append(rng)
    return groups, ranges

class __obj:
    rules = globals().get("rules", [])
word_groups, delimited_ranges = __fixup(__obj)

for __obj in globals().values():
    if hasattr(__obj, "rules"):
        __obj.word_groups, __obj.delimited_ranges = __fixup(__obj)

del __obj, __fixup
