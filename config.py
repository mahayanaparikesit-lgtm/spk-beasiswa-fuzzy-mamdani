"""
Konfigurasi SPK Kelayakan Beasiswa (Fuzzy Mamdani).

Semua parameter fungsi keanggotaan (MF), grid output, ambang kategori,
dan basis aturan disimpan di sini agar mudah diubah tanpa menyentuh engine.

Format MF:
    ("trap", [a, b, c, d])  -> trapesium: naik a..b, datar 1 di b..c, turun c..d
    ("tri",  [a, b, c])     -> segitiga : naik a..b, puncak di b, turun b..c
Bahu kiri ditulis trap(min, min, c, d), bahu kanan trap(a, b, max, max).
"""

# ---------------------------------------------------------------------------
# Variabel input
# ---------------------------------------------------------------------------
INPUTS = {
    "ipk": {
        "label": "IPK",
        "satuan": "",
        "semesta": (0.0, 4.0),
        "mf": {
            "Rendah": ("trap", [0.0, 0.0, 2.5, 3.0]),
            "Sedang": ("tri", [2.5, 3.0, 3.5]),
            "Tinggi": ("trap", [3.0, 3.5, 4.0, 4.0]),
        },
    },
    "penghasilan": {
        "label": "Penghasilan Orang Tua",
        "satuan": "juta Rp/bulan",
        "semesta": (0.0, 15.0),
        "mf": {
            "Rendah": ("trap", [0.0, 0.0, 2.0, 4.0]),
            "Sedang": ("trap", [2.0, 4.0, 6.0, 9.0]),
            "Tinggi": ("trap", [6.0, 9.0, 15.0, 15.0]),
        },
    },
    "tanggungan": {
        "label": "Jumlah Tanggungan Keluarga",
        "satuan": "orang",
        "semesta": (0.0, 8.0),
        "mf": {
            "Sedikit": ("trap", [0.0, 0.0, 1.0, 3.0]),
            "Sedang": ("tri", [1.0, 3.0, 5.0]),
            "Banyak": ("trap", [3.0, 5.0, 8.0, 8.0]),
        },
    },
    "prestasi": {
        "label": "Skor Prestasi",
        "satuan": "skor",
        "semesta": (0.0, 100.0),
        "mf": {
            "Rendah": ("trap", [0.0, 0.0, 30.0, 50.0]),
            "Sedang": ("tri", [30.0, 50.0, 70.0]),
            "Tinggi": ("trap", [50.0, 70.0, 100.0, 100.0]),
        },
    },
}

# Urutan input yang baku (dipakai di seluruh projek)
INPUT_KEYS = ["ipk", "penghasilan", "tanggungan", "prestasi"]

# ---------------------------------------------------------------------------
# Variabel output
# ---------------------------------------------------------------------------
OUTPUT = {
    "key": "kelayakan",
    "label": "Kelayakan Beasiswa",
    "satuan": "skor",
    "semesta": (0.0, 100.0),
    "mf": {
        "Tidak Layak": ("trap", [0.0, 0.0, 25.0, 45.0]),
        "Cukup Layak": ("tri", [25.0, 45.0, 65.0]),
        "Layak": ("tri", [45.0, 65.0, 85.0]),
        "Sangat Layak": ("trap", [65.0, 85.0, 100.0, 100.0]),
    },
}

# Langkah grid diskrit untuk defuzzifikasi centroid: z = 0, 0.1, ..., 100
# -> 1001 titik sampel.
OUTPUT_STEP = 0.1

# Interpretasi skor crisp. Batas 35/55/75 adalah titik potong MF output
# yang bersebelahan, sehingga konsisten dengan kategori ber-μ terbesar.
# (batas_bawah_inklusif, batas_atas_eksklusif, kategori)
KATEGORI_SKOR = [
    (0.0, 35.0, "Tidak Layak"),
    (35.0, 55.0, "Cukup Layak"),
    (55.0, 75.0, "Layak"),
    (75.0, 100.0001, "Sangat Layak"),
]

# ---------------------------------------------------------------------------
# Basis aturan
# Setiap aturan: id, anteseden (dict var -> kategori, digabung AND=MIN),
# konsekuen (kategori output), dan alasan singkat.
# Aturan boleh memakai sebagian anteseden (tidak harus 4 variabel).
# ---------------------------------------------------------------------------
RULES = [
    # --- Kelompok A: IPK x Penghasilan ---
    {"id": "R1", "if": {"ipk": "Rendah", "penghasilan": "Rendah"}, "then": "Cukup Layak",
     "alasan": "Sangat membutuhkan bantuan, tetapi akademiknya lemah sehingga hanya cukup layak."},
    {"id": "R2", "if": {"ipk": "Rendah", "penghasilan": "Sedang"}, "then": "Tidak Layak",
     "alasan": "Akademik lemah dan kebutuhan ekonomi tidak mendesak."},
    {"id": "R3", "if": {"ipk": "Rendah", "penghasilan": "Tinggi"}, "then": "Tidak Layak",
     "alasan": "Tidak unggul secara akademik dan keluarga mampu secara ekonomi."},
    {"id": "R4", "if": {"ipk": "Sedang", "penghasilan": "Rendah"}, "then": "Layak",
     "alasan": "IPK memenuhi syarat umum dan keluarga membutuhkan bantuan."},
    {"id": "R5", "if": {"ipk": "Sedang", "penghasilan": "Sedang"}, "then": "Cukup Layak",
     "alasan": "Akademik dan kondisi ekonomi sama-sama menengah."},
    {"id": "R6", "if": {"ipk": "Sedang", "penghasilan": "Tinggi"}, "then": "Tidak Layak",
     "alasan": "Keluarga mampu dan IPK tidak menonjol."},
    {"id": "R7", "if": {"ipk": "Tinggi", "penghasilan": "Rendah"}, "then": "Sangat Layak",
     "alasan": "Unggul secara akademik dan sangat membutuhkan bantuan."},
    {"id": "R8", "if": {"ipk": "Tinggi", "penghasilan": "Sedang"}, "then": "Layak",
     "alasan": "Unggul secara akademik dengan kebutuhan ekonomi sedang."},
    {"id": "R9", "if": {"ipk": "Tinggi", "penghasilan": "Tinggi"}, "then": "Cukup Layak",
     "alasan": "Unggul secara akademik, tetapi keluarga mampu sehingga prioritas turun."},
    # --- Kelompok B: Prestasi x Tanggungan ---
    {"id": "R10", "if": {"prestasi": "Rendah", "tanggungan": "Sedikit"}, "then": "Tidak Layak",
     "alasan": "Prestasi rendah dan beban keluarga ringan."},
    {"id": "R11", "if": {"prestasi": "Rendah", "tanggungan": "Sedang"}, "then": "Tidak Layak",
     "alasan": "Beban keluarga sedang belum menutupi prestasi yang rendah."},
    {"id": "R12", "if": {"prestasi": "Rendah", "tanggungan": "Banyak"}, "then": "Cukup Layak",
     "alasan": "Beban keluarga berat memberi pertimbangan meskipun prestasi rendah."},
    {"id": "R13", "if": {"prestasi": "Sedang", "tanggungan": "Sedikit"}, "then": "Tidak Layak",
     "alasan": "Prestasi biasa dan beban keluarga ringan."},
    {"id": "R14", "if": {"prestasi": "Sedang", "tanggungan": "Sedang"}, "then": "Cukup Layak",
     "alasan": "Prestasi dan beban keluarga sama-sama menengah."},
    {"id": "R15", "if": {"prestasi": "Sedang", "tanggungan": "Banyak"}, "then": "Layak",
     "alasan": "Beban keluarga berat dengan prestasi yang memadai."},
    {"id": "R16", "if": {"prestasi": "Tinggi", "tanggungan": "Sedikit"}, "then": "Cukup Layak",
     "alasan": "Berprestasi, tetapi beban keluarga ringan."},
    {"id": "R17", "if": {"prestasi": "Tinggi", "tanggungan": "Sedang"}, "then": "Layak",
     "alasan": "Berprestasi dengan beban keluarga sedang."},
    {"id": "R18", "if": {"prestasi": "Tinggi", "tanggungan": "Banyak"}, "then": "Sangat Layak",
     "alasan": "Berprestasi dan menanggung beban keluarga yang berat."},
    # --- Kelompok C: aturan silang ---
    {"id": "R19", "if": {"ipk": "Rendah", "prestasi": "Rendah"}, "then": "Tidak Layak",
     "alasan": "Gagal memenuhi standar akademik minimum dari dua sisi (IPK dan prestasi)."},
    {"id": "R20", "if": {"penghasilan": "Tinggi", "tanggungan": "Sedikit"}, "then": "Tidak Layak",
     "alasan": "Penghasilan tinggi dengan beban ringan berarti tidak membutuhkan bantuan."},
    {"id": "R21", "if": {"penghasilan": "Rendah", "tanggungan": "Banyak"}, "then": "Layak",
     "alasan": "Kebutuhan ekonomi sangat mendesak (miskin dengan banyak tanggungan)."},
    {"id": "R22", "if": {"ipk": "Tinggi", "prestasi": "Tinggi"}, "then": "Layak",
     "alasan": "Merit akademik kuat dari dua sisi (IPK dan prestasi)."},
]

# ---------------------------------------------------------------------------
# Nilai acuan untuk analisis & contoh
# ---------------------------------------------------------------------------
# Nilai dasar analisis sensitivitas (tiga input lain ditahan di nilai ini)
BASE_VALUES = {"ipk": 3.2, "penghasilan": 4.5, "tanggungan": 4.0, "prestasi": 60.0}

# Kasus perhitungan lengkap: semua input di daerah tumpang tindih
DETAIL_CASE = {"ipk": 3.3, "penghasilan": 3.5, "tanggungan": 4.0, "prestasi": 62.0}

# Resolusi grid uji cakupan (titik per variabel)
COVERAGE_POINTS = 30
