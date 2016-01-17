# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: bash.js
name = 'Bash'
file_patterns = ['*.bash', '*.sh', '*.zsh']

built_in = """
    break cd continue eval exec exit export getopts hash pwd readonly
    return shift test times trap umask unset alias bind builtin caller
    command declare echo enable help let local logout mapfile printf
    read readarray source type typeset ulimit unalias set shopt autoload
    bg bindkey bye cap chdir clone comparguments compcall compctl
    compdescribe compfiles compgroups compquote comptags comptry
    compvalues dirs disable disown echotc echoti emulate fc fg float
    functions getcap getln history integer jobs kill limit log noglob
    popd print pushd pushln rehash sched setcap setopt stat suspend
    ttyctl unfunction unhash unlimit unsetopt vared wait whence where
    which zcompile zformat zftp zle zmodload zparseopts zprof zpty
    zregexparse zsocket zstyle ztcp
    """.split()

keyword = """
    if then else elif fi for while in do done case esac function
    """.split()

class function:
    default_text_color = DELIMITER
    rules = [('title', [RE(r"\w[\w\d_]*")])]

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

operator_escape = ('operator.escape', [RE(r"\\[\s\S]")])

variable = ('variable', [RE(r"\$[\w\d#@][\w\d_]*")])

variable0 = ('variable', [RE(r"\$\{(?:.*?)}")])

class variable1:
    default_text_color = DELIMITER
    rules = [operator_escape]
variable1.__name__ = 'variable'

class string:
    default_text_color = DELIMITER
    rules = [
        operator_escape,
        variable,
        variable0,
        ('variable', RE(r"\$\("), [RE(r"\)")], variable1),
    ]

rules = [
    ('_', ['-ne', '-eq', '-lt', '-gt', '-f', '-d', '-e', '-s', '-l', '-a']),
    ('built_in', built_in),
    ('keyword', keyword),
    ('literal', ['true', 'false']),
    ('meta', [RE(r"^#![^\n]+sh\s*$")]),
    ('function', RE(r"(?=\w[\w\d_]*\s*\(\s*\)\s*\{)"), [RE(r"\B|\b")], function),
    ('comment', RE(r"#"), [RE(r"$")], comment),
    ('number', [RE(r"\b\d+(?:\.\d+)?")]),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('string', RE(r"'"), [RE(r"'")]),
    variable,
    variable0,
]