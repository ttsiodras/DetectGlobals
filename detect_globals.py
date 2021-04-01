#!/home/taste/GitLocal/DeadCodeDetector/.venv/bin/python3
"""
A utility that parses pre-processed (standalone) C files using Clang,
and then detects and reports all functions inside an ELF that are
not used anywhere.
"""

import os
import sys
import multiprocessing

# For mypy static type checks.
from typing import List, Tuple, Any  # NOQA

from clang.cindex import (
    CursorKind, TokenKind, Index, TranslationUnit, TranslationUnitLoadError)


# For SPARC targets, this is the toolchain prefix
G_PLATFORM_PREFIX = "sparc-rtems-"

# To detect globals, track if we are inside or outside function bodies
G_BRACE_LEVEL = 0

# Debug level
G_DEBUG = 1


def parse_ast(t_units: List[Any]) -> None:
    """
    Traverse the AST, gathering all mentions of our functions.
    """

    def process_unit(t_unit: Any):
        global G_BRACE_LEVEL
        f_log = open("log.txt", "w")
        result = []  # type: List[str]
        interim = []
        last_column = 0

        def emit_interim(is_static):
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
                result.append(interim[:])
                print(interim)
            while interim:
                interim.pop()

        function_line_ranges = []
        is_static = False

        # Gather all the references to functions in this C file
        for node in t_unit.cursor.walk_preorder():
            # To find the unused functions, we need to collect all 'mentions'
            # of functions anywhere. This is generally speaking, hard...
            # But... (see below)
            if node.kind == CursorKind.TRANSLATION_UNIT:
                continue
            if node.location.file.name != t_unit.spelling:
                continue

            for token in node.get_tokens():
                f_log.write('%s %s %s\n' % (
                    node.kind, token.kind, token.spelling))
                if node.kind == CursorKind.FUNCTION_DECL:
                    if token.kind == TokenKind.PUNCTUATION:
                        if token.spelling == "{":
                            G_BRACE_LEVEL += 1
                            function_line_ranges.append(token.location.line)
                        elif token.spelling == "}":
                            G_BRACE_LEVEL -= 1
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
                        #     import pdb ; pdb.set_trace()
                        if token.location.column < last_column:
                            if interim:
                                emit_interim(is_static)
                                is_static = False
                        interim.append(token.spelling)
                        last_column = token.location.column
                else:
                    if interim:
                        emit_interim(is_static)
                        is_static = False
        # res_queue.put(result)

    res_queue = multiprocessing.Queue()  # type: Any
    list_of_processes = []  # type: List[Any]
    running_instances = 0

    for idx, t_unit in enumerate(t_units):
        process_unit(t_unit)
    #    print("[-] %3d%% Navigating AST and collecting symbols... " % (
    #        100*(1+idx)/len(t_units)))
    #    # if running_instances >= multiprocessing.cpu_count():
    #    if running_instances >= 1:
    #        for definition in res_queue.get():
    #            print(definition)
    #        all_are_still_alive = True
    #        while all_are_still_alive:
    #            for idx_proc, proc in enumerate(list_of_processes):
    #                child_alive = proc.is_alive()
    #                all_are_still_alive = all_are_still_alive and child_alive
    #                if not child_alive:
    #                    del list_of_processes[idx_proc]
    #                    break
    #            else:
    #                time.sleep(1)
    #        running_instances -= 1
    #    proc = multiprocessing.Process(
    #        target=process_unit, args=(t_unit,))
    #    list_of_processes.append(proc)
    #    proc.start()
    #    running_instances += 1
    #for proc in list_of_processes:
    #    proc.join()
    #    if proc.exitcode != 0:
    #        print("[x] Failure in one of the child processes...")
    #        sys.exit(1)
    #    for definition in res_queue.get():
    #        print(definition)


def parse_files(list_of_files: List[str]) -> Tuple[Any, List[Any]]:
    """
    Use Clang to parse the provided list of files, and return
    a tuple of the Clang index, and the list of compiled ASTs
    one for each compilation unit)
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


def main() -> None:
    """
    Parse all passed-in C files (preprocessed with -E, to be standalone).
    Then scout for mentions of functions at any place, to collect the
    *actually* used functions.

    Finally, report the unused ones.

    The first command line argument expected is the ELF (so we can gather
    the entire list of functions in the object code). The remaining ones
    are the preprocessed C source files.
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
