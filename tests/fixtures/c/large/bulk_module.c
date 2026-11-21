/*
 * Bulk stress module: many medium-complexity functions.
 * Used to exercise scale (function_count, tokens, HTML size).
 */

#include <stdint.h>

#define BULK_MAX 64
#define BULK_MASK 0xFF
#define BULK_FLAG(x) ((x) & BULK_MASK)

static int *g_bulk_ptr;
static volatile int g_bulk_regs[8];


int bulk_fn_00(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_01(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_02(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_03(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_04(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_05(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_06(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_07(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_08(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_09(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_10(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_11(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_12(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_13(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_14(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_15(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_16(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_17(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_18(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_19(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_20(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_21(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_22(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_23(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_24(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_25(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_26(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_27(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_28(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_29(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_30(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_31(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_32(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_33(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_34(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_35(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_36(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_37(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_38(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_39(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_40(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_41(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_42(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_43(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_44(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_45(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_46(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_47(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_48(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_49(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_50(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_51(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_52(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_53(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_54(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_55(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_56(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_57(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_58(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_fn_59(int a, int b, int c)
{
    int s = 0;
    int k;
    if (a > 0) {
        s += a;
    }
    if (b && c) {
        s += b * c;
    } else if (b || c) {
        s += b + c;
    }
    for (k = 0; k < a && k < 8; k++) {
        if (k > b) {
            s += k;
        }
    }
    switch (c & 3) {
    case 0:
        return s;
    case 1:
        return s + 1;
    case 2:
        return s + 2;
    default:
        return s - 1;
    }
}


int bulk_entry(int *buf, int n)
{
    int i, sum = 0;
    if (!buf || n <= 0) {
        return -1;
    }
    g_bulk_ptr = buf;
    for (i = 0; i < n && i < BULK_MAX; i++) {
        if (BULK_FLAG(buf[i])) {
            sum += buf[i];
        }
        if (i < 8) {
            g_bulk_regs[i] = buf[i];
        }
    }
    return sum;
}

