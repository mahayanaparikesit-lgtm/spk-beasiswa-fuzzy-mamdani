"""Jalankan seluruh data mahasiswa -> hasil/hasil_uji.csv."""
import os

import _path  # noqa: F401
import pandas as pd

from fuzzy.batch import proses_dataframe


def main():
    df = pd.read_csv(os.path.join(_path.ROOT, "data", "data_mahasiswa.csv"))
    hasil = proses_dataframe(df)
    path = os.path.join(_path.HASIL, "hasil_uji.csv")
    hasil.to_csv(path, index=False)
    ringkas = hasil[["id", "nama_samaran", "ipk", "penghasilan", "tanggungan", "prestasi",
                     "jumlah_aturan_aktif", "skor", "kategori_kelayakan", "kategori_uji"]]
    pd.set_option("display.width", 200)
    print(ringkas.to_string(index=False))
    print("\nDistribusi kategori:")
    print(hasil["kategori_kelayakan"].value_counts().to_string())
    print("\ntersimpan:", path)


if __name__ == "__main__":
    main()
