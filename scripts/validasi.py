"""
Validasi hasil program.

1. Perhitungan MANUAL: ditulis ulang secara eksplisit dengan Python murni
   (tanpa NumPy, tanpa memanggil engine/config). Rumus MF diketik langsung
   dengan angka parameternya, setiap aturan ditulis satu per satu.
2. Pembanding scikit-fuzzy (skfuzzy.control) dengan MF & aturan yang sama.
3. Efek resolusi grid centroid.
Hasil: hasil/validasi.csv, hasil/validasi_manual.md, hasil/efek_grid.csv
"""
import os

import _path  # noqa: F401
import pandas as pd

import config
from fuzzy.engine import inferensi

KASUS = {
    "M09 Indah (tumpang tindih)": (3.3, 3.5, 4, 62),
    "M13 Maya (bertentangan)": (2.1, 0.8, 7, 25),
    "M17 Rizky (normal)": (3.45, 5.2, 3, 66),
    "M12 Lukman (bertentangan)": (3.9, 12.0, 2, 85),
}


# ---------------------------------------------------------------------------
# 1. MANUAL — rumus ditulis langsung
# ---------------------------------------------------------------------------
# IPK: Rendah trap(0,0,2.5,3), Sedang tri(2.5,3,3.5), Tinggi trap(3,3.5,4,4)
def ipk_rendah(x):
    if x <= 2.5:
        return 1.0
    if x >= 3.0:
        return 0.0
    return (3.0 - x) / (3.0 - 2.5)


def ipk_sedang(x):
    if x <= 2.5 or x >= 3.5:
        return 0.0
    if x <= 3.0:
        return (x - 2.5) / (3.0 - 2.5)
    return (3.5 - x) / (3.5 - 3.0)


def ipk_tinggi(x):
    if x <= 3.0:
        return 0.0
    if x >= 3.5:
        return 1.0
    return (x - 3.0) / (3.5 - 3.0)


# Penghasilan: Rendah trap(0,0,2,4), Sedang trap(2,4,6,9), Tinggi trap(6,9,15,15)
def pgh_rendah(x):
    if x <= 2:
        return 1.0
    if x >= 4:
        return 0.0
    return (4 - x) / (4 - 2)


def pgh_sedang(x):
    if x <= 2 or x >= 9:
        return 0.0
    if x < 4:
        return (x - 2) / (4 - 2)
    if x <= 6:
        return 1.0
    return (9 - x) / (9 - 6)


def pgh_tinggi(x):
    if x <= 6:
        return 0.0
    if x >= 9:
        return 1.0
    return (x - 6) / (9 - 6)


# Tanggungan: Sedikit trap(0,0,1,3), Sedang tri(1,3,5), Banyak trap(3,5,8,8)
def tg_sedikit(x):
    if x <= 1:
        return 1.0
    if x >= 3:
        return 0.0
    return (3 - x) / (3 - 1)


def tg_sedang(x):
    if x <= 1 or x >= 5:
        return 0.0
    if x <= 3:
        return (x - 1) / (3 - 1)
    return (5 - x) / (5 - 3)


def tg_banyak(x):
    if x <= 3:
        return 0.0
    if x >= 5:
        return 1.0
    return (x - 3) / (5 - 3)


# Prestasi: Rendah trap(0,0,30,50), Sedang tri(30,50,70), Tinggi trap(50,70,100,100)
def pr_rendah(x):
    if x <= 30:
        return 1.0
    if x >= 50:
        return 0.0
    return (50 - x) / (50 - 30)


def pr_sedang(x):
    if x <= 30 or x >= 70:
        return 0.0
    if x <= 50:
        return (x - 30) / (50 - 30)
    return (70 - x) / (70 - 50)


def pr_tinggi(x):
    if x <= 50:
        return 0.0
    if x >= 70:
        return 1.0
    return (x - 50) / (70 - 50)


# Output: TL trap(0,0,25,45), CL tri(25,45,65), L tri(45,65,85), SL trap(65,85,100,100)
def out_tl(z):
    if z <= 25:
        return 1.0
    if z >= 45:
        return 0.0
    return (45 - z) / 20


def out_cl(z):
    if z <= 25 or z >= 65:
        return 0.0
    if z <= 45:
        return (z - 25) / 20
    return (65 - z) / 20


def out_l(z):
    if z <= 45 or z >= 85:
        return 0.0
    if z <= 65:
        return (z - 45) / 20
    return (85 - z) / 20


def out_sl(z):
    if z <= 65:
        return 0.0
    if z >= 85:
        return 1.0
    return (z - 65) / 20


def manual(ipk, pgh, tg, pr, log):
    # Langkah 1: fuzzifikasi
    iR, iS, iT = ipk_rendah(ipk), ipk_sedang(ipk), ipk_tinggi(ipk)
    pR, pS, pT = pgh_rendah(pgh), pgh_sedang(pgh), pgh_tinggi(pgh)
    tS, tM, tB = tg_sedikit(tg), tg_sedang(tg), tg_banyak(tg)
    sR, sS, sT = pr_rendah(pr), pr_sedang(pr), pr_tinggi(pr)
    log.append(f"Fuzzifikasi: IPK(R,S,T)=({iR:.4f}, {iS:.4f}, {iT:.4f}); "
               f"Penghasilan(R,S,T)=({pR:.4f}, {pS:.4f}, {pT:.4f}); "
               f"Tanggungan(Sd,S,B)=({tS:.4f}, {tM:.4f}, {tB:.4f}); "
               f"Prestasi(R,S,T)=({sR:.4f}, {sS:.4f}, {sT:.4f})")

    # Langkah 2: α-predikat (MIN), aturan ditulis satu per satu
    a = [
        ("R1", min(iR, pR), "CL"), ("R2", min(iR, pS), "TL"), ("R3", min(iR, pT), "TL"),
        ("R4", min(iS, pR), "L"), ("R5", min(iS, pS), "CL"), ("R6", min(iS, pT), "TL"),
        ("R7", min(iT, pR), "SL"), ("R8", min(iT, pS), "L"), ("R9", min(iT, pT), "CL"),
        ("R10", min(sR, tS), "TL"), ("R11", min(sR, tM), "TL"), ("R12", min(sR, tB), "CL"),
        ("R13", min(sS, tS), "TL"), ("R14", min(sS, tM), "CL"), ("R15", min(sS, tB), "L"),
        ("R16", min(sT, tS), "CL"), ("R17", min(sT, tM), "L"), ("R18", min(sT, tB), "SL"),
        ("R19", min(iR, sR), "TL"), ("R20", min(pT, tS), "TL"),
        ("R21", min(pR, tB), "L"), ("R22", min(iT, sT), "L"),
    ]
    log.append("α aktif: " + ", ".join(f"{r}={v:.4f}→{k}" for r, v, k in a if v > 0))

    # Langkah 3: tinggi potongan per kategori output = MAX α aturan berkonsekuen sama
    h = {"TL": 0.0, "CL": 0.0, "L": 0.0, "SL": 0.0}
    for _, v, k in a:
        if v > h[k]:
            h[k] = v
    log.append("Tinggi potongan: " + ", ".join(f"{k}={v:.4f}" for k, v in h.items()))

    # Langkah 4 & 5: agregasi MAX dan centroid diskrit, z = 0, 0.1, ..., 100
    pembilang, penyebut = 0.0, 0.0
    for i in range(1001):
        z = i * 0.1
        mu = max(min(h["TL"], out_tl(z)), min(h["CL"], out_cl(z)),
                 min(h["L"], out_l(z)), min(h["SL"], out_sl(z)))
        pembilang += mu * z
        penyebut += mu
    skor = pembilang / penyebut
    log.append(f"Centroid: Σμz / Σμ = {pembilang:.4f} / {penyebut:.4f} = {skor:.4f}")
    return skor


# ---------------------------------------------------------------------------
# 2. scikit-fuzzy
# ---------------------------------------------------------------------------
def bangun_skfuzzy():
    import numpy as np
    import skfuzzy as fuzz
    from skfuzzy import control as ctrl

    def mf(univ, spec):
        bentuk, p = spec
        return fuzz.trimf(univ, p) if bentuk == "tri" else fuzz.trapmf(univ, p)

    ant = {}
    for k in config.INPUT_KEYS:
        lo, hi = config.INPUTS[k]["semesta"]
        univ = np.round(np.arange(lo, hi + 1e-9, (hi - lo) / 15000), 6)
        ant[k] = ctrl.Antecedent(univ, k)
        for kat, spec in config.INPUTS[k]["mf"].items():
            ant[k][kat] = mf(univ, spec)
    z = np.round(np.arange(0, 100 + 1e-9, config.OUTPUT_STEP), 6)
    out = ctrl.Consequent(z, "kelayakan", defuzzify_method="centroid")
    for kat, spec in config.OUTPUT["mf"].items():
        out[kat] = mf(z, spec)
    rules = []
    for r in config.RULES:
        terms = [ant[v][c] for v, c in r["if"].items()]
        expr = terms[0]
        for t in terms[1:]:
            expr = expr & t  # AND = fmin (default skfuzzy)
        rules.append(ctrl.Rule(expr, out[r["then"]]))
    return ctrl.ControlSystem(rules)


def skor_skfuzzy(sistem, nilai):
    from skfuzzy import control as ctrl
    sim = ctrl.ControlSystemSimulation(sistem)
    for k, v in nilai.items():
        sim.input[k] = v
    sim.compute()
    return float(sim.output["kelayakan"])


def main():
    baris, md = [], ["## Validasi manual vs program\n"]
    try:
        sistem = bangun_skfuzzy()
    except Exception as e:  # skfuzzy opsional
        print("scikit-fuzzy tidak tersedia:", e)
        sistem = None

    for nama, (i, p, t, s) in KASUS.items():
        log = []
        sm = manual(i, p, t, s, log)
        nilai = dict(zip(config.INPUT_KEYS, (i, p, t, s)))
        sp = inferensi(nilai)["skor"]
        sk = skor_skfuzzy(sistem, nilai) if sistem else float("nan")
        baris.append({"kasus": nama, "ipk": i, "penghasilan": p, "tanggungan": t, "prestasi": s,
                      "skor_manual": round(sm, 6), "skor_program": round(sp, 6),
                      "selisih_manual_program": abs(sm - sp),
                      "skor_skfuzzy": round(sk, 6), "selisih_program_skfuzzy": round(abs(sp - sk), 6)})
        md.append(f"### {nama}: IPK={i}, penghasilan={p}, tanggungan={t}, prestasi={s}\n")
        md += [f"- {x}" for x in log]
        md.append(f"- **Manual = {sm:.6f}; Program = {sp:.6f}; selisih = {abs(sm - sp):.2e}; "
                  f"scikit-fuzzy = {sk:.6f}**\n")

    df = pd.DataFrame(baris)
    df.to_csv(os.path.join(_path.HASIL, "validasi.csv"), index=False)
    with open(os.path.join(_path.HASIL, "validasi_manual.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    pd.set_option("display.width", 250)
    print("\n".join(md))
    print(df.to_string(index=False))

    # 3. Efek resolusi grid centroid
    langkah = [0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
    rows = []
    for nama, v in KASUS.items():
        nilai = dict(zip(config.INPUT_KEYS, v))
        acuan = inferensi(nilai, step=0.001)["skor"]
        d = {"kasus": nama, "acuan_langkah_0.001": round(acuan, 4)}
        for st in langkah:
            d[f"langkah_{st:g}"] = round(inferensi(nilai, step=st)["skor"], 4)
        rows.append(d)
    g = pd.DataFrame(rows)
    g.to_csv(os.path.join(_path.HASIL, "efek_grid.csv"), index=False)
    print("\nEfek resolusi grid centroid:")
    print(g.to_string(index=False))


if __name__ == "__main__":
    main()
