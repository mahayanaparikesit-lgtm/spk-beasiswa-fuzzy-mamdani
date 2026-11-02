"""Buat grafik fungsi keanggotaan semua variabel -> hasil/mf_*.png."""
import os

import _path  # noqa: F401
import matplotlib.pyplot as plt

import config
from fuzzy.plotting import gambar_mf, gambar_mf_ax, TEMA


def main():
    semua = config.INPUT_KEYS + [config.OUTPUT["key"]]
    for var in semua:
        fig = gambar_mf(var)
        path = os.path.join(_path.HASIL, f"mf_{var}.png")
        fig.savefig(path, dpi=150)
        plt.close(fig)
        print("tersimpan:", path)

    # satu gambar gabungan 5 panel
    fig, axes = plt.subplots(5, 1, figsize=(8, 16))
    fig.patch.set_facecolor(TEMA["terang"]["bg"])
    for ax, var in zip(axes, semua):
        gambar_mf_ax(ax, var)
    fig.tight_layout()
    path = os.path.join(_path.HASIL, "mf_semua.png")
    fig.savefig(path, dpi=130)
    plt.close(fig)
    print("tersimpan:", path)


if __name__ == "__main__":
    main()
