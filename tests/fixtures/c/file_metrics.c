/*
 * File-level (SourceMonitor-style) fixture.
 * Expected approximate properties after FileAnalyzer.analyze():
 *   - comment_percentage > 0
 *   - preprocessor_directives >= 2  (#include + #define)
 *   - pointer_operations >= 1
 *   - conditional_statements >= 2  (braceless if + braced if/else)
 *   - logical_operators >= 1  (&&)
 *   - max_block_depth >= 1
 */

#include <stdio.h>

#define MAX_N 10

static int *g_ptr;

int file_sample(int a, int b)
{
    int *p = &a;          /* pointer decl + address-of */
    /* braceless if must still count as conditional */
    if (a)
        b = 1;
    if (a && b) {
        *p = a;           /* deref */
        g_ptr = p;        /* may use -> elsewhere */
    } else {
        b = 0;
    }
    while (b > 0) {
        b--;
    }
    return *p;
}
