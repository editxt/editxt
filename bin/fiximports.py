#! /usr/bin/env python
import argparse
import os
import re
from fnmatch import fnmatch
from os.path import isdir, isfile, join

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--dry_run", action="store_true")
    parser.add_argument("-x", "--exclude", default="",
        help="comma-delimited list of file or directory patterns to exclude")
    parser.add_argument("-i", "--include", default="",
        help="comma-delimited list of file patterns to include")
    #parser.add_argument("find_regex")
    #parser.add_argument("replace_expression")
    parser.add_argument("path", nargs="+",
        help="One or more file or directory paths")

    args = parser.parse_args()
    excludes = [p for p in args.exclude.split(",") if p.strip()]
    includes = [p for p in args.include.split(",") if p.strip()]
    #regex = re.compile(args.find_regex)
    for path in args.path:
        replace_in_path(path, includes, excludes, args.dry_run)


def replace_in_path(path, includes, excludes, dry_run):
    def ismatch(name, patterns):
        return any(fnmatch(name, p) for p in patterns)
    if isdir(path):
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                if ismatch(filename, excludes) \
                        or not ismatch(filename, includes):
                    continue
                filepath = join(dirpath, filename)
                if ismatch(filepath, excludes):
                    continue
                replace(filepath, dry_run)
            for name in list(dirnames):
                if ismatch(name, excludes):
                    dirnames.remove(name)
                if ismatch(join(dirpath, name), excludes):
                    dirnames.remove(name)
    elif isfile(path):
        replace(path, dry_run)
    else:
        print("skipped: " + path)


import Foundation
fn_names = list(Foundation.__all__)
import AppKit
ak_names = list(AppKit.__all__)

IMPORT_STAR = re.compile(r"^from (AppKit|Foundation) import \* *(\r?\n)", re.MULTILINE)
TRANS = {"AppKit": "ak", "Foundation": "fn"}
fn_set = set(n for n in fn_names if any(c.isupper() for c in n))
ak_set = set(n for n in ak_names if any(c.isupper() for c in n))
for name in ["Foundation", "AppKit"]:
    ak_set.discard(name)
    fn_set.discard(name)
common = set(n for n in fn_set
    if getattr(AppKit, n) is not getattr(Foundation, n))
assert not common, common
ak_expr = re.compile(r"""([^."'\w])(""" + r"|".join(ak_set - fn_set) + "\W)")
fn_expr = re.compile(r"""([^."'\w])(""" + r"|".join(fn_set) + "\W)")


def replace(filepath, dry_run=False):
    with open(filepath) as fileobj:
        data = fileobj.read()
    def fix_import(match):
        name = match.group(1)
        return "import {} as {}{}".format(name, TRANS[name], match.group(2))
    original_data = data
    data, num = do_replace(IMPORT_STAR, fix_import, data)
    if num:
        data, m = do_replace(ak_expr, (lambda m: m.expand(r"\1ak.\2")), data)
        data, n = do_replace(fn_expr, (lambda m: m.expand(r"\1fn.\2")), data)
        if not (m + n):
            data, x = do_replace(IMPORT_STAR, (lambda m: ""), original_data)
            assert x == num, (filepath, x)
        print("{} : {}".format(filepath, num + m + n))
        if not dry_run:
            with open(filepath, "w") as fileobj:
                fileobj.write(data)


def do_replace(regex, replace_func, data):
    pieces = []
    num = 0
    end = 0
    for match in regex.finditer(data):
        if is_comment_line(data, match.start()):
            continue
        num += 1
        if match.start() > end:
            pieces.append(data[end:match.start()])
        pieces.append(replace_func(match))
        end = match.end()
    if num:
        if end < len(data):
            pieces.append(data[end:])
        data = "".join(pieces)
    return data, num


def is_comment_line(data, pos):
    for i in range(pos, -1, -1):
        if data[i] in "\n\r":
            i += 1
            break
    return data[i:pos].lstrip().startswith("#")


if __name__ == "__main__":
    main()
