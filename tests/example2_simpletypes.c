#include <stdio.h>

int i;
float f;
double d;

// libclang emits the following (node, token) data:
//
// CursorKind.VAR_DECL (i) TokenKind.KEYWORD (int)
// CursorKind.VAR_DECL (i) TokenKind.IDENTIFIER (i)
// CursorKind.VAR_DECL (f) TokenKind.KEYWORD (float)
// CursorKind.VAR_DECL (f) TokenKind.IDENTIFIER (f)
// CursorKind.VAR_DECL (d) TokenKind.KEYWORD (double)
// CursorKind.VAR_DECL (d) TokenKind.IDENTIFIER (d)

int main()
{
    int l_i;
    float l_f;
    double l_d;
}
