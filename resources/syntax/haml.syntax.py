# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: haml.js
name = 'Haml'
file_patterns = ['*.haml']

flags = re.IGNORECASE | re.MULTILINE

meta = [
    RE(r"^!!!(?: (?:5|1\.1|Strict|Frameset|Basic|Mobile|RDFa|XML\b.*))?$"),
]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

class _group0:
    default_text_color = DELIMITER
    rules = [('_group0', RE(r"^\s*(?:-|=|!=)(?!#)"), [RE(r"\B|\b")])]

selector_tag = [RE(r"\w+")]

selector_id = [RE(r"#[\w-]+")]

selector_class = [RE(r"\.[\w-]+")]

attr = [RE(r":\w+")]

class string:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

class _group5:
    default_text_color = DELIMITER
    rules = [
        ('attr', attr),
        ('string', RE(r"'"), [RE(r"'")], string),
        ('string', RE(r"\""), [RE(r"\"")], string),
        # ignore {'begin': '\\w+', 'relevance': 0},
    ]

class _group3:
    default_text_color = DELIMITER
    rules = [('_group5', RE(r"(?=:\w+\s*=>)"), [RE(r",\s+")], _group5)]

class _group6:
    default_text_color = DELIMITER
    rules = [
        ('attr', selector_tag),
        _group5.rules[1],
        _group5.rules[2],
        # ignore {'begin': '\\w+', 'relevance': 0},
    ]

class _group4:
    default_text_color = DELIMITER
    rules = [('_group6', RE(r"(?=\w+\s*=)"), [RE(r"\s+")], _group6)]

class tag:
    default_text_color = DELIMITER
    rules = [
        ('selector-tag', selector_tag),
        ('selector-id', selector_id),
        ('selector-class', selector_class),
        ('_group3', RE(r"{\s*"), [RE(r"\s*}")], _group3),
        ('_group4', RE(r"\(\s*"), [RE(r"\s*\)")], _group4),
    ]

class _group1:
    default_text_color = DELIMITER
    rules = [('_group1', RE(r"#{"), [RE(r"\B|\b")])]

rules = [
    ('meta', meta),
    ('comment', RE(r"^\s*(?:!=#|=#|-#|/).*$"), [RE(r"\B\b")], comment),
    ('_group0', _group0, [RE(r"\n")], 'ruby'),
    ('tag', RE(r"^\s*%"), [RE(r"\B\b")], tag),
    # ignore {'begin': '^\\s*[=~]\\s*'},
    ('_group1', _group1, [RE(r"}")], 'ruby'),
]
