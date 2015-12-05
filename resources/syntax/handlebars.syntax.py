# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: handlebars.js
name = 'Handlebars'
file_patterns = ['*.handlebars', '*.hbs', '*.html.hbs', '*.html.handlebars']

flags = re.IGNORECASE | re.MULTILINE

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [
        # {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

builtin_name = """
    each in with if else unless bindattr action collection debugger log
    outlet template unbound view yield
    """.split()

class name0:
    default_text = DELIMITER
    rules = [('builtin-name', builtin_name)]
name0.__name__ = 'name'

class name1:
    default_text = DELIMITER
    rules = [('name', RE(r"[a-zA-Z\.-]+"), [RE(r"\B\b")], name0)]
name1.__name__ = 'name'

class string:
    default_text = DELIMITER
    rules = [
        # {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

class _group0:
    default_text = DELIMITER
    rules = [('string', RE(r"\""), [RE(r"\"")], string)]

class template_tag:
    default_text = DELIMITER
    rules = [('name', name1, [RE(r"(?=\}\})")], _group0)]
template_tag.__name__ = 'template-tag'

class template_variable:
    default_text = DELIMITER
    rules = [('builtin-name', builtin_name)]
template_variable.__name__ = 'template-variable'

rules = [
    ('comment', RE(r"{{!(?:--)?"), [RE(r"(?:--)?}}")], comment),
    ('template-tag', RE(r"\{\{[#\/]"), [RE(r"\}\}")], template_tag),
    ('template-variable', RE(r"\{\{"), [RE(r"\}\}")], template_variable),
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
