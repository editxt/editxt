# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: haml.js
name = 'Haml'
file_patterns = ['*.haml']

flags = re.IGNORECASE | re.MULTILINE

meta = [
    RE(r"^!!!(?: (?:5|1\.1|Strict|Frameset|Basic|Mobile|RDFa|XML\b.*))?$"),
]

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

class _group10:
    default_text_color = DELIMITER
    rules = [('_group1', RE(r"^\s*(?:-|=|!=)(?!#)"), [RE(r"\B|\b")])]
_group10.__name__ = '_group1'

operator_escape = ('operator.escape', [RE(r"\\[\s\S]")])

class string:
    default_text_color = DELIMITER
    rules = [operator_escape]

string0 = ('string', RE(r"'"), [RE(r"'")], string)

string1 = ('string', RE(r"\""), [RE(r"\"")], string)

class _group4:
    default_text_color = DELIMITER
    rules = [
        ('attr', [RE(r":\w+")]),
        string0,
        string1,
        # ignore {'begin': '\\w+', 'relevance': 0},
    ]

class _group3:
    default_text_color = DELIMITER
    rules = [('_group4', RE(r"(?=:\w+\s*=>)"), [RE(r",\s+")], _group4)]

class _group7:
    default_text_color = DELIMITER
    rules = [
        ('attr', [RE(r"\w+")]),
        string0,
        string1,
        # ignore {'begin': '\\w+', 'relevance': 0},
    ]

class _group6:
    default_text_color = DELIMITER
    rules = [('_group7', RE(r"(?=\w+\s*=)"), [RE(r"\s+")], _group7)]

class tag:
    default_text_color = DELIMITER
    rules = [
        ('selector-tag', [RE(r"\w+")]),
        ('selector-id', [RE(r"#[\w-]+")]),
        ('selector-class', [RE(r"\.[\w-]+")]),
        ('_group3', RE(r"{\s*"), [RE(r"\s*}")], _group3),
        ('_group6', RE(r"\(\s*"), [RE(r"\s*\)")], _group6),
    ]

class _group101:
    default_text_color = DELIMITER
    rules = [('_group10', RE(r"#{"), [RE(r"\B|\b")])]
_group101.__name__ = '_group10'

rules = [
    ('meta', meta),
    ('comment', RE(r"^\s*(?:!=#|=#|-#|/).*$"), [RE(r"\B\b")], comment),
    ('_group1', _group10, [RE(r"\n")], 'ruby'),
    ('tag', RE(r"^\s*%"), [RE(r"\B\b")], tag),
    # ignore {'begin': '^\\s*[=~]\\s*'},
    ('_group10', _group101, [RE(r"}")], 'ruby'),
]
