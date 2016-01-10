# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: stylus.js
name = 'Stylus'
file_patterns = ['*.stylus', '*.styl']

operator_escape = ('operator.escape', [RE(r"\\[\s\S]")])

class string:
    default_text_color = DELIMITER
    rules = [operator_escape]

string0 = ('string', RE(r"\""), [RE(r"\"")], string)

string1 = ('string', RE(r"'"), [RE(r"'")], string)

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

number = ('number', [RE(r"#(?:[a-fA-F0-9]{6}|[a-fA-F0-9]{3})")])

class _group1:
    default_text_color = DELIMITER
    rules = [('selector-class', [RE(r"\.[a-zA-Z][a-zA-Z0-9_-]*")])]

class _group2:
    default_text_color = DELIMITER
    rules = [('selector-id', [RE(r"\#[a-zA-Z][a-zA-Z0-9_-]*")])]

class _group3:
    default_text_color = DELIMITER
    rules = [('selector-tag', [RE(r"\b[a-zA-Z][a-zA-Z0-9_-]*")])]

variable = ('variable', [RE(r"\$[a-zA-Z]\w*")])

number0 = [
    RE(r"\b\d+(?:\.\d+)?(?:%|em|ex|ch|rem|vw|vh|vmin|vmax|cm|mm|in|pt|pc|px|deg|grad|rad|turn|s|ms|Hz|kHz|dpi|dpcm|dppx)?"),
]

number1 = ('number', number0)

number2 = ('number', [RE(r"\b\d+(?:\.\d+)?")])

class params:
    default_text_color = DELIMITER
    rules = [number, variable, string1, number1, number2, string0]

class function:
    default_text_color = DELIMITER
    rules = [
        ('title', [RE(r"\b[a-zA-Z][a-zA-Z0-9_-]*")]),
        ('params', RE(r"\("), [RE(r"\)")], params),
    ]

attribute = [
    RE(r"\b(?:z-index|word-wrap|word-spacing|word-break|width|widows|white-space|visibility|vertical-align|unicode-bidi|transition-timing-function|transition-property|transition-duration|transition-delay|transition|transform-style|transform-origin|transform|top|text-underline-position|text-transform|text-shadow|text-rendering|text-overflow|text-indent|text-decoration-style|text-decoration-line|text-decoration-color|text-decoration|text-align-last|text-align|table-layout|tab-size|right|resize|quotes|position|pointer-events|perspective-origin|perspective|page-break-inside|page-break-before|page-break-after|padding-top|padding-right|padding-left|padding-bottom|padding|overflow-y|overflow-x|overflow-wrap|overflow|outline-width|outline-style|outline-offset|outline-color|outline|orphans|order|opacity|object-position|object-fit|normal|none|nav-up|nav-right|nav-left|nav-index|nav-down|min-width|min-height|max-width|max-height|mask|marks|margin-top|margin-right|margin-left|margin-bottom|margin|list-style-type|list-style-position|list-style-image|list-style|line-height|letter-spacing|left|justify-content|initial|inherit|ime-mode|image-resolution|image-rendering|image-orientation|icon|hyphens|height|font-weight|font-variant-ligatures|font-variant|font-style|font-stretch|font-size-adjust|font-size|font-language-override|font-kerning|font-feature-settings|font-family|font|float|flex-wrap|flex-shrink|flex-grow|flex-flow|flex-direction|flex-basis|flex|filter|empty-cells|display|direction|cursor|counter-reset|counter-increment|content|columns|column-width|column-span|column-rule-width|column-rule-style|column-rule-color|column-rule|column-gap|column-fill|column-count|color|clip-path|clip|clear|caption-side|break-inside|break-before|break-after|box-sizing|box-shadow|box-decoration-break|bottom|border-width|border-top-width|border-top-style|border-top-right-radius|border-top-left-radius|border-top-color|border-top|border-style|border-spacing|border-right-width|border-right-style|border-right-color|border-right|border-radius|border-left-width|border-left-style|border-left-color|border-left|border-image-width|border-image-source|border-image-slice|border-image-repeat|border-image-outset|border-image|border-color|border-collapse|border-bottom-width|border-bottom-style|border-bottom-right-radius|border-bottom-left-radius|border-bottom-color|border-bottom|border|background-size|background-repeat|background-position|background-origin|background-image|background-color|background-clip|background-attachment|background|backface-visibility|auto|animation-timing-function|animation-play-state|animation-name|animation-iteration-count|animation-fill-mode|animation-duration|animation-direction|animation-delay|animation|align-self|align-items|align-content)\b"),
]

rules = [
    ('keyword', ['if', 'else', 'for', 'in']),
    string0,
    string1,
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment),
    number,
    ('_group1', RE(r"(?=\.[a-zA-Z][a-zA-Z0-9_-]*[\.\s\n\[\:,])"), [RE(r"\B\b")], _group1),
    ('_group2', RE(r"(?=\#[a-zA-Z][a-zA-Z0-9_-]*[\.\s\n\[\:,])"), [RE(r"\B\b")], _group2),
    ('_group3', RE(r"(?=\b(?:a|abbr|address|article|aside|audio|b|blockquote|body|button|canvas|caption|cite|code|dd|del|details|dfn|div|dl|dt|em|fieldset|figcaption|figure|footer|form|h1|h2|h3|h4|h5|h6|header|hgroup|html|i|iframe|img|input|ins|kbd|label|legend|li|mark|menu|nav|object|ol|p|q|quote|samp|section|span|strong|summary|sup|table|tbody|td|textarea|tfoot|th|thead|time|tr|ul|var|video)[\.\s\n\[\:,])"), [RE(r"\B\b")], _group3),
    # ignore {'begin': '&?:?:\\b(after|before|first-letter|first-line|active|first-child|focus|hover|lang|link|visited)[\\.\\s\\n\\[\\:,]'},
    # ignore {'begin': '@(charset|css|debug|extend|font-face|for|import|include|media|mixin|page|warn|while)\\b'},
    variable,
    number1,
    number2,
    ('function', RE(r"(?=^[a-zA-Z][a-zA-Z0-9_-]*\(.*\))"), [RE(r"\B\b")], function),
    ('attribute', attribute),
]
