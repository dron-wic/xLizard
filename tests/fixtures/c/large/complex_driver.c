/*
 * Landmark functions for comprehensive metric checks.
 * Analyze with: cognitive, nd, gotocount, returncount, pathcount, io
 *
 * Expected (approximate / exact where noted):
 *   landmark_plain     CCN=1 CogC=0 ND=0 PARAM=0 goto=0 return=1
 *   landmark_params6   PARAM=6
 *   landmark_nested4   ND>=4  CCN>=5  CogC>=8
 *   landmark_goto2     goto_count=2  return_count>=2
 *   landmark_returns3  return_count=3
 *   landmark_pathy     path_count high (many sequential if)
 *   landmark_hub       calls >= 8  (unique util_* / shared_api_*)
 *   landmark_fat       nloc >= 40  length >= 50  token_count >= 80
 */

#include <stdint.h>
#include <stddef.h>

#define REG_CTRL  ((volatile int *)0x40000000)
#define REG_STAT  ((volatile int *)0x40000004)
#define REG_DATA  ((volatile int *)0x40000008)
#define FLAG_RDY  0x01
#define FLAG_ERR  0x02
#define FLAG_OVR  0x04
#define MAX_RETRY 8

extern int util_a(int x);
extern int util_b(int x);
extern int util_c(int x);
extern int util_d(int x);
extern int util_e(int x);
extern int util_f(int x);
extern int util_g(int x);
extern int util_h(int x);
extern int util_i(int x);
extern int util_j(int x);
extern int util_k(int x);
extern int util_l(int x);
extern int shared_api_read(int *reg);
extern int shared_api_write(int *reg, int v);

/* ================================================================
 * landmark_plain
 * ================================================================ */
int landmark_plain(void)
{
    return 0;
}

/* ================================================================
 * landmark_params6 — PARAM = 6 (above default/HIS 5)
 * ================================================================ */
int landmark_params6(int a, int b, int c, int d, int e, int f)
{
    return a + b + c + d + e + f;
}

/* ================================================================
 * landmark_nested4 — deep nesting ND >= 4
 * ================================================================ */
int landmark_nested4(int a, int b, int c, int d, int e)
{
    if (a) {
        if (b) {
            if (c) {
                if (d) {
                    if (e) {
                        return 1;
                    }
                }
            }
        }
    }
    return 0;
}

/* ================================================================
 * landmark_goto2 — GOTO=2, multiple returns
 * ================================================================ */
int landmark_goto2(int mode, int *out)
{
    if (!out) {
        goto fail_null;
    }
    if (mode < 0) {
        goto fail_mode;
    }
    *out = mode;
    return 0;
fail_null:
    return -1;
fail_mode:
    return -2;
}

/* ================================================================
 * landmark_returns3 — RETURN = 3
 * ================================================================ */
int landmark_returns3(int x)
{
    if (x < 0) {
        return -1;
    }
    if (x == 0) {
        return 0;
    }
    return 1;
}

/* ================================================================
 * landmark_pathy — many sequential decisions → high PATH estimate
 * ================================================================ */
int landmark_pathy(int a, int b, int c, int d, int e, int f, int g, int h)
{
    int s = 0;
    if (a) { s += 1; }
    if (b) { s += 2; }
    if (c) { s += 4; }
    if (d) { s += 8; }
    if (e) { s += 16; }
    if (f) { s += 32; }
    if (g) { s += 64; }
    if (h) { s += 128; }
    switch (a & 3) {
    case 0: s ^= 1; break;
    case 1: s ^= 2; break;
    case 2: s ^= 4; break;
    default: s ^= 8; break;
    }
    return s;
}

/* ================================================================
 * landmark_hub — CALLS: unique project callees (utils + shared_api)
 * ================================================================ */
int landmark_hub(int x)
{
    int v;
    v = util_a(x);
    v = util_b(v);
    v = util_c(v);
    v = util_d(v);
    v = util_e(v);
    v = util_f(v);
    v = util_g(v);
    v = util_h(v);
    v += shared_api_read((int *)REG_STAT);
    shared_api_write((int *)REG_DATA, v);
    /* repeated call must not inflate unique CALLS */
    v = util_a(v);
    v = util_a(v);
    return v;
}

/* ================================================================
 * landmark_fat — large NLOC / tokens / length
 * ================================================================ */
int landmark_fat(volatile int *regs, int n, int mask)
{
    int i;
    int acc = 0;
    int tmp;
    int *p;

    if (!regs || n <= 0) {
        return -1;
    }
    p = (int *)regs;
    for (i = 0; i < n; i++) {
        tmp = p[i];
        if ((tmp & mask) == 0) {
            continue;
        }
        if (tmp & FLAG_ERR) {
            acc -= 1;
        } else if (tmp & FLAG_OVR) {
            acc -= 2;
        } else if (tmp & FLAG_RDY) {
            acc += (tmp & 0xff);
        } else {
            acc += tmp >> 8;
        }
        if (i > 0 && (p[i - 1] & FLAG_RDY) && (tmp & FLAG_RDY)) {
            acc += 3;
        }
        while (tmp & FLAG_OVR) {
            tmp &= ~FLAG_OVR;
            acc++;
            if (acc > 1000) {
                break;
            }
        }
    }
    for (i = 0; i < MAX_RETRY; i++) {
        if (shared_api_read((int *)REG_CTRL) & FLAG_RDY) {
            break;
        }
        acc++;
    }
    if (acc < 0) {
        return -2;
    }
    if (acc == 0) {
        return 0;
    }
    return acc;
}

/* Callers of shared_api_* to raise CALLING on those helpers */
int caller_alpha(int *r)
{
    return shared_api_read(r) + util_a(1);
}

int caller_beta(int *r, int v)
{
    return shared_api_write(r, v) + util_b(2);
}

int caller_gamma(int *r)
{
    int x = shared_api_read(r);
    return shared_api_write(r, x) + util_c(3);
}

int caller_delta(int *r)
{
    return shared_api_read(r) + util_d(4);
}

int caller_epsilon(int *r, int v)
{
    shared_api_write(r, v);
    return shared_api_read(r) + util_e(5);
}

/* Mixed logic / pointers for file-level SourceMonitor heuristics */
int peripheral_poll(void)
{
    volatile int *ctrl = REG_CTRL;
    volatile int *stat = REG_STAT;
    int *shadow;
    int tries = 0;
    int code = 0;

    shadow = (int *)stat;
    if (!ctrl || !stat) {
        return -1;
    }
    while (tries < MAX_RETRY) {
        if ((*stat & FLAG_RDY) && !(*stat & FLAG_ERR)) {
            code = *REG_DATA;
            break;
        } else if (*stat & FLAG_ERR) {
            *ctrl |= FLAG_ERR;
            code = -2;
            break;
        }
        tries++;
    }
    if (tries >= MAX_RETRY || (code < 0 && (*shadow & FLAG_OVR))) {
        return -3;
    }
    return code;
}
