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
    <hljs-file>     A language syntax definition file or directory
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
    rsync -aHv --delete dmiller@octagon:code/EditXT/resources/hljs2json/hljs/ \
                                                    resources/hljs2json/hljs/
    ./bin/hljs2xt.py -v resources/hljs2json/hljs/src/languages/ resources/syntax/
    git apply resources/hljs2json/markdown-syntax.patch resources/syntax/markdown.syntax.py
"""
import json
import os
import re
import sys
import traceback
from bdb import BdbQuit
from collections import defaultdict, OrderedDict
from contextlib import contextmanager
from itertools import chain, count
from os.path import abspath, basename, dirname, exists, isdir, isfile, join, splitext
from subprocess import check_output, CalledProcessError

import docopt

THIS_PATH = abspath(dirname(__file__))
HLJS2JSON = join(THIS_PATH, "../resources/hljs2json/hljs2json.js")
AUTO_COMMENT = "# Syntax definition automatically generated by hljs2xt.py\n"
IGNORE_ITEM_KEYS = {"begin", "relevance"}

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
    except (BdbQuit, KeyboardInterrupt):
        raise
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
    if verbose > 2:
        print(hljs_json)
    meta = parse_metadata(hljs_file)
    data = DictObj(json.loads(hljs_json))
    definitions = Definitions(verbose > 1)
    if data._get("case_insensitive"):
        flags = Assignment("flags", Literal("re.IGNORECASE | re.MULTILINE"))
        flags = definitions.add(flags)
        assert flags == "flags", flags
    syntax = transform_syntax(data, definitions, ())
    syntax.finalize_recursive_refs(definitions.recursive)
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


def transform_syntax(data, definitions, path, name=None, parent_ends=None):
    syntax = SyntaxClass(name, ends_with_parent=data._get("endsWithParent"))
    if data._get("keywords"):
        for word_name, words in iter_keyword_sets(data.keywords):
            syntax.add_rule(definitions.add_words(word_name, words))
    if data._get("beginKeywords"):
        words = split_keywords(data.beginKeywords)
        syntax.add_rule(definitions.add_words("keyword", words))

    contains = data._get("contains", [])
    if hasattr(contains, "get") and contains.get("type") == "RecursiveRef":
        definitions.recursive.add_rules_ref(syntax, contains)
        return syntax

    definitions.recursive[path + ("contains",)] = syntax
    for i, item in enumerate(contains):
        if item == "self":
            assert name is not None, repr(syntax)
            syntax.contains_self = True
            continue
        if item.get("type") == "RecursiveRef":
            syntax.add_recursive_ref(item)
            continue
        base_path = path + ("contains", i)
        if "variants" in item:
            if "contains" in item:
                # create rule in case a variant masks it and references it
                cont = definitions.new_dict_obj(item)
                with definitions.new_rule(cont, base_path) as rule:
                    rule.range = transform_range(cont, definitions, base_path, parent_ends)
            items = list(iter_variants(item, syntax, base_path))
            paths = [item_path for x, item_path, x in items]
            #print(base_path, '-->', paths)
            definitions.recursive[base_path] = VariantsRef(paths)
        else:
            items = [(item, base_path, base_path)]
        for item, item_path, child_path in items:
            original, item = item, definitions.new_dict_obj(item)
            has_name = not item.className.startswith("_")
            if "end" in item or item._get("endsWithParent") \
                    or "contains" in item or "keywords" in item \
                    or "beginKeywords" in item or "starts" in item:
                with definitions.new_rule(item, item_path) as rule:
                    rule.range = transform_range(item, definitions, child_path, parent_ends)
                if item._get("endsParent"):
                    end = SyntaxClass(item.className, [rule])
                    end_name = definitions.add(end)
                    syntax.parent_ends.append(Literal(end_name))
                else:
                    syntax.add_rule(rule)
            elif has_name and "begin" in item:
                words = [regex(item.begin)]
                rule = definitions.add_words(item.className, words, item_path)
                syntax.add_rule(rule)
            else:
                syntax.add_rule(definitions.ignore(original, item_path))

    return syntax


def iter_variants(item, syntax, base_path):
    for j, variant in enumerate(item["variants"]):
        var = item.copy()
        del var['variants']
        var.update(variant)
        var_path = base_path + ("variants", j)
        if "contains" in item:
            if "contains" in variant:
                print("WARNING {} masks contains in {}".format(
                      var_path, syntax.safe_name))
            else:
                assert "starts" not in item, \
                    DictObj(item) - {"contains", "variants", "keywords"}
            child_path = var_path
        elif "starts" in item and "starts" not in variant:
            assert "contains" not in item, \
                DictObj(item) - {"contains", "variants", "keywords"}
            child_path = base_path
        else:
            child_path = var_path
        yield var, var_path, child_path


def transform_range(item, definitions, path, parent_ends):
    name = item.className

    begin = transform_begin(item, definitions)
    ends = transform_ends(item, definitions, parent_ends)

    content = ()
    if "keywords" in item or item._get("contains") \
            or any("contains" in v for v in item._get("variants", [])):
        syntax = transform_syntax(item, definitions, path, name, ends)
        content = (SyntaxRef(definitions.add(syntax), syntax),)
        ends.extend(syntax.parent_ends)

    if "subLanguage" in item:
        if item._get("subLanguageMode") == "continuous":
            print("continuous sub-language not implemented")
        else:
            if item.subLanguage:
                if content:
                    print("WARNING discarding range rules for sub language")
                    print(syntax)
                content = (transform_sublanguage(item.subLanguage),)
            else:
                print("auto sub-language detection not implemented")

    if item._get("starts"):
        rules = []
        if "keywords" in item and "begin" in item and "end" not in item:
            begin_re = re.compile(begin.pattern + "$")
            for word_name, words in iter_keyword_sets(item.keywords):
                words = [w for w in words if begin_re.match(w)]
                if words:
                    rules.append(definitions.add_words(word_name, words))
        rules.append(definitions.add_range((name, begin, ends) + content))
        begin_syntax = SyntaxClass(name, rules, is_delim=True)
        begin = SyntaxRef(definitions.add(begin_syntax), begin_syntax)
        ends = []
        if isinstance(item.starts, str):
            content = (item.starts,)
            raise NotImplementedError("how to end? {}".format(
                    item - {"contains", "variants", "keywords"}))
        else:
            next_item = definitions.new_dict_obj(item.starts, _parent_starts=begin)
            next_path = path + ("starts",)
            with definitions.new_rule(next_item, next_path) as rule:
                rule.range = rng = transform_range(
                    next_item, definitions, next_path, parent_ends)
            if next_item._get("starts"):
                begin = rng[1]
            ends = rng[2]
            content = rng[3:]

    return (name, begin, ends) + content


def transform_begin(item, definitions):
    if "_parent_starts" in item:
        assert "begin" not in item and "beginKeywords" not in item, \
            item - {"contains", "variants", "starts"}
        return item._parent_starts
    if "beginKeywords" in item:
        #assert "begin" not in item, item - {"contains"}
        begin = regex(r"\b(" + "|".join(item.beginKeywords.split()) + ")")
    elif "begin" in item:
        begin = regex(item.begin)
    else:
        begin = RE(r"\B|\b")
    if begin != RE(r"\B|\b") and not begin.pattern.startswith(("(?=", "(?<=")):
        if item._get("excludeBegin") and not item.className.startswith("_"):
            assert not item._get("returnBegin"), item - {"contains"}
            #begin = RE(r"(?<={})".format(begin.pattern))
            name = "_{}".format(item.className)
            rules = [definitions.add_words(name, [begin])]
            syntax = SyntaxClass(name, rules, is_delim=True)
            begin = SyntaxRef(definitions.add(syntax), syntax)
        elif item._get("returnBegin") and (item._get("end")
                # does not have ignored contained element with same pattern
                or not any(sub.get("begin") == item.begin
                            and not (set(sub) - IGNORE_ITEM_KEYS)
                            for sub in item._get("contains", []))):
            begin = begin.lookahead()
    return begin


def transform_ends(item, definitions, parent_ends):
    if item._get("end"):
        end = regex(item.end)
        if item._get("returnEnd"):
            end = end.lookahead()
        elif item._get("excludeEnd") \
                and not item.className.startswith("_") \
                and not end.pattern.startswith("(?="):
            name = "_{}".format(item.className)
            rules = [definitions.add_words(name, [end])]
            syntax = SyntaxClass(name, rules, is_delim=True)
            non_lookahead_pattern = end.non_lookahead_pattern
            end = SyntaxRef(definitions.add(syntax), syntax)
            end.non_lookahead_pattern = non_lookahead_pattern
        return [end]
    elif "starts" in item or item._get("returnBegin"):
        # The range with "starts" or "returnBegin" and no "end" should
        # end after matching a single token.
        return [RE(r"\B|\b")]
    # matches nothing -> end with parent
    if not parent_ends:
        return [RE(r"\B|\b")]
    pattern = "|".join(e.non_lookahead_pattern for e in parent_ends)
    return [RE(pattern).lookahead()]


def iter_keyword_sets(keywords):
    if isinstance(keywords, str):
        yield "keyword", split_keywords(keywords)
    else:
        for word_name, words in sorted(keywords.items()):
            yield word_name, split_keywords(words)

def split_keywords(words):
    if isinstance(words, str):
        return [k.split("|")[0] for k in words.split()]
    return words


def transform_sublanguage(lang):
    if isinstance(lang, str):
        return lang
    print("WARNING auto-language detection not implemented: {}".format(lang))
    assert isinstance(lang, list), lang
    return "javascript" if "javascript" in lang else lang[0]


def regex(obj):
    if isinstance(obj, str):
        return RE(obj)
    if obj["type"] == "RegExp":
        return RE(obj["pattern"])
    raise Error("unknown regex type: {}".format(obj))


class RE:

    def __init__(self, pattern, non_lookahead_pattern=None):
        self.pattern = pattern.replace("\n", r"\n").replace("\r", r"\r")
        assert non_lookahead_pattern is None or pattern.startswith(r"(?="), pattern
        self._non_lookahead_pattern = non_lookahead_pattern

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

    def __repr__(self, paren=re.compile(r"(^|(?<=[^\\])(?:\\\\)*)\((?!\?)"),
                       capture_all=re.compile(r"(^|(?<=[^\\])(?:\\\\)*)\[\^\]"),
                       group=re.compile(r"\$\d")):
        pattern = paren.sub(r"\1(?:", self.pattern) # paren -> non-capturing paren
        pattern = capture_all.sub(r"\1[\s\S]", pattern) # [^] -> [\s\S]
        assert not group.search(pattern), "illegal group ref: " + self.pattern
        return 'RE(r"{}")'.format(pattern.replace('"', '\\"'))

    def is_lookahead(self):
        # WARNING returns wrong result (False) for /(?=\))/
        return self._non_lookahead_pattern is not None \
            or self.pattern.startswith("(?=") and self.pattern.endswith(")") \
                and ")" not in self.pattern[3:-1]

    def lookahead(self):
        if self.is_lookahead() or self.pattern == "$":
            return self
        return RE(r"(?={})".format(self.pattern), self.pattern)

    @property
    def non_lookahead_pattern(self):
        if self._non_lookahead_pattern is not None:
            return self._non_lookahead_pattern
        if self.is_lookahead():
            return self.pattern[3:-1]
        return self.pattern


class Definitions:

    def __init__(self, verbose=False):
        self.items = OrderedDict()
        self.names = ("_group{}".format(i) for i in count())
        self.recursive = Recurses(self, verbose=verbose)

    def add(self, expr):
        expr.finalize_recursive_refs(self.recursive)
        name = self.find(expr)
        if name is None:
            name = self.get_name(expr, expr.name)
            if name.name != expr.name.name:
                expr.safe_name = name
            self.items[name] = expr
        return name

    def new_rule(self, item, path):
        @contextmanager
        def context():
            rule = Rule(item.className, Placeholder(item))
            if path not in self.recursive:
                self.recursive[path] = rule
            yield rule
            self.add(rule)
        return context()

    def add_words(self, name, words, path=None):
        assert isinstance(name, str), name
        rule = (name, words)
        if len(repr(rule)) > 80:
            words_name = self.add(Assignment(*rule))
            rule = (name, Literal(words_name))
        return self.add_range(rule, path)

    def add_range(self, rng, path=None):
        rule = Rule(rng[0], rng)
        self.add(rule)
        if path is not None and path not in self.recursive:
            self.recursive[path] = rule
        return rule

    def ignore(self, item, path):
        if isinstance(item, dict) and item.get("className", "").startswith("_"):
            item = dict(item)
            item.pop("className")
        comment = Comment("# ignore {}".format(ordered_repr(item)))
        self.recursive[path] = comment
        return comment

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

    def new_dict_obj(self, item, **kw):
        if "className" not in item:
            assert "className" not in kw, kw
            try:
                begin = item["begin"]
                if isinstance(begin, dict):
                    begin = begin["pattern"]
                name = DEFAULT_COLORS[begin]
            except KeyError:
                name = self.get_name(item).name
            kw["className"] = name
        return DictObj(item, **kw)

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
        statements = []
        for expr in self.items.values():
            if isinstance(expr, Rule):
                if expr.assignment is None:
                    continue
                rule = Literal(expr.repr_rule_tuple(expr.range, ""))
                expr = Literal(expr.assignment.repr_assignment(rule))
            elif isinstance(expr, SyntaxClass) and not expr:
                expr = Literal("#" + repr(expr).replace("\n", "\n#"))
            statements.append(repr(expr))
        return "\n" + "\n\n".join(statements)

    def get_recursive_refs(self):
        statements = []
        rules_refs = []
        for expr in self.items.values():
            if isinstance(expr, SyntaxClass):
                statements.extend(repr(r) for r in expr.iter_recursive_refs())
                rules_refs.extend(expr.recursive_rules_refs)
        statements.extend(repr(r) for r in rules_refs)
        if statements:
            statements.insert(0, "")
            statements.insert(0, "")
        return "\n".join(statements)


class Recurses:

    def __init__(self, definitions, verbose=False):
        self.pathmap = {}
        self.placeholders = defaultdict(list)
        self.definitions = definitions
        self.verbose = verbose

    def __setitem__(self, path, obj):
        if self.verbose:
            print(path, obj.safe_name if isinstance(obj, Rule) else obj)
        assert isinstance(obj, (Rule, Literal, VariantsRef, SyntaxClass)), (type(obj), obj)
        if path in self.placeholders:
            assert isinstance(obj, Rule), obj
            if obj.assignment is None:
                obj.setup_assignment()
            for rule in self.placeholders[path]:
                rule.value = obj
        #if path in self.pathmap:
        #    assert self.pathmap[path] == obj, (self.pathmap[path], obj)
        self.pathmap[path] = obj

    def __getitem__(self, item):
        if isinstance(item, dict):
            desc = item["desc"]
            path = tuple(item["path"])
        else:
            path = desc = item
        try:
            return self.pathmap[path]
        except KeyError:
            raise KeyError(Literal("{} {}".format(path, desc)))

    def __contains__(self, path):
        return path in self.pathmap

    def add_rules_ref(self, syntax, item):
        syntax.add_recursive_rules_ref(self[item])

    def iter_rules(self, item, syntax):
        def deref(rule, path):
            if isinstance(rule, Rule):
                found = self.definitions.find_item(rule)
                if found is not None:
                    rule = found
                if rule.assignment is None:
                    # TODO don't do this for clojure _group20
                    rule.setup_assignment()
                return RecursiveRule(rule, found is None)
            if isinstance(rule, Comment):
                return rule
            raise NotImplementedError("{} {} -> {!r}".format(path, desc, rule))
        desc = item["desc"]
        path = tuple(item["path"])
        ref = self[item]
        if isinstance(ref, VariantsRef):
            for path in ref.paths:
                try:
                    ref = self[path]
                except KeyError:
                    rule = RecursiveRule(Placeholder(path), True)
                    self.placeholders[path].append(rule)
                else:
                    rule = deref(ref, path)
                yield rule
        else:
            yield deref(ref, path)

    def dedupe(self, rule, path=None):
        found = self.definitions.find_item(rule)
        if found is None:
            assert isinstance(rule, RecursiveRule), rule
            # maybe the wrong place for this
            rule.recursive = True
        else:
            if found is rule:
                # could be problematic:
                # just because rule is in definitions does not mean
                # it does not need an assignment (clojure works though)
                return rule
            if path is not None:
                self[path] = found
            rule = found
        return rule


class ValueType:

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.value == other.value

    def __ne__(self, other):
        return not self == other


class Literal(ValueType):

    def __repr__(self):
        if isinstance(self.value, Name):
            return str(self.value)
        return self.value


class Placeholder(Literal):

    def __init__(self, item):
        self.value = "placeholder for {}".format(ordered_repr(item))


class SyntaxRef(Literal):

    def __init__(self, name, syntax):
        self.value = name
        self.syntax = syntax

    def __bool__(self):
        return bool(self.syntax)


class Comment(Literal):

    def __eq__(self, other):
        return isinstance(other, type(self))

    def __len__(self):
        return 0


class RecursiveRef(ValueType):
    """Container: value contains path to recursive element"""


class VariantsRef:

    def __init__(self, paths):
        self.paths = paths

    def __repr__(self):
        return "<{} {}>".format(type(self).__name__, self.paths)


class RulesExtension:

    def __init__(self, dst, src):
        self.src = src
        self.dst = dst

    def __repr__(self):
        prefix = '' if self.src else '#'
        ref = self.dst.ref("rules.extend({ref})", ref=self.src.ref("rules"))
        return prefix + repr(ref)

class Ref:

    def __init__(self, template, args):
        self.template = template
        self.args = args

    def __repr__(self):
        return self.template.format(**self.args)


class Name:

    def __init__(self, name, value=None):
        if isinstance(name, Name):
            name = name.name
        assert name is None or isinstance(name, str), (type(name), name)
        self.name = name
        self.value = value if value is not None else object()

    def __bool__(self):
        return bool(self.name)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        return isinstance(other, type(self)) and (
            self.name == other.name or
            self.value is other.value or
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


class Assignment(ValueType):

    def __init__(self, name, value):
        self.safe_name = Name(name, value)
        self.value = value

    @property
    def name(self):
        return self.safe_name

    def finalize_recursive_refs(self, recursive):
        pass

    def repr_assignment(self, value):
        return "{} = {}".format(self.safe_name, pretty_format(value))

    def __repr__(self):
        return self.repr_assignment(self.value)


class Rule(ValueType):

    def __init__(self, name, value):
        self.value = Assignment(name, value)
        self.assignment = None

    @property
    def safe_name(self):
        return self.value.safe_name
    @safe_name.setter
    def safe_name(self, value):
        self.value.safe_name = value

    @property
    def name(self):
        return self.value.safe_name

    @property
    def range(self):
        return self.value.value
    @range.setter
    def range(self, value):
        self.value.value = value

    def setup_assignment(self):
        self.assignment = self.value

    def finalize_recursive_refs(self, recursive):
        pass

    def repr_rule_tuple(self, rule, sep=","):
        if len(rule) == 4:
            assert isinstance(rule[3], (str, SyntaxRef)), rule
            if not rule[3]:
                return repr(rule[:3]) + "{} #, {!r})".format(sep, rule[3])
        return repr(rule)

    def __bool__(self):
        rng = self.range
        return bool(
            not rng[0].startswith("_") or                   # text color
            len(self.range) > 3 or                          # sub rules
            (isinstance(rng[1], SyntaxRef) and rng[1]) or   # begin rules
            (                                               # end rules
                len(rng) > 2 and
                any(isinstance(end, SyntaxRef) and end for end in rng[2])
            )
        )

    def __repr__(self):
        if isinstance(self.range, Placeholder):
            raise Error(repr(self.range))
        if self.assignment is not None:
            return str(self.safe_name)
        return self.repr_rule_tuple(self.range)


class RecursiveRule(ValueType):

    def __init__(self, rule, recursive=False):
        assert isinstance(rule, (Rule, Placeholder)), rule
        self.value = rule
        self.recursive = recursive

    @property
    def safe_name(self):
        return self.value.safe_name

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.value == other.value
        return self.value == other

    def __bool__(self):
        return bool(self.value)

    def __repr__(self):
        if self.recursive:
            return "None, # {}".format(self.value)
        return repr(self.value)


class SyntaxClass:

    def __init__(self, name, rules=None, *, is_delim=False, ends_with_parent=False):
        self.name = Name(name, self)
        self.rules = rules or []
        self._safe_name = None
        self.contains_self = False
        self.parent_ends = []
        self.recursive_rules_refs = []
        self.is_root_namespace = name is None
        self.is_delim = is_delim
        self.ends_with_parent = ends_with_parent

    def add_rule(self, rule):
        self.rules.append(rule)

    def add_recursive_ref(self, item):
        self.rules.append(RecursiveRef(item))

    def add_recursive_rules_ref(self, syntax):
        assert isinstance(syntax, SyntaxClass), syntax
        self.recursive_rules_refs.append(RulesExtension(self, syntax))

    def finalize_recursive_refs(self, recursive):
        def iter_rules():
            for rule in self.rules:
                if isinstance(rule, RecursiveRef):
                    yield from recursive.iter_rules(rule.value, self)
                elif isinstance(rule, Comment):
                    yield rule
                else:
                    if not isinstance(rule, (Rule, Comment)):
                        import bug; bug.trace()
                    yield recursive.dedupe(rule)
        self.rules[:] = iter_rules()

    def ref(self, template, **args):
        args["expr"] = self
        if self.is_root_namespace:
            return Ref(template, args)
        return Ref("{expr.safe_name}." + template, args)

    @property
    def safe_name(self):
        return self._safe_name or self.name
    @safe_name.setter
    def safe_name(self, value):
        self._safe_name = value

    def __bool__(self):
        return bool(any(self.rules) or self.recursive_rules_refs or self.is_delim)

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
        lines.append("    default_text_color = DELIMITER")
        if self.ends_with_parent:
            lines.append("    ends_with_parent = True")
        rules = pretty_format(self.rules, 4).lstrip()
        lines.append("    rules = {}".format(rules))
        if self._safe_name:
            lines.append("{}.__name__ = {!r}".format(self.safe_name, self.name))
        return "\n".join(lines)

    def iter_recursive_refs(self):
        comments = 0
        for i, rule in enumerate(self.rules):
            if isinstance(rule, Comment):
                comments += 1
            elif isinstance(rule, RecursiveRule) and rule.recursive:
                yield self.ref("rules[{i}] = {ref}", i=i - comments, ref=rule.value)


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


DEFAULT_COLORS = {
    r"\\[\s\S]": "operator.escape",
    r"`[\s\S]": "operator.escape",
    #'""': "operator.escape",
}


TEMPLATE = """
# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: {hljs_file}
name = {name!r}
file_patterns = {file_patterns!r}
{definitions}

rules = {rules}{recursive_refs}
""".lstrip()

PYTHON_KEYWORDS = set("""
    and       del       from      not       while    
    as        elif      global    or        with     
    assert    else      if        pass      yield    
    break     except    import    class     in       
    raise     continue  finally   is        return   
    def       for       lambda    try       nonlocal
    RE        DELIMITER
    comment_token       default_text_color  delimited_ranges
    disabled  ends      file_patterns       name
    registry  whitespace          word_groups
    rules
    """.split())

if __name__ == "__main__":
    main()
