Maxime's work on creating a model checker depends on knowledge of variables in
global storage. This little utility attempts to use libclang and a bunch of
heuristics to provide that information. 

# Setup - usage

Begin by setting up the virtual environment and activating it:

    $ make dev-install
    $ . .venv/bin/activate

You can now modify your project's Makefiles/build system files to spawn your
cross-compiler with `-E` instead of `-c`. This will give you a set of `*.o`
files that aren't really object files - they are instead preprocessed,
standalone source code.

Collect them, and rename them appropriately:

    $ mkdir /path/to/preprocessed
    $ find /path/to/src -type f -iname '*.o' \
        -exec mv -i '{}' /path/to/preprocessed/ \;
    $ cd /path/to/preprocessed
    $ rename -E 's,o$,c,' *.o
    $ cd -

You can now "feed" these standalone preprocessed sources to this
script, with an invocation like this:

    $ ./detect_globals.py /path/to/preprocessed/*.c

The script will then report the globals it finds (including
function-level statics).
