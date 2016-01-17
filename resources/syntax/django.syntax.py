# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: django.js
name = 'Django'
file_patterns = ['*.django', '*.jinja']

flags = re.IGNORECASE | re.MULTILINE

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

name0 = """
    comment endcomment load templatetag ifchanged endifchanged if endif
    firstof for endfor ifnotequal endifnotequal widthratio extends
    include spaceless endspaceless regroup ifequal endifequal ssi now
    with cycle url filter endfilter debug block endblock else autoescape
    endautoescape csrf_token empty elif endwith static trans blocktrans
    endblocktrans get_static_prefix get_media_prefix plural
    get_current_language language get_available_languages
    get_current_language_bidi get_language_info get_language_info_list
    localize endlocalize localtime endlocaltime timezone endtimezone
    get_current_timezone verbatim
    """.split()

class name2:
    default_text_color = DELIMITER
    rules = [('name', name0)]
name2.__name__ = 'name'

class name4:
    default_text_color = DELIMITER
    rules = [('name', name0), ('name', RE(r"\w+"), [RE(r"\B|\b")], name2)]
name4.__name__ = 'name'

name5 = """
    truncatewords removetags linebreaksbr yesno get_digit timesince
    random striptags filesizeformat escape linebreaks length_is ljust
    rjust cut urlize fix_ampersands title floatformat capfirst pprint
    divisibleby add make_list unordered_list urlencode timeuntil
    urlizetrunc wordcount stringformat linenumbers slice date dictsort
    dictsortreversed default_if_none pluralize lower join center default
    truncatewords_html upper length phone2numeric wordwrap time
    addslashes slugify first escapejs force_escape iriencode last safe
    safeseq truncatechars localize unlocalize localtime utc timezone
    """.split()

operator_escape = ('operator.escape', [RE(r"\\[\s\S]")])

class string:
    default_text_color = DELIMITER
    rules = [operator_escape]

class _group2:
    default_text_color = DELIMITER
    rules = [
        ('name', name5),
        ('string', RE(r"\""), [RE(r"\"")], string),
        ('string', RE(r"'"), [RE(r"'")], string),
    ]

_group20 = ('_group2', RE(r"\|[A-Za-z]+:?"), [RE(r"(?=%})")], _group2)

class _group1:
    default_text_color = DELIMITER
    ends_with_parent = True
    rules = [('keyword', ['in', 'by', 'as']), _group20]

class template_tag:
    default_text_color = DELIMITER
    rules = [('name', name4, [RE(r"(?=%})")], _group1)]
template_tag.__name__ = 'template-tag'

class template_variable:
    default_text_color = DELIMITER
    rules = [_group20]
template_variable.__name__ = 'template-variable'

rules = [
    ('comment', RE(r"\{%\s*comment\s*%}"), [RE(r"\{%\s*endcomment\s*%}")], comment),
    ('comment', RE(r"\{#"), [RE(r"#}")], comment),
    ('template-tag', RE(r"\{%"), [RE(r"%}")], template_tag),
    ('template-variable', RE(r"\{\{"), [RE(r"}}")], template_variable),
]