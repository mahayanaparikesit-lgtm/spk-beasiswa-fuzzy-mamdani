"""
Mesin inferensi Fuzzy Mamdani.

Tahapan:
  1. Fuzzifikasi   : μ setiap kategori untuk setiap input
  2. α-predikat    : AND = MIN atas anteseden setiap aturan
  3. Implikasi     : MIN (clipping) -> μ_konsekuen(z) dipotong setinggi α
  4. Agregasi      : MAX atas semua fungsi output terpotong
  5. Defuzzifikasi : centroid diskrit  z* = Σ μ(z_i)·z_i / Σ μ(z_i)
"""
import numpy as np

import config
from fuzzy.membership import hitung_mf, mu_skalar


def grid_output(step=None):
    """Grid diskrit semesta output, mis. 0, 0.1, ..., 100."""
    step = config.OUTPUT_STEP if step is None else step
    lo, hi = config.OUTPUT["semesta"]
    n = int(round((hi - lo) / step)) + 1
    return np.linspace(lo, hi, n)


def kategori_skor(skor):
    """Ubah skor crisp menjadi kategori kelayakan (lihat config.KATEGORI_SKOR)."""
    for lo, hi, nama in config.KATEGORI_SKOR:
        if lo <= skor < hi:
            return nama
    return config.KATEGORI_SKOR[-1][2]


def fuzzifikasi(nilai):
    """
    nilai: dict {var: angka}. Nilai di luar semesta dipotong ke batas semesta.
    Return: {var: {kategori: μ}}
    """
    hasil = {}
    for var in config.INPUT_KEYS:
        lo, hi = config.INPUTS[var]["semesta"]
        x = min(max(float(nilai[var]), lo), hi)
        hasil[var] = {kat: mu_skalar(x, spec) for kat, spec in config.INPUTS[var]["mf"].items()}
    return hasil


def alpha_predikat(mu, rules=None):
    """
    α setiap aturan = MIN dari μ anteseden.
    Return: list dict {id, if, then, alasan, komponen, alpha}
    """
    rules = config.RULES if rules is None else rules
    out = []
    for r in rules:
        komponen = {var: mu[var][kat] for var, kat in r["if"].items()}
        out.append({**r, "komponen": komponen, "alpha": min(komponen.values())})
    return out


def implikasi(alphas, z):
    """Implikasi MIN: μ_i(z) = min(α_i, μ_konsekuen(z)). Return list array."""
    mf_out = {k: hitung_mf(z, spec) for k, spec in config.OUTPUT["mf"].items()}
    return [np.minimum(a["alpha"], mf_out[a["then"]]) for a in alphas]


def agregasi(terpotong, z):
    """Agregasi MAX atas semua fungsi output terpotong."""
    if not terpotong:
        return np.zeros_like(z)
    return np.max(np.vstack(terpotong), axis=0)


def centroid(z, mu):
    """Centroid diskrit Σμ·z / Σμ. Return (skor, Σμ·z, Σμ). Skor NaN bila Σμ = 0."""
    num = float(np.sum(mu * z))
    den = float(np.sum(mu))
    skor = num / den if den > 0 else float("nan")
    return skor, num, den


def inferensi(nilai, step=None, rules=None):
    """Jalankan seluruh proses Mamdani untuk satu mahasiswa."""
    z = grid_output(step)
    mu = fuzzifikasi(nilai)
    alphas = alpha_predikat(mu, rules)
    terpotong = implikasi(alphas, z)
    agr = agregasi(terpotong, z)
    skor, num, den = centroid(z, agr)
    return {
        "input": {k: float(nilai[k]) for k in config.INPUT_KEYS},
        "mu": mu,
        "alphas": alphas,
        "aktif": [a["id"] for a in alphas if a["alpha"] > 0],
        "z": z,
        "terpotong": terpotong,
        "agregasi": agr,
        "sum_mu_z": num,
        "sum_mu": den,
        "skor": skor,
        "kategori": kategori_skor(skor) if den > 0 else "Tidak terdefinisi",
    }


def skor_saja(nilai, step=None):
    """Shortcut: hanya mengembalikan skor crisp."""
    return inferensi(nilai, step)["skor"]
