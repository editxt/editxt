# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: accesslog.js
name = 'Access log'
file_patterns = ['*.accesslog']

number = [RE(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d{1,5})?\b")]

number0 = [RE(r"\b\d+\b")]

keyword = [
    'GET',
    'POST',
    'HEAD',
    'PUT',
    'DELETE',
    'CONNECT',
    'OPTIONS',
    'PATCH',
    'TRACE',
]

class string:
    default_text = DELIMITER
    rules = [('keyword', keyword)]

rules = [
    ('number', number),
    ('number', number0),
    ('string', RE(r"\"(GET|POST|HEAD|PUT|DELETE|CONNECT|OPTIONS|PATCH|TRACE)"), [RE(r"\"")], string),
    ('string', RE(r"\["), [RE(r"\]")]),
    ('string', RE(r"\""), [RE(r"\"")]),
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
