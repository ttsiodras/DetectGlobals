[![Build and Test Status of DetectGlobals on Circle CI](https://circleci.com/gh/ttsiodras/DetectGlobals.svg?&style=shield)](https://circleci.com/gh/ttsiodras/DetectGlobals/tree/master)

Maxime's work on creating a model checker depends on knowledge of variables in
global storage. This little utility uses libclang to provide that information. 

If you run...

    $ make
    ...
    ===== 7 passed in 0.14s ====

...you will then execute the static analysis tests on this utility's Python source;
and you will also run actual C source code processing tests.

To verify the coverage achieved, issue this:

    $ make coverage
    ...
    Coverage achieved: 100%

You can "feed" C source code to this script, with an invocation like this:

    $ ./detect_globals.py /path/to/*.c

The script will then report the globals it finds (including function-level `static`s).
For usage information in library form, see the test code (in `test_detector.py`).
