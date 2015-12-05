# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: scilab.js
name = 'Scilab'
file_patterns = ['*.scilab', '*.sci']

built_in = """
    abs and acos asin atan ceil cd chdir clearglobal cosh cos cumprod
    deff disp error exec execstr exists exp eye gettext floor fprintf
    fread fsolve imag isdef isempty isinfisnan isvector lasterror length
    load linspace list listfiles log10 log2 log max min msprintf mclose
    mopen ones or pathconvert poly printf prod pwd rand real round sinh
    sin size gsort sprintf sqrt strcat strcmps tring sum system tanh tan
    type typename warning zeros matrix
    """.split()

keyword = """
    abort break case clear catch continue do elseif else endfunction end
    for function global if pause return resume select try then while
    """.split()

literal = """
    %f %F %t %T %pi %eps %inf %nan %e %i %z %s
    """.split()

keyword0 = ['function']

title = [RE(r"[a-zA-Z_]\w*")]

class function:
    default_text = DELIMITER
    rules = [
        ('keyword', keyword0),
        ('title', title),
        ('params', RE(r"\("), [RE(r"\)")]),
    ]

number = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

class string:
    default_text = DELIMITER
    rules = [
        # {'begin': '\\\\[\\s\\S]', 'relevance': 0},
        # {'begin': "''"},
    ]

class _group1:
    default_text = DELIMITER
    rules = [
        ('number', number),
        ('string', RE(r"'|\""), [RE(r"'|\"")], string),
    ]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [
        # {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('literal', literal),
    ('function', RE(r"\b(?:function)"), [RE(r"$")], function),
    ('_group0', RE(r"[a-zA-Z_][a-zA-Z_0-9]*(?:'+[\.']*|[\.']+)"), [RE(r"\B\b")]),
    ('_group1', RE(r"\["), [RE(r"\]'*[\.']*")], _group1),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('number', number),
    _group1.rules[1],
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
