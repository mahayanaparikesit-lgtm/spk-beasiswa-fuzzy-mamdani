"""
Grafik matplotlib untuk laporan (tema "terang") dan aplikasi web (tema "gelap").
Tema gelap mengikuti DESIGN.md: latar #121212, kartu #1E1E1E, grid #2C2C2E,
aksen data #00E5FF.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import config
from fuzzy.membership import hitung_mf

TEMA = {
    "terang": {
        "bg": "#FFFFFF", "panel": "#FFFFFF", "grid": "#E4E4E0", "teks": "#1A1A19",
        "teks2": "#5F5E58", "aksen": "#2A78D6", "isi": "#2A78D6", "titik": "#D62828",
        "seri": ["#2A78D6", "#EB6834", "#1BAF7A", "#EDA100"],
    },
    "gelap": {
        "bg": "#121212", "panel": "#1E1E1E", "grid": "#2C2C2E", "teks": "#FFFFFF",
        "teks2": "#98989D", "aksen": "#00E5FF", "isi": "#00E5FF", "titik": "#FF453A",
        "seri": ["#3987E5", "#D95926", "#199E70", "#C98500"],
    },
}


def _gaya(ax, t):
    ax.set_facecolor(t["panel"])
    ax.grid(True, color=t["grid"], linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color(t["grid"])
    ax.tick_params(colors=t["teks2"], labelsize=9)
    ax.xaxis.label.set_color(t["teks2"])
    ax.yaxis.label.set_color(t["teks2"])
    # judul loc="left" disimpan di _left_title, bukan ax.title
    for judul in (ax.title, ax._left_title, ax._right_title):
        judul.set_color(t["teks"])


def _fig(t, w=8, h=3.6, **kw):
    fig, ax = plt.subplots(figsize=(w, h), **kw)
    fig.patch.set_facecolor(t["bg"])
    return fig, ax


def _info_var(var):
    return config.OUTPUT if var == config.OUTPUT["key"] else config.INPUTS[var]


def _label_sumbu(info):
    return f"{info['label']} ({info['satuan']})" if info["satuan"] else info["label"]


def gambar_mf_ax(ax, var, tema="terang", nilai=None):
    """Gambar semua kategori satu variabel ke ax. nilai: garis penanda input (opsional)."""
    t = TEMA[tema]
    info = _info_var(var)
    lo, hi = info["semesta"]
    x = np.linspace(lo, hi, 2001)
    for i, (kat, spec) in enumerate(info["mf"].items()):
        warna = t["seri"][i]
        y = hitung_mf(x, spec)
        ax.plot(x, y, color=warna, linewidth=2, label=kat)
        # label langsung di tengah daerah μ = 1
        puncak = x[y >= 0.999]
        xm = (puncak.min() + puncak.max()) / 2
        ax.text(xm, 1.05, kat, color=t["teks"], ha="center", va="bottom", fontsize=9)
        if nilai is not None:
            m = float(hitung_mf(np.array([nilai]), spec)[0])
            if m > 0:
                ax.plot([lo, nilai], [m, m], color=warna, linewidth=1, linestyle=":")
                ax.plot(nilai, m, "o", color=warna, markersize=7,
                        markeredgecolor=t["panel"], markeredgewidth=2)
    if nilai is not None:
        ax.axvline(nilai, color=t["teks2"], linewidth=1.2, linestyle="--")
    ax.set_xlim(lo, hi)
    ax.set_ylim(0, 1.2)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xlabel(_label_sumbu(info))
    ax.set_ylabel("Derajat keanggotaan μ")
    ax.set_title(f"Fungsi keanggotaan — {info['label']}", fontsize=11, loc="left")
    ax.legend(loc="center right", fontsize=8, frameon=False, labelcolor=t["teks2"])
    _gaya(ax, t)


def gambar_mf(var, tema="terang", nilai=None):
    fig, ax = _fig(TEMA[tema])
    gambar_mf_ax(ax, var, tema, nilai)
    fig.tight_layout()
    return fig


def gambar_agregasi(res, tema="terang", judul=None):
    """Daerah hasil agregasi MAX + MF output (garis tipis) + titik centroid."""
    t = TEMA[tema]
    fig, ax = _fig(t, 8, 3.8)
    z = res["z"]
    for i, (kat, spec) in enumerate(config.OUTPUT["mf"].items()):
        ax.plot(z, hitung_mf(z, spec), color=t["seri"][i], linewidth=1, linestyle="--", alpha=0.8)
        y = hitung_mf(z, spec)
        puncak = z[y >= 0.999]
        ax.text((puncak.min() + puncak.max()) / 2, 1.04, kat, color=t["teks2"], ha="center", fontsize=8)
    ax.fill_between(z, res["agregasi"], color=t["isi"], alpha=0.35, linewidth=0)
    ax.plot(z, res["agregasi"], color=t["aksen"], linewidth=2, label="Agregasi MAX")
    s = res["skor"]
    ax.axvline(s, color=t["titik"], linewidth=2)
    ax.text(s + 1, 0.9, f"Centroid z* = {s:.2f}\n({res['kategori']})", color=t["teks"], fontsize=9)
    ax.set_xlim(*config.OUTPUT["semesta"])
    ax.set_ylim(0, 1.15)
    ax.set_xlabel("Skor kelayakan z")
    ax.set_ylabel("μ")
    ax.set_title(judul or "Daerah hasil agregasi MAX (area terarsir) dan titik centroid", fontsize=11, loc="left")
    _gaya(ax, t)
    fig.tight_layout()
    return fig


def gambar_implikasi(res, tema="terang"):
    """Small multiples: fungsi output terpotong (clipping) untuk setiap aturan aktif."""
    t = TEMA[tema]
    aktif = [(a, c) for a, c in zip(res["alphas"], res["terpotong"]) if a["alpha"] > 0]
    n = len(aktif)
    kol = 4
    bar = int(np.ceil(n / kol))
    fig, axes = plt.subplots(bar, kol, figsize=(12, 2.3 * bar), sharex=True, sharey=True, squeeze=False)
    fig.patch.set_facecolor(t["bg"])
    z = res["z"]
    nama_out = list(config.OUTPUT["mf"].keys())
    for ax, (a, c) in zip(axes.flat, aktif):
        idx = nama_out.index(a["then"])
        warna = t["seri"][idx]
        ax.plot(z, hitung_mf(z, config.OUTPUT["mf"][a["then"]]), color=warna, linewidth=1, linestyle="--")
        ax.fill_between(z, c, color=warna, alpha=0.45, linewidth=0)
        ax.axhline(a["alpha"], color=t["teks2"], linewidth=0.8, linestyle=":")
        ax.set_title(f"{a['id']} → {a['then']}  (α={a['alpha']:.3f})", fontsize=9, loc="left")
        ax.set_ylim(0, 1.05)
        _gaya(ax, t)
    for ax in list(axes.flat)[n:]:
        ax.set_visible(False)
    fig.suptitle("Implikasi MIN: fungsi output terpotong setinggi α", color=t["teks"], x=0.01, ha="left")
    fig.supxlabel("Skor kelayakan z", color=t["teks2"], fontsize=9)
    fig.tight_layout()
    return fig


def gambar_sensitivitas(x, y, var, tema="terang", nilai_dasar=None):
    t = TEMA[tema]
    info = config.INPUTS[var]
    fig, ax = _fig(t, 8, 3.6)
    # pita kategori kelayakan sebagai latar
    for i, (lo, hi, nama) in enumerate(config.KATEGORI_SKOR):
        ax.axhspan(lo, min(hi, 100), color=t["seri"][i], alpha=0.07, linewidth=0)
        ax.text(info["semesta"][1], (lo + min(hi, 100)) / 2, f" {nama}", color=t["teks2"],
                fontsize=8, va="center", ha="left")
    ax.plot(x, y, color=t["aksen"], linewidth=2)
    if nilai_dasar is not None:
        ax.axvline(nilai_dasar, color=t["teks2"], linestyle="--", linewidth=1)
        ax.text(nilai_dasar, 3, f" nilai dasar = {nilai_dasar:g}", color=t["teks2"], fontsize=8)
    ax.set_xlim(*info["semesta"])
    ax.set_ylim(0, 100)
    ax.set_xlabel(_label_sumbu(info))
    ax.set_ylabel("Skor kelayakan")
    ax.set_title(f"Sensitivitas skor terhadap {info['label']}", fontsize=11, loc="left")
    _gaya(ax, t)
    fig.tight_layout()
    return fig
