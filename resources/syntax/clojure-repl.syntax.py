# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: clojure-repl.js
name = 'Clojure REPL'
file_patterns = ['*.clojure-repl']

class meta0:
    default_text_color = DELIMITER
    rules = [('meta', RE(r"^(?:[\w.-]+|\s*#_)=>"), [RE(r"\B|\b")])]
meta0.__name__ = 'meta'

rules = [('meta', meta0, [RE(r"$")], 'clojure')]
