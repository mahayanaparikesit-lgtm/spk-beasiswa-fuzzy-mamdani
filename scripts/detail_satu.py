"""
Perhitungan lengkap langkah demi langkah untuk satu mahasiswa.

Pemakaian:
    python scripts/detail_satu.py                      # kasus config.DETAIL_CASE
    python scripts/detail_satu.py 3.3 3.5 4 62         # ipk penghasilan tanggungan prestasi
Hasil: hasil/detail_perhitungan.md, hasil/detail_*.png
"""
import os
import sys

import _path  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np

import config
from fuzzy.engine import inferensi
from fuzzy.membership import rumus_substitusi, hitung_mf
from fuzzy.plotting import gambar_agregasi, gambar_implikasi, gambar_mf_ax, TEMA


def buat_markdown(res):
    L = []
    nilai = res["input"]
    L.append("### Data mahasiswa\n")
    L.append("| Variabel | Nilai |\n|---|---|")
    for k in config.INPUT_KEYS:
        info = config.INPUTS[k]
        L.append(f"| {info['label']} | {nilai[k]:g} {info['satuan']} |")

    # Langkah 1
    L.append("\n### Langkah 1 — Fuzzifikasi\n")
    L.append("| Variabel | Kategori | Parameter | Substitusi | μ |\n|---|---|---|---|---|")
    for k in config.INPUT_KEYS:
        info = config.INPUTS[k]
        for kat, spec in info["mf"].items():
            par = f"{spec[0]}({', '.join(f'{v:g}' for v in spec[1])})"
            L.append(f"| {info['label']} | {kat} | {par} | {rumus_substitusi(nilai[k], spec)} | "
                     f"**{res['mu'][k][kat]:.4f}** |")

    # Langkah 2
    L.append("\n### Langkah 2 — α-predikat setiap aturan (AND = MIN)\n")
    L.append("| Aturan | Anteseden | MIN(...) | α | Konsekuen |\n|---|---|---|---|---|")
    for a in res["alphas"]:
        ant = " ∧ ".join(f"{config.INPUTS[v]['label']} {c}" for v, c in a["if"].items())
        mins = ", ".join(f"{m:.4f}" for m in a["komponen"].values())
        tebal = f"**{a['alpha']:.4f}**" if a["alpha"] > 0 else "0"
        L.append(f"| {a['id']} | {ant} | MIN({mins}) | {tebal} | {a['then']} |")
    aktif = [a for a in res["alphas"] if a["alpha"] > 0]
    L.append(f"\nAturan aktif (α > 0): **{len(aktif)}** dari {len(res['alphas'])} — "
             + ", ".join(a["id"] for a in aktif) + ".")

    # Langkah 3
    L.append("\n### Langkah 3 — Implikasi MIN (clipping)\n")
    L.append("Untuk setiap aturan aktif i: μ_i(z) = min(α_i, μ_konsekuen(z)). "
             "Jika beberapa aturan memiliki konsekuen sama, yang menentukan bentuk akhir adalah α terbesar:\n")
    L.append("| Kategori output | Aturan aktif | α terbesar (tinggi potongan) |\n|---|---|---|")
    tinggi = {}
    for kat in config.OUTPUT["mf"]:
        ids = [a for a in aktif if a["then"] == kat]
        if ids:
            tinggi[kat] = max(a["alpha"] for a in ids)
            L.append(f"| {kat} | {', '.join(f'{a['id']} ({a['alpha']:.4f})' for a in ids)} | "
                     f"**{tinggi[kat]:.4f}** |")
        else:
            L.append(f"| {kat} | – | 0 |")
    L.append("\n![Implikasi](detail_implikasi.png)")

    # Langkah 4
    L.append("\n### Langkah 4 — Agregasi MAX\n")
    L.append("μ_agr(z) = max_i μ_i(z) = max over kategori k dari min(α_k, μ_k(z)), "
             "dengan α_k = tinggi potongan pada tabel di atas.\n")
    L.append("Contoh nilai μ_agr pada beberapa titik z:\n")
    z = res["z"]
    L.append("| z | " + " | ".join(f"min(α, μ_{k})" for k in config.OUTPUT["mf"]) + " | μ_agr(z) |")
    L.append("|---|" + "---|" * (len(config.OUTPUT["mf"]) + 1))
    for zz in [0, 10, 20, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 100]:
        i = int(round(zz / config.OUTPUT_STEP))
        sel = []
        for kat, spec in config.OUTPUT["mf"].items():
            sel.append(f"{min(tinggi.get(kat, 0.0), float(hitung_mf(np.array([zz]), spec)[0])):.4f}")
        L.append(f"| {zz} | " + " | ".join(sel) + f" | **{res['agregasi'][i]:.4f}** |")
    L.append("\n![Agregasi](detail_agregasi.png)")

    # Langkah 5
    L.append("\n### Langkah 5 — Defuzzifikasi centroid (diskrit)\n")
    L.append(f"Grid output: z = 0, {config.OUTPUT_STEP:g}, {2 * config.OUTPUT_STEP:g}, …, 100 "
             f"(langkah Δz = {config.OUTPUT_STEP:g}, **{len(z)} titik**).\n")
    L.append("$$z^* = \\frac{\\sum_{i} \\mu_{agr}(z_i)\\, z_i}{\\sum_{i} \\mu_{agr}(z_i)}"
             f" = \\frac{{{res['sum_mu_z']:.4f}}}{{{res['sum_mu']:.4f}}} = {res['skor']:.4f}$$\n")
    L.append(f"**Skor kelayakan = {res['skor']:.2f} → kategori _{res['kategori']}_** "
             "(rekomendasi, bukan keputusan final).")
    return "\n".join(L)


def main():
    if len(sys.argv) == 5:
        nilai = dict(zip(config.INPUT_KEYS, map(float, sys.argv[1:5])))
    else:
        nilai = config.DETAIL_CASE
    res = inferensi(nilai)

    md = buat_markdown(res)
    with open(os.path.join(_path.HASIL, "detail_perhitungan.md"), "w", encoding="utf-8") as f:
        f.write(md)
    print(md)

    # grafik fuzzifikasi (4 panel dengan penanda nilai input)
    fig, axes = plt.subplots(2, 2, figsize=(12, 6.5))
    fig.patch.set_facecolor(TEMA["terang"]["bg"])
    for ax, k in zip(axes.flat, config.INPUT_KEYS):
        gambar_mf_ax(ax, k, nilai=nilai[k])
    fig.tight_layout()
    fig.savefig(os.path.join(_path.HASIL, "detail_fuzzifikasi.png"), dpi=130)
    plt.close(fig)

    fig = gambar_implikasi(res)
    fig.savefig(os.path.join(_path.HASIL, "detail_implikasi.png"), dpi=130)
    plt.close(fig)

    fig = gambar_agregasi(res)
    fig.savefig(os.path.join(_path.HASIL, "detail_agregasi.png"), dpi=150)
    plt.close(fig)
    print("\ntersimpan: hasil/detail_perhitungan.md, detail_fuzzifikasi.png, "
          "detail_implikasi.png, detail_agregasi.png")


if __name__ == "__main__":
    main()
