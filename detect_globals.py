#!/usr/bin/env python3
"""
A utility that parses pre-processed (standalone) C files using Clang,
and then detects and reports all functions inside an ELF that are
not used anywhere.
"""

import os
import sys

# For mypy static type checks.
from typing import List, Tuple, Any  # NOQA

from clang.cindex import (
    CursorKind, TokenKind, Index, TranslationUnit, TranslationUnitLoadError)

from multicore_loop import MultiCoreLoop


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
    function_line_ranges: List[int] = []
    is_static = False

    def emit_interim(is_static, token):
        if not is_static:
            check_range_iter = iter(function_line_ranges)
            inside_function = False
            while not inside_function:
                try:
                    a_min = next(check_range_iter)
                    b_max = next(check_range_iter)
                    inside_function = a_min < token.location.line < b_max
                except StopIteration:
                    break
        if is_static or not inside_function:
            processor(interim[:])
        while interim:
            interim.pop()

    for node in t_unit.cursor.walk_preorder():
        if node.kind == CursorKind.TRANSLATION_UNIT or     \
                node.location.file is None or              \
                node.location.file.name != t_unit.spelling:
            continue

        for token in node.get_tokens():
            f_log.write('%s %s %s\n' % (
                node.kind, token.kind, token.spelling))
            if node.kind == CursorKind.FUNCTION_DECL and \
                    token.kind == TokenKind.PUNCTUATION:
                if token.spelling == "{":
                    brace_level += 1
                    if brace_level == 1:
                        function_line_ranges.append(token.location.line)
                elif token.spelling == "}":
                    brace_level -= 1
                    if brace_level == 0:
                        function_line_ranges.append(token.location.line)
            elif node.kind == CursorKind.VAR_DECL:
                if token.kind in [
                        TokenKind.KEYWORD, TokenKind.IDENTIFIER,
                        TokenKind.PUNCTUATION]:
                    if token.spelling in ['const', 'volatile']:
                        continue
                    if token.spelling in ['extern', '=']:
                        break
                    if token.spelling == 'static':
                        is_static = True
                        continue
                    # if token.spelling == 'in':
                    #     import pdb ; pdb.set_trace()
                    if token.location.column < last_column and \
                            interim:
                        emit_interim(is_static, token)
                        is_static = False
                    interim.append(token.spelling)
                    last_column = token.location.column
            else:
                if interim:
                    emit_interim(is_static, token)
                    is_static = False


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
