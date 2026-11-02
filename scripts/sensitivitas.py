"""
Analisis sensitivitas: setiap input diubah bertahap dari minimum ke maksimum
semesta, tiga input lain ditahan pada config.BASE_VALUES.
Hasil: hasil/sensitivitas.csv, hasil/sensitivitas_ringkasan.csv, hasil/sensitivitas_*.png
"""
import os

import _path  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config
from fuzzy.engine import skor_saja
from fuzzy.plotting import gambar_sensitivitas

N_LANGKAH = 401
# Arah yang diharapkan: +1 = makin besar input makin layak, -1 = sebaliknya
ARAH = {"ipk": 1, "penghasilan": -1, "tanggungan": 1, "prestasi": 1}


def sapuan(var):
    lo, hi = config.INPUTS[var]["semesta"]
    x = np.linspace(lo, hi, N_LANGKAH)
    y = np.array([skor_saja({**config.BASE_VALUES, var: v}) for v in x])
    return x, y


def plateau(x, y, tol=1e-6, min_lebar_frac=0.03):
    """Daftar interval [x_awal, x_akhir] tempat skor konstan (plateau)."""
    datar = np.abs(np.diff(y)) < tol
    hasil, mulai = [], None
    for i, d in enumerate(datar):
        if d and mulai is None:
            mulai = i
        if (not d or i == len(datar) - 1) and mulai is not None:
            akhir = i + 1 if d else i
            if x[akhir] - x[mulai] >= min_lebar_frac * (x[-1] - x[0]):
                hasil.append((float(x[mulai]), float(x[akhir]), float(y[mulai])))
            mulai = None
    return hasil


def ringkas(var, x, y):
    dy = np.diff(y)
    dx = x[1] - x[0]
    arah = ARAH[var]
    monoton = bool(np.all(arah * dy >= -1e-9))
    i_tajam = int(np.argmax(np.abs(dy)))
    lompatan_maks = float(np.max(np.abs(dy)))
    return {
        "variabel": var,
        "nilai_dasar": config.BASE_VALUES[var],
        "skor_di_min": round(float(y[0]), 3),
        "skor_di_maks": round(float(y[-1]), 3),
        "rentang_skor": round(float(y.max() - y.min()), 3),
        "arah_diharapkan": "naik" if arah > 0 else "turun",
        "monoton_sesuai_arah": monoton,
        "titik_paling_tajam": round(float((x[i_tajam] + x[i_tajam + 1]) / 2), 4),
        "kemiringan_maks_per_satuan": round(lompatan_maks / dx, 3),
        "perubahan_maks_per_langkah": round(lompatan_maks, 4),
        "plateau": "; ".join(f"[{a:g}–{b:g}] skor≈{s:.2f}" for a, b, s in plateau(x, y)) or "-",
    }


def main():
    semua, ringkasan = [], []
    fig_all, axes = plt.subplots(2, 2, figsize=(13, 7.5))
    for ax, var in zip(axes.flat, config.INPUT_KEYS):
        x, y = sapuan(var)
        semua.append(pd.DataFrame({"variabel": var, "nilai": x, "skor": y}))
        r = ringkas(var, x, y)
        ringkasan.append(r)
        fig = gambar_sensitivitas(x, y, var, nilai_dasar=config.BASE_VALUES[var])
        fig.savefig(os.path.join(_path.HASIL, f"sensitivitas_{var}.png"), dpi=150)
        plt.close(fig)
        # panel gabungan
        ax.plot(x, y, color="#2A78D6", linewidth=2)
        ax.axvline(config.BASE_VALUES[var], color="#5F5E58", linestyle="--", linewidth=1)
        ax.set_ylim(0, 100)
        ax.set_title(config.INPUTS[var]["label"], loc="left", fontsize=10)
        ax.grid(True, color="#E4E4E0")
        for s in ["top", "right"]:
            ax.spines[s].set_visible(False)
    fig_all.supylabel("Skor kelayakan")
    fig_all.suptitle(f"Sensitivitas skor (nilai dasar: {config.BASE_VALUES})", x=0.01, ha="left", fontsize=10)
    fig_all.tight_layout()
    fig_all.savefig(os.path.join(_path.HASIL, "sensitivitas_semua.png"), dpi=130)
    plt.close(fig_all)

    pd.concat(semua).to_csv(os.path.join(_path.HASIL, "sensitivitas.csv"), index=False)
    df = pd.DataFrame(ringkasan)
    df.to_csv(os.path.join(_path.HASIL, "sensitivitas_ringkasan.csv"), index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 120)
    print("Nilai dasar:", config.BASE_VALUES, "-> skor", round(skor_saja(config.BASE_VALUES), 3))
    print(df.T.to_string())


if __name__ == "__main__":
    main()
