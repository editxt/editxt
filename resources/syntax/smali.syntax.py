# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: smali.js
name = 'Smali'
file_patterns = ['*.smali', '*.smali']

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    word_groups = [('doctag', doctag)]

keyword = [RE(r"\s*\.end\s[a-zA-Z0-9]*")]

keyword0 = [RE(r"^[ ]*\.[a-zA-Z]*")]

keyword1 = [RE(r"\s:[a-zA-Z_0-9]*")]

keyword2 = [
    RE(r"\s(transient|constructor|abstract|final|synthetic|public|private|protected|static|bridge|system)"),
]

built_in = [
    RE(r"\s(add|and|cmp|cmpg|cmpl|const|div|double|float|goto|if|int|long|move|mul|neg|new|nop|not|or|rem|return|shl|shr|sput|sub|throw|ushr|xor)\s"),
]

built_in0 = [
    RE(r"\s(add|and|cmp|cmpg|cmpl|const|div|double|float|goto|if|int|long|move|mul|neg|new|nop|not|or|rem|return|shl|shr|sput|sub|throw|ushr|xor)((\-|/)[a-zA-Z0-9]+)+\s"),
]

built_in1 = [
    RE(r"\s(aget|aput|array|check|execute|fill|filled|goto/16|goto/32|iget|instance|invoke|iput|monitor|packed|sget|sparse)((\-|/)[a-zA-Z0-9]+)*\s"),
]

class0 = [RE(r"L[^(;:\n]*;")]

word_groups = [
    ('keyword', keyword),
    ('keyword', keyword0),
    ('keyword', keyword1),
    ('keyword', keyword2),
    ('built_in', built_in),
    ('built_in', built_in0),
    ('built_in', built_in1),
    ('class', class0),
]

delimited_ranges = [
    ('string', RE(r"\""), [RE(r"\"")]),
    ('comment', RE(r"#"), [RE(r"$")], comment),
]
