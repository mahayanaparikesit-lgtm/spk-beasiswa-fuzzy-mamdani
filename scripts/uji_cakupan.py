"""
Uji celah fungsi keanggotaan dan cakupan basis aturan.
Hasil: hasil/uji_celah_mf.csv, hasil/uji_cakupan.json, hasil/basis_aturan.csv
"""
import json
import os

import _path  # noqa: F401
import pandas as pd

import config
from fuzzy.coverage import cek_celah_mf, cek_cakupan_aturan, cek_kombinasi_kategori


def main():
    # 1. Celah MF
    celah = cek_celah_mf()
    df = pd.DataFrame([
        {"variabel": v, "tanpa_celah": h["ok"], "min_dari_max_mu": round(h["min_max_mu"], 4),
         "titik_terlemah": h["titik_terlemah"]}
        for v, h in celah.items()
    ])
    df.to_csv(os.path.join(_path.HASIL, "uji_celah_mf.csv"), index=False)
    print("=== Uji celah MF (10001 titik per semesta) ===")
    print(df.to_string(index=False))

    # 2. Cakupan aturan: grid numerik pada beberapa resolusi + cek logis 81 kombinasi
    hasil = {"grid": []}
    print("\n=== Uji cakupan aturan (grid 4 dimensi) ===")
    for n in [20, 30, 40]:
        c = cek_cakupan_aturan(n)
        hasil["grid"].append(c)
        print(f"{n} titik/variabel: {c['tercakup']}/{c['total_kombinasi']} tercakup "
              f"({c['persen']:.2f}%), aturan aktif min={c['aturan_aktif_min']} "
              f"maks={c['aturan_aktif_maks']} rata2={c['aturan_aktif_rata2']:.2f}, "
              f"min(α maks)={c['min_alpha_maks']:.3f}")
        if c["contoh_tidak_tercakup"]:
            print("  contoh tidak tercakup:", c["contoh_tidak_tercakup"])
    k = cek_kombinasi_kategori()
    hasil["kombinasi_kategori"] = {"total": k["total"], "tidak_tercakup": k["tidak_tercakup"]}
    print(f"Kombinasi kategori: {k['total'] - len(k['tidak_tercakup'])}/{k['total']} punya aturan")
    with open(os.path.join(_path.HASIL, "uji_cakupan.json"), "w", encoding="utf-8") as f:
        json.dump(hasil, f, indent=2, ensure_ascii=False)

    # 3. Tabel basis aturan
    rows = []
    for r in config.RULES:
        d = {"id": r["id"]}
        for var in config.INPUT_KEYS:
            d[var] = r["if"].get(var, "-")
        d["kelayakan"] = r["then"]
        d["alasan"] = r["alasan"]
        rows.append(d)
    pd.DataFrame(rows).to_csv(os.path.join(_path.HASIL, "basis_aturan.csv"), index=False)
    print(f"\nBasis aturan: {len(rows)} aturan -> hasil/basis_aturan.csv")


if __name__ == "__main__":
    main()
