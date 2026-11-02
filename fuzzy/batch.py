"""Pemrosesan banyak mahasiswa sekaligus (dipakai run_all.py dan app.py)."""
import pandas as pd

import config
from fuzzy.engine import inferensi

KOLOM_WAJIB = config.INPUT_KEYS


def proses_dataframe(df, step=None):
    """
    df: DataFrame dengan kolom ipk, penghasilan, tanggungan, prestasi
        (kolom lain seperti id/nama dipertahankan di depan).
    Return: DataFrame berisi input, μ hasil fuzzifikasi, aturan aktif, skor, kategori.
    """
    hilang = [k for k in KOLOM_WAJIB if k not in df.columns]
    if hilang:
        raise ValueError(f"Kolom wajib tidak ada: {hilang}")
    baris = []
    for _, row in df.iterrows():
        res = inferensi({k: row[k] for k in KOLOM_WAJIB}, step)
        d = {c: row[c] for c in df.columns}
        for var in KOLOM_WAJIB:
            for kat, m in res["mu"][var].items():
                d[f"mu_{var}_{kat.lower()}"] = round(m, 4)
        aktif = [a for a in res["alphas"] if a["alpha"] > 0]
        d["jumlah_aturan_aktif"] = len(aktif)
        d["aturan_aktif"] = "; ".join(f"{a['id']}({a['alpha']:.3f})->{a['then']}" for a in aktif)
        d["skor"] = round(res["skor"], 3)
        d["kategori_kelayakan"] = res["kategori"]
        baris.append(d)
    return pd.DataFrame(baris)
