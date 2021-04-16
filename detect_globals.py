#!/usr/bin/env python3
"""
A utility that parses C source using Clang, and then
detects and reports all variables with global
storage - i.e. all globals and function-statics.
"""

import os
import sys
import logging

# For mypy static type checks.
from typing import List, Tuple, Any  # NOQA

from clang.cindex import (
    CursorKind, StorageClass, Index, TranslationUnit,
    TranslationUnitLoadError)


def process_unit(t_unit: Any, processor):
    for cur in t_unit.cursor.get_children():
        if cur.kind == CursorKind.TRANSLATION_UNIT or     \
                cur.location.file is None or              \
                cur.location.file.name != t_unit.spelling:
            # print("Skipping over", node.spelling)
            continue
        if cur.kind == CursorKind.FUNCTION_DECL:
            # Must somehow report static variables...
            for cur_sub in cur.walk_preorder():
                if cur_sub.kind == CursorKind.VAR_DECL and \
                        cur_sub.spelling != "":
                    if cur_sub.storage_class == StorageClass.STATIC and \
                            not cur_sub.type.spelling.startswith('const'):
                        processor([
                            'static',
                            cur_sub.spelling,
                            cur_sub.type.spelling,
                            t_unit.spelling,
                            cur_sub.location.line])
        elif cur.kind == CursorKind.VAR_DECL and cur.spelling != "":
            processor([
                'global', cur.spelling, cur.type.spelling,
                t_unit.spelling, cur.location.line])


def parse_ast(t_units: List[Any]) -> List[Any]:
    """
    Traverse the AST, gathering all globals/statics
    """
    results = []

    def print_and_add(x):
        results.append(x)
    for t_unit in t_units:
        process_unit(t_unit, print_and_add)
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
                logging.info("[-] Loading cached AST for %s", filename)
            except TranslationUnitLoadError:  # pragma: nocover
                logging.info("[-] %3d%% Parsing %s", (
                    100*(i+1)/len(list_of_files)), filename)  # pragma: nocover
                t_units.append(idx.parse(filename))  # pragma: nocover
                t_units[-1].save(cache_filename)  # pragma: nocover
        else:
            # No, parse it now.
            logging.info("[-] %3d%% Parsing %s", (
                100*(i+1)/len(list_of_files)), filename)
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
        print("Usage:", sys.argv[0], "[-h] [-v] <source_file1> ...")
        sys.exit(1)

    if "-h" in sys.argv:
        print("Usage:", sys.argv[0], "[-h] [-v] <source_file1> ...")
        print("Options are:")
        print("    -h for help")
        print("    -v for increased verbosity")
        sys.exit(1)
    if "-v" in sys.argv:
        del sys.argv[sys.argv.index("-v")]
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
    logging.info("[-] Parsing input files...")
    _, t_units = parse_files(sys.argv[1:])
    # To debug what happens with a specific compilation unit, use this:
    #
    # le_units = [x for x in t_units if x.spelling.endswith('svc191vnir.c')]
    # import ipdb ; ipdb.set_trace()
    for result in parse_ast(t_units):
        print("[-] Detected variable:", str(result))
    logging.info("[-] Done.")


if __name__ == "__main__":
    main()
