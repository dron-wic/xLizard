/*
 * Shared helpers for CALLS / CALLING and modularity stress.
 * Each util_* is a trivial leaf (CCN=1, CogC=0, ND=0).
 */

int util_a(int x) { return x + 1; }
int util_b(int x) { return x + 2; }
int util_c(int x) { return x + 3; }
int util_d(int x) { return x + 4; }
int util_e(int x) { return x + 5; }
int util_f(int x) { return x + 6; }
int util_g(int x) { return x + 7; }
int util_h(int x) { return x + 8; }
int util_i(int x) { return x + 9; }
int util_j(int x) { return x + 10; }
int util_k(int x) { return x + 11; }
int util_l(int x) { return x + 12; }

/* Fan-in targets: many callers in complex_driver.c / callers.c */
int shared_api_read(int *reg)
{
    return *reg;
}

int shared_api_write(int *reg, int v)
{
    *reg = v;
    return v;
}
