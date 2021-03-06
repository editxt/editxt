# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: accesslog.js
name = 'Access log'
file_patterns = ['*.accesslog']

keyword = """
    GET POST HEAD PUT DELETE CONNECT OPTIONS PATCH TRACE
    """.split()

class string:
    default_text_color = DELIMITER
    rules = [('keyword', keyword)]

rules = [
    ('number', [RE(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d{1,5})?\b")]),
    ('number', [RE(r"\b\d+\b")]),
    ('string', RE(r"\"(?:GET|POST|HEAD|PUT|DELETE|CONNECT|OPTIONS|PATCH|TRACE)"), [RE(r"\"")], string),
    ('string', RE(r"\["), [RE(r"\]")]),
    ('string', RE(r"\""), [RE(r"\"")]),
]
