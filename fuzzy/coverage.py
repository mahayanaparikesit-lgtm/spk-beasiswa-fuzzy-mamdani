"""Pengecekan celah fungsi keanggotaan dan cakupan basis aturan."""
import itertools

import numpy as np

import config
from fuzzy.membership import hitung_mf


def cek_celah_mf(n_titik=10001):
    """
    Untuk setiap variabel (input & output), sisir semesta dengan n_titik sampel
    dan cek bahwa di setiap titik minimal satu kategori bernilai μ > 0.
    Return: {var: {"ok", "min_max_mu", "titik_celah"}}
    """
    semua = {**{k: config.INPUTS[k] for k in config.INPUT_KEYS}, config.OUTPUT["key"]: config.OUTPUT}
    hasil = {}
    for var, info in semua.items():
        lo, hi = info["semesta"]
        x = np.linspace(lo, hi, n_titik)
        mus = np.vstack([hitung_mf(x, spec) for spec in info["mf"].values()])
        maks = mus.max(axis=0)
        celah = x[maks <= 0]
        hasil[var] = {
            "ok": celah.size == 0,
            "min_max_mu": float(maks.min()),
            "titik_terlemah": float(x[np.argmin(maks)]),
            "titik_celah": celah.tolist()[:10],
        }
    return hasil


def cek_cakupan_aturan(n_titik=None, rules=None):
    """
    Sisir grid seluruh kombinasi 4 input (n_titik per variabel) dan cek bahwa
    setiap kombinasi mengaktifkan minimal satu aturan (α > 0).
    Dihitung tervektorisasi: μ setiap kategori dihitung per sumbu, lalu
    α = MIN anteseden disebar (broadcast) ke grid 4 dimensi.
    """
    n = config.COVERAGE_POINTS if n_titik is None else n_titik
    rules = config.RULES if rules is None else rules
    sumbu = {k: np.linspace(*config.INPUTS[k]["semesta"], n) for k in config.INPUT_KEYS}
    mu_sumbu = {
        k: {kat: hitung_mf(sumbu[k], spec) for kat, spec in config.INPUTS[k]["mf"].items()}
        for k in config.INPUT_KEYS
    }
    bentuk = (n,) * len(config.INPUT_KEYS)
    alpha_maks = np.zeros(bentuk)
    jumlah_aktif = np.zeros(bentuk, dtype=int)
    for r in rules:
        a = np.ones(bentuk)
        for var, kat in r["if"].items():
            idx = config.INPUT_KEYS.index(var)
            shape = [1] * len(bentuk)
            shape[idx] = n
            a = np.minimum(a, mu_sumbu[var][kat].reshape(shape))
        alpha_maks = np.maximum(alpha_maks, a)
        jumlah_aktif += (a > 0)

    tidak = np.argwhere(alpha_maks <= 0)
    contoh = [
        {k: float(sumbu[k][i]) for k, i in zip(config.INPUT_KEYS, idx)}
        for idx in tidak[:10]
    ]
    total = alpha_maks.size
    return {
        "titik_per_variabel": n,
        "total_kombinasi": int(total),
        "tercakup": int(total - len(tidak)),
        "persen": 100.0 * (total - len(tidak)) / total,
        "contoh_tidak_tercakup": contoh,
        "min_alpha_maks": float(alpha_maks.min()),
        "aturan_aktif_min": int(jumlah_aktif.min()),
        "aturan_aktif_maks": int(jumlah_aktif.max()),
        "aturan_aktif_rata2": float(jumlah_aktif.mean()),
    }


def cek_kombinasi_kategori(rules=None):
    """
    Cek secara logis: untuk setiap kombinasi kategori (3^4 = 81), apakah ada
    aturan yang antesedennya terpenuhi oleh kombinasi tersebut.
    """
    rules = config.RULES if rules is None else rules
    kats = [list(config.INPUTS[k]["mf"].keys()) for k in config.INPUT_KEYS]
    tidak = []
    for kombi in itertools.product(*kats):
        d = dict(zip(config.INPUT_KEYS, kombi))
        if not any(all(d[v] == c for v, c in r["if"].items()) for r in rules):
            tidak.append(d)
    return {"total": len(list(itertools.product(*kats))), "tidak_tercakup": tidak}
