/*
 * xLizard metric fixtures — expected values documented per function.
 * Analyze with: -Ecognitive -End  (and -Emccabe / -m where noted)
 */

/* ================================================================
 * plain_fn
 *   CCN  = 1
 *   CogC = 0
 *   ND   = 0
 *   PARAM = 0
 * ================================================================ */
int plain_fn(void)
{
    return 0;
}

/* ================================================================
 * one_param
 *   PARAM = 1
 *   CCN   = 1
 * ================================================================ */
int one_param(int x)
{
    return x;
}

/* ================================================================
 * three_params
 *   PARAM = 3
 * ================================================================ */
int three_params(int a, int b, int c)
{
    return a + b + c;
}

/* ================================================================
 * if_simple
 *   CCN  = 2   (base + if)
 *   CogC = 1   (+1 if)
 *   ND   = 1
 * ================================================================ */
int if_simple(int a)
{
    if (a) {
        return 1;
    }
    return 0;
}

/* ================================================================
 * if_and
 *   CCN  = 3   (base + if + &&)
 *   CogC = 2   (+1 if, +1 && sequence)
 *   ND   = 1   (&& does not add nesting)
 * ================================================================ */
int if_and(int a, int b)
{
    if (a && b) {
        return 1;
    }
    return 0;
}

/* ================================================================
 * if_and_or
 *   CCN  = 4   (base + if + && + ||)
 *   CogC = 3   (+1 if, +1 && seq, +1 || seq)
 * ================================================================ */
int if_and_or(int a, int b, int c)
{
    if (a && b || c) {
        return 1;
    }
    return 0;
}

/* ================================================================
 * nested_if
 *   CCN  = 3   (base + if + if)
 *   CogC = 3   (+1 outer, +2 inner at nesting 1)
 *   ND   = 2
 * ================================================================ */
int nested_if(int a, int b)
{
    if (a) {
        if (b) {
            return 1;
        }
    }
    return 0;
}

/* ================================================================
 * if_else
 *   CCN  = 2   (else does not add CCN)
 *   CogC = 2   (+1 if, +1 else hybrid)
 *   ND   = 1
 * ================================================================ */
int if_else(int a)
{
    if (a) {
        return 1;
    } else {
        return 0;
    }
}

/* ================================================================
 * ternary_op
 *   CCN  = 2   (base + ?)
 *   CogC = 1   (+1 ternary)
 * ================================================================ */
int ternary_op(int a)
{
    return a ? 1 : 0;
}

/* ================================================================
 * for_loop
 *   CCN  = 2
 *   CogC = 1
 *   ND   = 1
 * ================================================================ */
int for_loop(int n)
{
    int i, s = 0;
    for (i = 0; i < n; i++) {
        s += i;
    }
    return s;
}

/* ================================================================
 * while_loop
 *   CCN  = 2
 *   CogC = 1
 * ================================================================ */
int while_loop(int n)
{
    int s = 0;
    while (n > 0) {
        s += n;
        n--;
    }
    return s;
}

/* ================================================================
 * do_while
 *   CCN  = 2   (while token)
 *   CogC = 1   (do structural; trailing while not double-counted)
 * ================================================================ */
int do_while(int n)
{
    int s = 0;
    do {
        s += n;
        n--;
    } while (n > 0);
    return s;
}

/* ================================================================
 * switch_two_cases
 *   CCN  = 3   (base + case + case; switch itself not counted)
 *   CogC = 1   (whole switch once)
 *   with -m (modified): CCN = 2  (cases cancel; switch +1 → base+1)
 * ================================================================ */
int switch_two_cases(int x)
{
    switch (x) {
    case 1:
        return 1;
    case 2:
        return 2;
    default:
        return 0;
    }
}

/* ================================================================
 * switch_fallthrough
 *   CCN default = 3  (base + case + case)
 *   CCN -Emccabe = 2 (fall-through second case subtracted)
 *   CogC = 1
 * ================================================================ */
int switch_fallthrough(int x)
{
    switch (x) {
    case 1:
    case 2:
        return 1;
    default:
        return 0;
    }
}

/* ================================================================
 * goto_label
 *   CCN  = 2   (base + if; goto not in default CCN)
 *   CogC = 2   (+1 if, +1 goto fundamental)
 * ================================================================ */
int goto_label(int a)
{
    if (a) {
        goto done;
    }
    return 0;
done:
    return 1;
}

/* ================================================================
 * nested_for_if  (CogC classic-ish)
 *   CCN  = 3
 *   CogC = 4   (+1 for, +2 if nesting1, +1 &&)
 *   ND   = 2
 * ================================================================ */
int nested_for_if(int n, int k)
{
    int i, c = 0;
    for (i = 0; i < n; i++) {
        if (i && k) {
            c++;
        }
    }
    return c;
}

/* ================================================================
 * recursion_self
 *   CogC >= 1 for direct recursion (+ optional if)
 * ================================================================ */
int recursion_self(int n)
{
    if (n <= 0) {
        return 0;
    }
    return n + recursion_self(n - 1);
}
