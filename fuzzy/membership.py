"""Fungsi keanggotaan segitiga dan trapesium (implementasi NumPy)."""
import numpy as np


def trapesium(x, a, b, c, d):
    """
    μ trapesium:
        0                 , x <= a atau x >= d
        (x - a) / (b - a) , a < x < b
        1                 , b <= x <= c
        (d - x) / (d - c) , c < x < d
    Bila a == b (bahu kiri) sisi naik dihilangkan; bila c == d (bahu kanan)
    sisi turun dihilangkan, sehingga μ = 1 sampai tepi semesta.
    """
    x = np.asarray(x, dtype=float)
    mu = np.zeros_like(x)
    # daerah datar
    mu[(x >= b) & (x <= c)] = 1.0
    # sisi naik
    if b > a:
        m = (x > a) & (x < b)
        mu[m] = (x[m] - a) / (b - a)
    # sisi turun
    if d > c:
        m = (x > c) & (x < d)
        mu[m] = (d - x[m]) / (d - c)
    return mu


def segitiga(x, a, b, c):
    """
    μ segitiga:
        0                 , x <= a atau x >= c
        (x - a) / (b - a) , a < x <= b
        (c - x) / (c - b) , b < x < c
    Segitiga adalah trapesium dengan b == c.
    """
    return trapesium(x, a, b, b, c)


def hitung_mf(x, spec):
    """Hitung μ(x) dari spesifikasi config, mis. ("tri", [a, b, c])."""
    bentuk, p = spec
    if bentuk == "tri":
        return segitiga(x, *p)
    if bentuk == "trap":
        return trapesium(x, *p)
    raise ValueError(f"Bentuk MF tidak dikenal: {bentuk}")


def mu_skalar(x, spec):
    """Versi skalar dari hitung_mf (mengembalikan float)."""
    return float(hitung_mf(np.array([x]), spec)[0])


def _f(v):
    return f"{v:g}"


def rumus_substitusi(x, spec):
    """Teks substitusi rumus μ(x), mis. '(3.5 − 3.3) / (3.5 − 3) = 0.4000'."""
    bentuk, p = spec
    a, b, c, d = (p[0], p[1], p[1], p[2]) if bentuk == "tri" else p
    m = mu_skalar(x, spec)
    if b <= x <= c:
        return f"{_f(b)} ≤ x ≤ {_f(c)} → μ = 1"
    if b > a and a < x < b:
        return f"(x − a)/(b − a) = ({_f(x)} − {_f(a)}) / ({_f(b)} − {_f(a)}) = {m:.4f}"
    if d > c and c < x < d:
        return f"(d − x)/(d − c) = ({_f(d)} − {_f(x)}) / ({_f(d)} − {_f(c)}) = {m:.4f}"
    return f"x ≤ {_f(a)} atau x ≥ {_f(d)} → μ = 0"
