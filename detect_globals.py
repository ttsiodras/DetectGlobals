#!/usr/bin/env python3
"""
A utility that parses pre-processed (standalone) C files using Clang,
and then detects and reports all functions inside an ELF that are
not used anywhere.
"""

import os
import sys
from collections import namedtuple

# For mypy static type checks.
from typing import List, Tuple, Any  # NOQA

from clang.cindex import (
    CursorKind, TokenKind, Index, TranslationUnit, TranslationUnitLoadError)

from multicore_loop import MultiCoreLoop

LineRange = namedtuple('LineRange', ['a_min', 'b_max'])


# For SPARC targets, this is the toolchain prefix
G_PLATFORM_PREFIX = "sparc-rtems-"

# Debug mode
G_DEBUG = True


def process_unit(t_unit: Any, processor):
    # To detect globals, track if we are inside or outside function bodies
    brace_level = 0

    f_log = open("log.txt", "w")
    interim: List[str] = []
    last_column = 0
    function_line_ranges: List[LineRange] = []
    is_static = False

    def emit_interim(is_static, token):
        if not is_static:
            inside_function = True
            for rnge in function_line_ranges:
                if rnge.a_min <= token.location.line <= rnge.b_max:
                    break
            else:
                inside_function = False
        if is_static or not inside_function:
            processor(interim[:])
        while interim:
            interim.pop()

    def add_function_border(lineno, data_pair=[]):  # pylint: disable=W0102
        if not data_pair:
            data_pair.append(lineno)
            return
        function_line_ranges.append(
            LineRange(data_pair[0], lineno))
        data_pair.pop()

    for cur in t_unit.cursor.get_children():
        if cur.kind == CursorKind.TRANSLATION_UNIT or     \
                cur.location.file is None or              \
                cur.location.file.name != t_unit.spelling:
            # print("Skipping over", node.spelling)
            continue
        if hasattr(cur, "CursorKind") and cur.CursorKind == CursorKind.FUNCTION_DECL:
            for cur_sub in cur.get_children():
                if cur.kind == CursorKind.VAR_DECL and cur.spelling != "":
                    print("Function defines:", cur.spelling)
        elif cur.kind == CursorKind.VAR_DECL and cur.spelling != "":
            print("Global defined:", cur.spelling, cur.type.spelling)


def parse_ast(t_units: List[Any]) -> List[Any]:
    """
    Traverse the AST, gathering all globals/statics
    """
    results = []
    if G_DEBUG:
        def print_and_add(x):
            print(x)
            results.append(x)
        for idx, t_unit in enumerate(t_units):
            process_unit(t_unit, print_and_add)
    else:
        multicore_loop = MultiCoreLoop(results.append)
        for idx, t_unit in enumerate(t_units):
            print("[-] %3d%% Navigating AST and collecting symbols... " % (
                100*(1+idx)/len(t_units)))
            multicore_loop.spawn(
                target=process_unit,
                args=(t_unit, multicore_loop.res_queue.put))
        multicore_loop.join()
    return results


def parse_files(list_of_files: List[str]) -> Tuple[Any, List[Any]]:
    """
    Use Clang to parse the provided list of files.
    """
    idx = Index.create()
    t_units = []  # type: List[Any]

    # To avoid parsing the files all the time, store the parsed ASTs
    # of each compilation unit in a cache.
    if not os.path.exists(".cache"):
        os.mkdir(".cache")
    for i, filename in enumerate(list_of_files):
        cache_filename = '.cache/' + os.path.basename(filename) + "_cache"
        # Have I parsed this file before?
        if os.path.exists(cache_filename):
            # Yes, load from cache
            try:
                t_units.append(
                    TranslationUnit.from_ast_file(
                        cache_filename, idx))
                print("[-] Loading cached AST for", filename)
            except TranslationUnitLoadError:
                print("[-] %3d%% Parsing " % (
                    100*(i+1)/len(list_of_files)) + filename)
                t_units.append(idx.parse(filename))
                t_units[-1].save(cache_filename)
        else:
            # No, parse it now.
            print("[-] %3d%% Parsing " % (
                100*(i+1)/len(list_of_files)) + filename)
            # ...to adapt to: .... filename, args=['-I ...', '-D ...']
            t_units.append(idx.parse(filename))
            t_units[-1].save(cache_filename)
    return idx, t_units


def get_globals_of(files: List[str]):
    _, t_units = parse_files(files)
    return parse_ast(t_units)


def main() -> None:
    """
    Parse all passed-in C files (preprocessed with -E, to be standalone).
    Then scout for globals/statics.
    """
    if len(sys.argv) <= 1:
        print("Usage:", sys.argv[0], "preprocessed_source_files")
        sys.exit(1)

    _, t_units = parse_files(sys.argv[1:])
    # To debug what happens with a specific compilation unit, use this:
    #
    # le_units = [x for x in t_units if x.spelling.endswith('svc191vnir.c')]
    # import ipdb ; ipdb.set_trace()
    parse_ast(t_units)
    print("[-] Done.")


if __name__ == "__main__":
    main()
