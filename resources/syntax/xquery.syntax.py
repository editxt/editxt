# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: xquery.js
name = 'XQuery'
file_patterns = ['*.xquery', '*.xpath', '*.xq']

keyword = """
    for let if while then else return where group by xquery encoding
    versionmodule namespace boundary-space preserve strip default
    collation base-uri orderingcopy-namespaces order declare import
    schema namespace function option in allowing emptyat tumbling window
    sliding window start when only end when previous next stable
    ascendingdescending empty greatest least some every satisfies switch
    case typeswitch try catch andor to union intersect instance of treat
    as castable cast map array delete insert intoreplace value rename
    copy modify update
    """.split()

literal = """
    false true xs:string xs:integer element item xs:date xs:datetime
    xs:float xs:double xs:decimal QName xs:anyURI xs:long xs:int
    xs:short xs:byte attribute
    """.split()

#class string:
#    default_text_color = DELIMITER
#    rules = [
#        # ignore {'begin': {'pattern': '""', 'type': 'RegExp'}, 'relevance': 0},
#    ]

number = [
    RE(r"(?:\b0[0-7_]+)|(?:\b0x[0-9a-fA-F_]+)|(?:\b[1-9][0-9_]*(?:\.[0-9_]+)?)|[0_]\b"),
]

class comment:
    default_text_color = DELIMITER
    rules = [('doctag', [RE(r"@\w+")])]

class _group3:
    default_text_color = DELIMITER
    rules = []

rules = [
    ('keyword', keyword),
    ('literal', literal),
    # ignore {'begin': {'pattern': '\\$[a-zA-Z0-9\\-]+', 'type': 'RegExp'}, 'relevance': 5},
    ('string', RE(r"\""), [RE(r"\"")]), #, string),
    ('string', RE(r"'"), [RE(r"'")]), #, string),
    ('number', number),
    ('comment', RE(r"\(:"), [RE(r":\)")], comment),
    ('meta', [RE(r"%\w+")]),
    ('_group3', RE(r"{"), [RE(r"}")], _group3),
]

_group3.rules.extend(rules)
