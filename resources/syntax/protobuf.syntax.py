# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: protobuf.js
name = 'Protocol Buffers'
file_patterns = ['*.protobuf']

built_in = [
    'double',
    'float',
    'int32',
    'int64',
    'uint32',
    'uint64',
    'sint32',
    'sint64',
    'fixed32',
    'fixed64',
    'sfixed32',
    'sfixed64',
    'bool',
    'string',
    'bytes',
]

keyword = [
    'package',
    'import',
    'option',
    'optional',
    'required',
    'repeated',
    'group',
]

literal = ['true', 'false']

number = [RE(r"\b\d+(\.\d+)?")]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [('doctag', doctag)]

keyword0 = ['message', 'enum', 'service']

class title:
    default_text = DELIMITER
    rules = [('title', RE(r"[a-zA-Z]\w*"), [RE(r"\B|\b")])]

class _group1:
    default_text = DELIMITER
    rules = []

class class0:
    default_text = DELIMITER
    rules = [('keyword', keyword0), ('title', title, [RE(r"(?=\{)")], _group1)]
class0.__name__ = 'class'

keyword1 = ['rpc', 'returns']

class function:
    default_text = DELIMITER
    rules = [('keyword', keyword1)]

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('literal', literal),
    ('string', RE(r"\""), [RE(r"\"")]),
    ('number', number),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('class', RE(r"\b(message|enum|service)"), [RE(r"\{")], class0),
    ('function', RE(r"\b(rpc)"), [RE(r"(?=;)")], function),
    ('_group2', RE(r"^\s*[A-Z_]+"), [RE(r"(?=\s*=)")]),
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
