# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: perl.js
name = 'Perl'
file_patterns = ['*.perl', '*.pl']

keyword = """
    getpwent getservent quotemeta msgrcv scalar kill dbmclose undef lc
    ma syswrite tr send umask sysopen shmwrite vec qx utime local oct
    semctl localtime readpipe do return format read sprintf dbmopen pop
    getpgrp not getpwnam rewinddir qqfileno qw endprotoent wait
    sethostent bless s opendir continue each sleep endgrent shutdown
    dump chomp connect getsockname die socketpair close flock exists
    index shmgetsub for endpwent redo lstat msgctl setpgrp abs exit
    select print ref gethostbyaddr unshift fcntl syscall goto
    getnetbyaddr join gmtime symlink semget splice x getpeername recv
    log setsockopt cos last reverse gethostbyname getgrnam study
    formline endhostent times chop length gethostent getnetent pack
    getprotoent getservbyname rand mkdir pos chmod y substr endnetent
    printf next open msgsnd readdir use unlink getsockopt getpriority
    rindex wantarray hex system getservbyport endservent int chr untie
    rmdir prototype tell listen fork shmread ucfirst setprotoent else
    sysseek link getgrgid shmctl waitpid unpack getnetbyname reset chdir
    grep split require caller lcfirst until warn while values shift
    telldir getpwuid my getprotobynumber delete and sort uc defined
    srand accept package seekdir getprotobyname semop our rename seek if
    q chroot sysread setpwent no crypt getc chown sqrt write setnetent
    setpriority foreach tie sin msgget map stat getlogin unless elsif
    truncate exec keys glob tied closedirioctl socket readlink eval xor
    readline binmode setservent eof ord bind alarm pipe atan2 getgrent
    exp time push setgrent gt lt or ne m break given say state when
    """.split()

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

comment0 = ('comment', RE(r"#"), [RE(r"$")], comment)

class _group4:
    default_text_color = DELIMITER
    rules = []

operator_escape = ('operator.escape', [RE(r"\\[\s\S]")])

class subst:
    default_text_color = DELIMITER
    rules = [('keyword', keyword)]

class string:
    default_text_color = DELIMITER
    rules = [
        operator_escape,
        ('subst', RE(r"[$@]\{"), [RE(r"\}")], subst),
        # ignore {'begin': {'pattern': '\\$\\d', 'type': 'RegExp'}},
        # ignore {'begin': {'pattern': '[\\$%@](\\^\\w\\b|#\\w+(::\\w+)*|{\\w+}|\\w+(::\\w*)*)', 'type': 'RegExp'}},
        # ignore {'begin': {'pattern': '[\\$%@][^\\s\\w{]', 'type': 'RegExp'}, 'relevance': 0},
    ]

class string7:
    default_text_color = DELIMITER
    rules = [operator_escape]
string7.__name__ = 'string'

number = [
    RE(r"(?:\b0[0-7_]+)|(?:\b0x[0-9a-fA-F_]+)|(?:\b[1-9][0-9_]*(?:\.[0-9_]+)?)|[0_]\b"),
]

class regexp0:
    default_text_color = DELIMITER
    rules = [operator_escape]
regexp0.__name__ = 'regexp'

class _group5:
    default_text_color = DELIMITER
    rules = [
        ('keyword', ['split', 'return', 'print', 'reverse', 'grep']),
        comment0,
        ('regexp', [RE(r"(?:s|tr|y)/(?:\\.|[^/])*/(?:\\.|[^/])*/[a-z]*")]),
        ('regexp', RE(r"(?:m|qr)?/"), [RE(r"/[a-z]*")], regexp0),
    ]

class _function:
    default_text_color = DELIMITER
    rules = [('function', [RE(r"(?:\s*\(.*?\))?[;{]")])]

class function0:
    default_text_color = DELIMITER
    rules = [('keyword', ['sub']), ('title', [RE(r"[a-zA-Z]\w*")])]
function0.__name__ = 'function'

class _group7:
    default_text_color = DELIMITER
    rules = [('comment', RE(r"^@@.*"), [RE(r"$")])]

rules = [
    ('keyword', keyword),
    # ignore {'begin': {'pattern': '\\$\\d', 'type': 'RegExp'}},
    # ignore {'begin': {'pattern': '[\\$%@](\\^\\w\\b|#\\w+(::\\w+)*|{\\w+}|\\w+(::\\w*)*)', 'type': 'RegExp'}},
    # ignore {'begin': {'pattern': '[\\$%@][^\\s\\w{]', 'type': 'RegExp'}, 'relevance': 0},
    comment0,
    ('comment', RE(r"^\=\w"), [RE(r"\=cut")], comment),
    ('_group4', RE(r"->{"), [RE(r"}")], _group4),
    ('string', RE(r"q[qwxr]?\s*\("), [RE(r"\)")], string),
    ('string', RE(r"q[qwxr]?\s*\["), [RE(r"\]")], string),
    ('string', RE(r"q[qwxr]?\s*\{"), [RE(r"\}")], string),
    ('string', RE(r"q[qwxr]?\s*\|"), [RE(r"\|")], string),
    ('string', RE(r"q[qwxr]?\s*\<"), [RE(r"\>")], string),
    ('string', RE(r"qw\s+q"), [RE(r"q")], string),
    ('string', RE(r"'"), [RE(r"'")], string7),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('string', RE(r"`"), [RE(r"`")], string7),
    ('string', RE(r"{\w+}"), [RE(r"\B\b")]),
    ('string', RE(r"-?\w+\s*\=\>"), [RE(r"\B\b")]),
    ('number', number),
    ('_group5', RE(r"(?:\/\/|!|!=|!==|%|%=|&|&&|&=|\*|\*=|\+|\+=|,|-|-=|/=|/|:|;|<<|<<=|<=|<|===|==|=|>>>=|>>=|>=|>>>|>>|>|\?|\[|\{|\(|\^|\^=|\||\|=|\|\||~|\b(?:split|return|print|reverse|grep)\b)\s*"), [RE(r"\B\b")], _group5),
    ('function', RE(r"\b(?:sub)"), [_function], function0),
    # ignore {'begin': '-\\w\\b', 'relevance': 0},
    ('_group7', RE(r"^__DATA__$"), [RE(r"^__END__$")], 'mojolicious'),
]

_group4.rules.extend(rules)
subst.rules.extend(rules)
