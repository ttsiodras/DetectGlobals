/* Buildsupport is (c) 2008-2016 European Space Agency
 * contact: maxime.perrotin@esa.int
 * License is LGPL, check LICENSE file */
/* 
 * build_c_glue.c
 * Generate vm_if.c/h and invoke_ri.c
 * (functions interfacing with the middleware)
 */


#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdbool.h>
#include <assert.h>
#include <sys/stat.h>

#include "my_types.h"
#include "practical_functions.h"
#include "c_ast_construction.h"

static FILE *g1 = NULL,
            *g2 = NULL,
            *g3 = NULL;

// libclang emits the following (node, token) data:
//
// CursorKind.VAR_DECL (g1) TokenKind.KEYWORD (static)
// CursorKind.VAR_DECL (g1) TokenKind.IDENTIFIER (FILE)
// CursorKind.VAR_DECL (g1) TokenKind.PUNCTUATION (*)
// CursorKind.VAR_DECL (g1) TokenKind.IDENTIFIER (g1)
// CursorKind.TYPE_REF (FILE) TokenKind.IDENTIFIER (FILE)
// CursorKind.VAR_DECL (g2) TokenKind.KEYWORD (static)
// CursorKind.VAR_DECL (g2) TokenKind.IDENTIFIER (FILE)
// CursorKind.VAR_DECL (g2) TokenKind.PUNCTUATION (*)
// CursorKind.VAR_DECL (g2) TokenKind.IDENTIFIER (g1)
// CursorKind.VAR_DECL (g2) TokenKind.PUNCTUATION (=)
// CursorKind.TYPE_REF (FILE) TokenKind.IDENTIFIER (FILE)
// CursorKind.VAR_DECL (g3) TokenKind.KEYWORD (static)
// CursorKind.VAR_DECL (g3) TokenKind.IDENTIFIER (FILE)
// CursorKind.VAR_DECL (g3) TokenKind.PUNCTUATION (*)
// CursorKind.VAR_DECL (g3) TokenKind.IDENTIFIER (g1)
// CursorKind.VAR_DECL (g3) TokenKind.PUNCTUATION (=)
// CursorKind.TYPE_REF (FILE) TokenKind.IDENTIFIER (FILE)
static int g_count = 0;

static bool g_brave_fpga = false;

/* Adds header to vm_if files */
void c_preamble(FV * param_fv)
{
    int l_hasparam = 0;
}
