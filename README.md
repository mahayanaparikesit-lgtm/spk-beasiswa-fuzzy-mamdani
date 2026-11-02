# SPK Kelayakan Penerima Beasiswa — Logika Fuzzy Metode Mamdani

Sistem pendukung keputusan yang memberi **skor rekomendasi kelayakan beasiswa (0–100)**
berdasarkan IPK, penghasilan orang tua, jumlah tanggungan keluarga, dan skor prestasi.
Mesin fuzzy (fungsi keanggotaan, fuzzifikasi, α-predikat, implikasi, agregasi, centroid)
diimplementasikan sendiri dengan NumPy; `scikit-fuzzy` hanya dipakai sebagai pembanding.

> Skor adalah **rekomendasi pendukung keputusan**, bukan keputusan final panitia.

## Metode
| Tahap | Pilihan |
|---|---|
| Operator AND | MIN |
| Implikasi | MIN (clipping) |
| Agregasi | MAX |
| Defuzzifikasi | Centroid diskrit, grid z = 0, 0.1, …, 100 (1001 titik) |

## Instalasi
```bash
pip install -r requirements.txt
```
Diuji dengan Python 3.14, NumPy 2.4, Streamlit 1.66, scikit-fuzzy 0.5.

## Menjalankan
Jalankan dari folder `fuzzy_beasiswa/`:

```bash
python scripts/grafik_mf.py        # grafik fungsi keanggotaan        -> hasil/mf_*.png
python scripts/uji_cakupan.py      # uji celah MF & cakupan aturan    -> hasil/uji_*.csv/json
python scripts/run_all.py          # proses 22 mahasiswa              -> hasil/hasil_uji.csv
python scripts/detail_satu.py      # perhitungan lengkap 1 mahasiswa  -> hasil/detail_*
python scripts/detail_satu.py 3.3 3.5 4 62   # (opsional) nilai sendiri: ipk penghasilan tanggungan prestasi
python scripts/sensitivitas.py     # analisis sensitivitas            -> hasil/sensitivitas_*
python scripts/validasi.py         # manual vs program vs skfuzzy     -> hasil/validasi*.csv
python scripts/buat_laporan.py     # susun laporan .md + .docx        -> laporan/
pytest                             # 40 test
streamlit run app.py               # aplikasi web (http://localhost:8501)
```
Di Windows, bila muncul error encoding di terminal, jalankan dulu `set PYTHONIOENCODING=utf-8`
(cmd) atau `$env:PYTHONIOENCODING='utf-8'` (PowerShell).

## Struktur
```
fuzzy_beasiswa/
├── config.py               # parameter MF, grid output, ambang kategori, 22 aturan
├── fuzzy/
│   ├── membership.py       # fungsi segitiga & trapesium
│   ├── engine.py           # fuzzifikasi, α-predikat, implikasi, agregasi, centroid
│   ├── coverage.py         # cek celah MF & cakupan aturan
│   ├── batch.py            # proses banyak data (CSV)
│   └── plotting.py         # grafik (tema terang untuk laporan, gelap untuk web)
├── data/data_mahasiswa.csv # 22 mahasiswa simulasi
├── scripts/                # run_all, detail_satu, sensitivitas, validasi, dll.
├── app.py                  # antarmuka Streamlit
├── tests/                  # pytest
├── hasil/                  # CSV & grafik PNG
└── laporan/                # laporan.md & laporan.docx
```

## Mengubah parameter
Semua parameter ada di `config.py`: bentuk & titik MF (`INPUTS`, `OUTPUT`), langkah grid
centroid (`OUTPUT_STEP`), ambang kategori (`KATEGORI_SKOR`), dan basis aturan (`RULES`).
Setelah mengubahnya, jalankan `pytest` dan `python scripts/uji_cakupan.py` untuk memastikan
tidak ada celah dan cakupan aturan tetap 100%.
