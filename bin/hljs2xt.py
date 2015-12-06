#! /usr/bin/env python
# EditXT
# Copyright 2007-2013 Daniel Miller <millerdev@gmail.com>
# 
# This file is part of EditXT, a programmer's text editor for Mac OS X,
# which can be found at http://editxt.org/.
# 
# EditXT is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# EditXT is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with EditXT.  If not, see <http://www.gnu.org/licenses/>.
"""
Convert Highlight.js syntax definition to EditXT syntax definition

Usage:
    syntaxgen.py [--overwrite] [--ignore=<names>] [-v...] <hljs-file> <editxt-file>
    syntaxgen.py -h | --help

Required arguments:
    <hljs-file>     A language syntax defintion file or directory
                    containing language syntax definition files.
    <editxt-file>   A file or directory where syntax definitions
                    will be written.

Options:
    --overwrite         Overwrite syntax definition if present.
    --ignore=<names>    Comma delimited list of filenames to ignore.
    -v --verbose        Verbose output. (-vv for very verbose)
    -h --help           Show this help screen.

Other useful commands:
    ack -l 'automatically generated by hljs2xt' resources/syntax/ | xargs rm -v
    node resources/hljs2json/hljs2json.js resources/hljs2json/hljs/src/languages/...
"""
import json
import os
import re
import sys
import traceback
from collections import defaultdict, OrderedDict
from itertools import chain, count
from os.path import abspath, basename, dirname, exists, isdir, isfile, join, splitext
from subprocess import check_output, CalledProcessError

import docopt

THIS_PATH = abspath(dirname(__file__))
HLJS2JSON = join(THIS_PATH, "../resources/hljs2json/hljs2json.js")
AUTO_COMMENT = "# Syntax definition automatically generated by hljs2xt.py\n"
SKIP_ITEM_KEYS = {"begin"}

sys.path.append(join(dirname(THIS_PATH)))
import editxt.platform as platform
platform.init("test", False)
from editxt.command.wraplines import wraplines


def main(args=None):
    opts = docopt.docopt(__doc__, args)
    hljs_file = opts["<hljs-file>"]
    xt_file = opts["<editxt-file>"]
    overwrite = opts["--overwrite"]
    ignore = {i for i in (opts["--ignore"] or "").split(",") if i}
    verbose = opts["--verbose"]
    if isdir(hljs_file):
        for name in os.listdir(hljs_file):
            if name.endswith(".js"):
                hljs_path = join(hljs_file, name)
                if name in ignore:
                    print("IGNORE", hljs_path)
                    continue
                err = convert_syntax(hljs_path, xt_file, overwrite, verbose)
                if err:
                    print(err, hljs_path)
                    #if err != "SKIP":
                    #    sys.exit(1)
    else:
        err = convert_syntax(hljs_file, xt_file, overwrite, verbose)
        if err == "SKIP":
            sys.exit("refusing to overwrite: " + xt_file)
        elif err:
            sys.exit(err + " " + xt_file)


def convert_syntax(hljs_file, xt_file, overwrite, verbose):
    if isdir(xt_file):
        xt_name = splitext(basename(hljs_file))[0] + ".syntax.py"
        xt_file = join(xt_file, xt_name)
    if exists(xt_file) and not overwrite:
        with open(xt_file) as fh:
            next(fh)  # skip first line
            if next(fh) != AUTO_COMMENT:
                return "SKIP"
    print(hljs_file, "->", xt_file)
    try:
        converted = parse(hljs_file, verbose)
        with open(xt_file, "w", encoding="utf-8") as fh:
            fh.write(converted)
    except CalledProcessError:
        return "ERROR"
    except Exception:
        if verbose:
            traceback.print_exc()
        return "ERROR"


def parse(hljs_file, verbose=False):
    hljs_json = check_output(
        ["node", HLJS2JSON, hljs_file],
        universal_newlines=True
    )
    if verbose > 1:
        print(hljs_json)
    meta = parse_metadata(hljs_file)
    data = DictObj(json.loads(hljs_json))
    definitions = Definitions()
    if data._get("case_insensitive"):
        flags = Assignment("flags", Literal("re.IGNORECASE | re.MULTILINE"))
        flags = definitions.add(flags)
        assert flags == "flags", flags
    syntax = transform_syntax(data, definitions, ())
    definitions.update_recursive_refs(syntax)
    assert not syntax.contains_self, syntax
    assert not syntax.parent_ends, syntax
    aliases = [meta.alias] + data._get("aliases", [])
    return TEMPLATE.format(
        hljs_file=basename(hljs_file),
        name=meta.Language,
        file_patterns=["*." + ext for ext in aliases],
        definitions=definitions,
        rules=pretty_format(syntax.rules),
        recursive_refs=definitions.get_recursive_refs()
    )


def parse_metadata(hljs_file):
    lang = re.compile(r"Language: (.+)$", re.MULTILINE)
    with open(hljs_file, encoding="utf-8") as fh:
        data = fh.read()
    assert "Language" in data
    language = lang.search(data).group(1)
    return DictObj(
        Language=language,
        alias=basename(hljs_file).rsplit(".", 1)[0].lower(),
    )


def transform_syntax(data, definitions, path, name=None):
    def add_words(name_, value, path=None):
        if isinstance(value, str):
            value = [k.split("|")[0] for k in value.split()]
        assignment = Assignment(name_, value)
        ref = definitions.add(assignment)
        rules.append((name_, Literal(ref)))
        if path is not None:
            ref  = "({name!r}, {expr.safe_name})"
            definitions.add_ref(path, ref, name=name_, expr=assignment)

    rules = []
    syntax = SyntaxClass(name, rules)
    keywords = data._get("keywords") or data._get("beginKeywords")
    if keywords:
        if isinstance(keywords, str):
            add_words("keyword", keywords)
        else:
            for word_name, value in sorted(keywords.items()):
                add_words(word_name, value)
    contains = data._get("contains", [])
    if hasattr(contains, "get") and contains.get("type") == "RecursiveRef":
        syntax.recursive_refs += 1
        definitions.add_recursive_ref(
            contains["path"],
            contains["name"],
            expr_ref(name, "rules.extend({ref})"),
            expr=syntax,
        )
        return syntax
    ref = expr_ref(name, "rules")
    definitions.add_ref(path + ("contains",), ref, expr=syntax)
    for i, item in enumerate(contains):
        if item == "self":
            assert name is not None, repr(syntax)
            syntax.contains_self = True
            continue
        if not set(item) - SKIP_ITEM_KEYS:
            rules.append(Comment("# {}".format(ordered_repr(item))))
            continue  # skip
        if item.get("type") == "RecursiveRef":
            syntax.recursive_refs += 1
            rules.append(definitions.add_recursive_ref(
                item["path"],
                item["name"],
                expr_ref(name, "rules[{i}] = {ref}"),
                expr=syntax,
                i=sum(1 for r in rules if not isinstance(r, Comment)),
            ))
            continue
        base_path = path + ("contains", i)
        if "variants" in item:
            def iteritems(item):
                if "contains" in item and \
                        all("contains" in v for v in item["variants"]):
                    print("WARNING variants mask contains in {} {}".format(
                        syntax.safe_name, base_path))
                for j, variant in enumerate(item["variants"]):
                    var = item.copy()
                    var.update(variant)
                    if "contains" in variant:
                        var_path = ("variants", j)
                    else:
                        var_path = ()
                    yield var, base_path + var_path
            items = iteritems(item)
        else:
            items = [(item, base_path)]
        for item, item_path in items:
            original = item
            plain = "className" not in item
            if plain:
                item = dict(item, className=definitions.get_name(item))
            item = DictObj(item, _parent=data)
            if "end" in item or item._get("endsWithParent") \
                    or "contains" in item or "keywords" in item \
                    or "beginKeywords" in item or "starts" in item:
                rng = transform_range(item, definitions, item_path)
                if item._get("endsParent"):
                    end_name = definitions.get_name(rng)
                    end = SyntaxClass(item.className, [rng])
                    end_name = definitions.add(end)
                    syntax.parent_ends.append(Literal(end_name))
                else:
                    ref = expr_ref(name, "rules[{i}]")
                    index = sum(1 for r in rules if not isinstance(r, Comment))
                    definitions.add_ref(item_path, ref, expr=syntax, i=index)
                    rules.append(rng)
            elif not plain and "begin" in item:
                add_words(item.className, [regex(item.begin)], item_path)
            else:
                rules.append(Comment("# {}".format(ordered_repr(original))))
    return syntax


def transform_range(item, definitions, path):
    name = item.className

    begin = transform_begin(item, definitions)
    end = transform_end(item, definitions)

    content = ()
    ends = []
    if "keywords" in item or item._get("contains"):
        syntax = transform_syntax(item, definitions, path, name)
        if syntax or syntax.contains_self:
            syntax_name = definitions.add(syntax)
            content = (Literal(syntax_name),)
        ends.extend(syntax.parent_ends)

    if "subLanguage" in item:
        if item._get("subLanguageMode") == "continuous":
            print("continuous sub-language not implemented")
        else:
            if content:
                print("WARNING discarding range rules for sub language")
                print(syntax)
            if item.subLanguage:
                content = (item.subLanguage,)
            else:
                print("auto sub-language detection not implemented")

    if item._get("starts"):
        start = SyntaxClass(name, [(name, begin, [end]) + content])
        start_name = definitions.add(start)
        begin = Literal(start_name)
        if isinstance(item.starts, str):
            content = (Literal(item.starts),)
            end = transform_end(item._parent, definitions, lookahead=True)
        else:
            args = {"_parent": item._parent}
            if "className" not in item.starts:
                args["className"] = definitions.get_name(item.starts)
            next_ = DictObj(item.starts, **args)
            sub_path = path + ("starts",)
            sub = transform_syntax(next_, definitions, sub_path, next_.className)
            sub_name = definitions.add(sub)
            content = (Literal(sub_name),)
            if "end" in next_:
                end = transform_end(next_, definitions)
            else:
                end = transform_end(item._parent, definitions, lookahead=True)

    return (name, begin, [end] + ends) + content


def transform_begin(item, definitions):
    if "beginKeywords" in item:
        begin = regex(r"\b(" + "|".join(item.beginKeywords.split()) + ")")
    elif "begin" in item:
        begin = regex(item.begin)
    else:
        begin = RE(r"\B|\b")
    if begin != RE(r"\B|\b") and not begin.pattern.startswith(("(?=", "(?<=")):
        if item._get("excludeBegin") and not str(item.className).startswith("_"):
            assert not item._get("returnBegin"), item - {"contains", "_parent"}
            #begin = RE(r"(?<={})".format(begin.pattern))
            rules = [Literal("('_{}', [{!r}])".format(item.className, begin))]
            syntax = SyntaxClass("_{}".format(item.className), rules)
            begin = Literal(definitions.add(syntax))
        elif item._get("returnBegin"):
            begin = RE(r"(?={})".format(begin.pattern))
    return begin


def transform_end(item, definitions, lookahead=False):
    lookahead = lookahead or item._get("end") and item._get("returnEnd")
    if item._get("end"):
        end = regex(item.end)
        if item._get("excludeEnd") \
                and not str(item.className).startswith("_") \
                and not lookahead \
                and not end.pattern.startswith("(?="):
            #end = end.lookahead()
            rules = [Literal("('_{}', [{!r}])".format(item.className, end))]
            syntax = SyntaxClass("_{}".format(item.className), rules)
            return Literal(definitions.add(syntax))
        elif lookahead and not end.is_lookahead():
            end = end.lookahead()
        return end
    # matches nothing -> end with parent
    return RE(r"\B\b")


def regex(obj):
    if isinstance(obj, str):
        return RE(obj)
    if obj["type"] == "RegExp":
        return RE(obj["pattern"])
    raise Error("unknown regex type: {}".format(obj))


class Definitions:

    def __init__(self):
        self.items = OrderedDict()
        self.names = ("_group{}".format(i) for i in count())
        self.paths = {}
        self.deferred_refs = defaultdict(list)
        self.recursive_refs = []

    def add(self, expr):
        self.update_recursive_refs(expr)
        name = self.find(expr)
        if name is not None:
            return name
        name = self.get_name(expr, expr.name)
        if name.name != expr.name.name:
            expr.safe_name = name
        self.items[name] = expr
        return name

    def add_ref(self, path, template, **args):
        self.paths[path] = (template, args)

    def add_recursive_ref(self, path, name, template, **args):
        path = tuple(path)
        if path not in self.paths:
            return Comment("# {}".format(ordered_repr(name)))
        ref_template, ref_args = self.paths[path]
        ref = RecursiveRef(ref_template, ref_args)
        deferred = (ref, path, name, template, args)
        self.deferred_refs[id(args["expr"])].append(deferred)
        return ref

    def update_recursive_refs(self, expr):
        if id(expr) not in self.deferred_refs:
            return
        for ref, path, name, template, args in self.deferred_refs[id(expr)]:
            expr = self.find_item(ref.args["expr"])
            if expr is not None:
                ref.update(expr)
            else:
                assert path in self.paths, (path, name, template, args)
                self.recursive_refs.append((path, name, template, args))

    def get_recursive_refs(self):
        def deref(args):
            def find(obj):
                found = self.find_item(obj)
                return obj if found is None else found
            return {k: find(v) for k, v in args.items()}
        defs = []
        for path, name, template, args in self.recursive_refs:
            ref_template, ref_args = self.paths[path]
            ref = ref_template.format(**deref(ref_args))
            assignment = template.format(ref=ref, **deref(args))
            if assignment not in defs:
                defs.append(assignment)
        if defs:
            defs.sort(key=lambda x: 1 if ".extend(" in x else 0)
            defs.insert(0, "")
            defs.insert(0, "")
        return "\n".join(defs)

    def get(self, name, default=None):
        return self.items.get(name, default)

    def get_name(self, value, name=None, exchars=re.compile(r"\W+")):
        if not name:
            return Name(next(self.names), value)
        if isinstance(name, Name):
            name = name.name
        name = exchars.sub("_", name)
        if name[0] in "0123456789":
            name = "_" + name
        temp = name
        number = count()
        while name in self or name in PYTHON_KEYWORDS:
            name = temp + str(next(number))
        return Name(name, value)

    def find(self, obj):
        for name, item in self.items.items():
            if obj == item:
                return name
        return None

    def find_item(self, obj):
        for item in self:
            if obj == item:
                return item
        return None

    def __contains__(self, name):
        return name in self.items

    def __iter__(self):
        return iter(self.items.values())

    def __repr__(self):
        if not self.items:
            return ""
        defs = []
        for expr in self.items.values():
            defs.append(repr(expr))
        return "\n" + "\n\n".join(defs)


class Name:

    def __init__(self, name, value=None):
        if isinstance(name, Name):
            name = name.name
            assert isinstance(name, str)
        self.name = name
        self.value = value if value is not None else object()

    def __bool__(self):
        return bool(self.name)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        return isinstance(other, type(self)) and (
            self.name == other.name or
            self.value == other.value
        )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name or ""

    def __repr__(self):
        return repr(self.__str__())


class Literal:

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.value == other.value

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        if isinstance(self.value, Name):
            return str(self.value)
        return self.value


class RecursiveRef(Literal):

    def __init__(self, template, args):
        self.value = "None,  # " + template.format(**args)
        self.template = template
        self.args = args

    def update(self, expr):
        assert "expr" in self.args, self.args
        self.args["expr"] = expr
        self.value = self.template.format(**self.args)

    def __eq__(self, other):
        expr = self.args["expr"]
        if isinstance(other, tuple) and repr(self).startswith("("):
            ns = {expr.safe_name: Literal(expr.safe_name)}
        else:
            ns = {expr.safe_name: expr}
        obj = eval(repr(self), {}, ns)
        return obj == other or super().__eq__(other)


def expr_ref(name, attribute):
    if name is None:
        return attribute
    return "{expr.safe_name}." + attribute


class Comment(Literal):

    def update(self, expr):
        pass

    def __eq__(self, other):
        return isinstance(other, type(self))


class RE:

    def __init__(self, pattern):
        self.pattern = pattern.replace("\n", r"\n").replace("\r", r"\r")

    def __bool__(self):
        return bool(self.pattern)

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.pattern == other.pattern

    def __ne__(self, other):
        return not self == other

    def __or__(self, other):
        if other:
            if not self:
                return other
            return RE(self.pattern + "|" + other.pattern)
        return self

    def __repr__(self, paren=re.compile(r"(^|[^\\](?:\\\\)*)\((?!\?)"),
                       group=re.compile(r"\$\d")):
        pattern = paren.sub(r"\1(?:", self.pattern) # paren -> non-capturing paren
        assert not group.search(pattern), "illegal group ref: " + self.pattern
        return 'RE(r"{}")'.format(pattern.replace('"', '\\"'))

    def is_lookahead(self):
        # WARNING returns wrong result (False) for /(?=\))/
        return self.pattern.startswith("(?=") and self.pattern.endswith(")") \
                and ")" not in self.pattern[3:-1]

    def lookahead(self):
        return RE(r"(?={})".format(self.pattern))


class Assignment:

    def __init__(self, name, value):
        self.safe_name = Name(name, value)
        self.value = value

    @property
    def name(self):
        return self.safe_name

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.value == other.value

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return "{} = {}".format(self.safe_name, pretty_format(self.value))


class SyntaxClass:

    def __init__(self, name, rules):
        self.name = Name(name, self)
        self.rules = rules
        self._safe_name = None
        self.contains_self = False
        self.parent_ends = []
        self.recursive_refs = 0

    @property
    def safe_name(self):
        return self._safe_name or self.name
    @safe_name.setter
    def safe_name(self, value):
        self._safe_name = value

    @staticmethod
    def _get_names_from_range(rng):
        names = []
        if not isinstance(rng, Literal):
            if isinstance(rng[1], Literal):
                names.append(rng[1].value)
            for end in rng[2]:
                if isinstance(end, Literal):
                    names.append(end.value)
            if len(rng) > 3 and isinstance(rng[3], Literal):
                names.append(rng[3].value)
        return names

    def __bool__(self):
        return bool(self.rules or self.recursive_refs)

    def __eq__(self, other):
        return isinstance(other, type(self)) and (
            self.name.name == other.name.name and
            self.rules == other.rules
        )

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        # by design: name == None -> syntax error
        lines = ["class {}:".format(self.safe_name)]
        lines.append("    default_text = DELIMITER")
        rules = pretty_format(self.rules, 4).lstrip()
        lines.append("    rules = {}".format(rules))
        if self._safe_name:
            lines.append("{}.__name__ = {!r}".format(self.safe_name, self.name))
        return "\n".join(lines)


class DictObj:

    def __init__(self, _data=None, **data):
        if _data is None:
            _data = data
        elif data:
            _data.update(data)
        self._data = _data

    def __contains__(self, name):
        return name in self._data

    def __getattr__(self, name):
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError("{!r} not in {!r}".format(
                name,
                list(self._data)
            ))

    def __getitem__(self, name):
        return self._data[name]

    def __repr__(self):
        return repr(self._data)

    def __sub__(self, other):
        items = {k: v for k, v in self._data.items() if k not in other}
        return DictObj(**items)

    def _get(self, name, default=None):
        return self._data.get(name, default)


def pretty_format(obj, indent=0, width=72):
    rep = repr(obj)
    if len(rep) < width - indent and not rep.startswith("#") and "# " not in rep:
        return rep
    if isinstance(obj, list) and all(isinstance(x, str) and " " not in x for x in obj):
        indent += 4
        lines = iter([' ' * indent + " ".join(obj)])
        opts = DictObj(wrap_column=width, indent=True)
        return '"""\n{items}{indent}""".split()'.format(
            indent=' ' * indent,
            items="\n".join(wraplines(lines, opts))
        )
    if type(obj) in ITEM_FORMATS:
        return format_items(obj, indent, width)
    return rep

def format_items(obj, indent, width):
    open, format, close, iteritems = ITEM_FORMATS[type(obj)]
    prefix = " " * indent
    item_prefix = prefix + "    "
    parts = [prefix + open]
    parts.extend(item_prefix + format(i, indent + 4).lstrip() + ","
                 for i in iteritems(obj))
    parts.append(prefix + close)
    return "\n".join(parts)

ITEM_FORMATS = {
    list: ("[", pretty_format, "]", lambda obj: obj),
    #tuple: ("(", pretty_format, ")", lambda obj: obj),
}

def ordered_repr(obj, seen=None):
    if seen is None:
        seen = set()
    if id(obj) in seen:
        return "..."
    seen.add(id(obj))
    if isinstance(obj, dict):
        items = ("%r: %s" % (k, ordered_repr(v, seen))
                 for k, v in sorted(obj.items()))
        return "{%s}" % ", ".join(items)
    if isinstance(obj, list):
        return "[%s]" % ", ".join(ordered_repr(v, seen) for v in obj)
    if isinstance(obj, tuple):
        return "(%s)" % ", ".join(ordered_repr(v, seen) for v in obj)
    return repr(obj)


class Error(Exception): pass


TEMPLATE = """
# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: {hljs_file}
name = {name!r}
file_patterns = {file_patterns!r}
{definitions}

rules = {rules}{recursive_refs}

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
""".lstrip()

PYTHON_KEYWORDS = set("""
    and       del       from      not       while    
    as        elif      global    or        with     
    assert    else      if        pass      yield    
    break     except    import    class     in       
    raise     continue  finally   is        return   
    def       for       lambda    try       nonlocal
    RE        DELIMITER
    comment_token       default_text        delimited_ranges
    disabled  ends      file_patterns       name
    registry  whitespace          word_groups
    rules
    """.split())

if __name__ == "__main__":
    main()
