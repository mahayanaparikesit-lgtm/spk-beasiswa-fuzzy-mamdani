"""
Susun laporan/laporan.md dari hasil di folder hasil/, lalu ekspor ke laporan/laporan.docx.
Jalankan setelah grafik_mf, uji_cakupan, run_all, detail_satu, sensitivitas, validasi.
Catatan: komentar naratif ditulis untuk parameter versi ini; angka diambil otomatis dari hasil.
"""
import json
import os
import re

import _path  # noqa: F401
import pandas as pd

import config
from fuzzy.engine import inferensi
from md_ke_docx import konversi

H = _path.HASIL
LAP = os.path.join(_path.ROOT, "laporan")
os.makedirs(LAP, exist_ok=True)
IMG = "../hasil/"


def tabel(df, kolom=None, judul=None):
    df = df if kolom is None else df[kolom]
    if judul:
        df = df.rename(columns=judul)
    baris = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    for _, r in df.iterrows():
        baris.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in r.values) + " |")
    return "\n".join(baris)


def fmt(v):
    return f"{v:g}"


def persamaan(nama, spec):
    """LaTeX fungsi sepotong-sepotong untuk satu kategori."""
    bentuk, p = spec
    sub = nama.replace(" ", r"\;")
    if bentuk == "tri":
        a, b, c = p
        rows = [f"0, & x \\leq {fmt(a)} \\;\\mathrm{{atau}}\\; x \\geq {fmt(c)}",
                f"\\frac{{x-{fmt(a)}}}{{{fmt(b)}-{fmt(a)}}}, & {fmt(a)} < x \\leq {fmt(b)}",
                f"\\frac{{{fmt(c)}-x}}{{{fmt(c)}-{fmt(b)}}}, & {fmt(b)} < x < {fmt(c)}"]
    else:
        a, b, c, d = p
        if a == b:  # bahu kiri
            rows = [f"1, & x \\leq {fmt(c)}",
                    f"\\frac{{{fmt(d)}-x}}{{{fmt(d)}-{fmt(c)}}}, & {fmt(c)} < x < {fmt(d)}",
                    f"0, & x \\geq {fmt(d)}"]
        elif c == d:  # bahu kanan
            rows = [f"0, & x \\leq {fmt(a)}",
                    f"\\frac{{x-{fmt(a)}}}{{{fmt(b)}-{fmt(a)}}}, & {fmt(a)} < x < {fmt(b)}",
                    f"1, & x \\geq {fmt(b)}"]
        else:
            rows = [f"0, & x \\leq {fmt(a)} \\;\\mathrm{{atau}}\\; x \\geq {fmt(d)}",
                    f"\\frac{{x-{fmt(a)}}}{{{fmt(b)}-{fmt(a)}}}, & {fmt(a)} < x < {fmt(b)}",
                    f"1, & {fmt(b)} \\leq x \\leq {fmt(c)}",
                    f"\\frac{{{fmt(d)}-x}}{{{fmt(d)}-{fmt(c)}}}, & {fmt(c)} < x < {fmt(d)}"]
    return f"$$\\mu_{{\\mathrm{{{sub}}}}}(x) = \\begin{{cases}} " + " \\\\ ".join(rows) + " \\end{cases}$$"


def bagian_mf(var, info, alasan, alasan_param):
    L = [f"#### {info['label']} (semesta {fmt(info['semesta'][0])}–{fmt(info['semesta'][1])}"
         + (f" {info['satuan']})" if info["satuan"] else ")"), ""]
    L.append("| Kategori | Bentuk | Parameter |\n|---|---|---|")
    for kat, (b, p) in info["mf"].items():
        nama = {"tri": "Segitiga", "trap": "Trapesium"}[b]
        if b == "trap" and p[0] == p[1]:
            nama = "Trapesium (bahu kiri)"
        elif b == "trap" and p[2] == p[3]:
            nama = "Trapesium (bahu kanan)"
        L.append(f"| {kat} | {nama} | ({', '.join(fmt(v) for v in p)}) |")
    L.append("")
    for kat, spec in info["mf"].items():
        L.append(persamaan(kat, spec))
        L.append("")
    L.append(f"![Gambar: fungsi keanggotaan {info['label']}]({IMG}mf_{var}.png)")
    L.append("")
    L.append(f"**Alasan parameter.** {alasan_param}")
    L.append("")
    return "\n".join(L)


def main():
    uji = pd.read_csv(os.path.join(H, "hasil_uji.csv"))
    celah = pd.read_csv(os.path.join(H, "uji_celah_mf.csv"))
    cak = json.load(open(os.path.join(H, "uji_cakupan.json"), encoding="utf-8"))
    aturan = pd.read_csv(os.path.join(H, "basis_aturan.csv"))
    val = pd.read_csv(os.path.join(H, "validasi.csv"))
    grid = pd.read_csv(os.path.join(H, "efek_grid.csv"))
    sens = pd.read_csv(os.path.join(H, "sensitivitas_ringkasan.csv"))
    detail = open(os.path.join(H, "detail_perhitungan.md"), encoding="utf-8").read()
    detail = detail.replace("](detail_", f"]({IMG}detail_").replace("### Data mahasiswa", "### 5.0 Data mahasiswa")
    detail = re.sub(r"### Langkah (\d) — ", r"### 5.\1 Langkah \1 — ", detail)
    val_md = open(os.path.join(H, "validasi_manual.md"), encoding="utf-8").read()
    val_md = val_md.replace("## Validasi manual vs program\n", "").replace("### ", "#### ")

    S = {r["id"]: r for _, r in uji.iterrows()}

    def sk(i):
        return f"{S[i]['skor']:.2f} ({S[i]['kategori_kelayakan']})".replace(".", ",")

    terbaik = inferensi({"ipk": 4, "penghasilan": 0, "tanggungan": 8, "prestasi": 100})["skor"]
    terburuk = inferensi({"ipk": 0, "penghasilan": 15, "tanggungan": 0, "prestasi": 0})["skor"]
    sens_d = {r["variabel"]: r for _, r in sens.iterrows()}
    base = inferensi(config.BASE_VALUES)["skor"]
    dc = config.DETAIL_CASE
    n_z = len(inferensi(dc)["z"])

    L = []
    A = L.append
    A("# Pengembangan Sistem Pendukung Keputusan Kelayakan Penerima Beasiswa Menggunakan Logika Fuzzy Metode Mamdani")
    A("")
    A("Laporan Tugas Projek Mata Kuliah Logika Fuzzy")
    A("")
    A("---")
    A("")

    # ---------------------------------------------------------------- BAB 1
    A("## 1. Identifikasi Masalah")
    A("")
    A("Seleksi penerima beasiswa umumnya menilai dua hal sekaligus: **merit akademik** (IPK, prestasi) "
      "dan **kebutuhan ekonomi** (penghasilan orang tua, jumlah tanggungan). Penilaian dengan ambang tegas "
      "(misalnya \"IPK ≥ 3,00 lolos, < 3,00 gugur\") menimbulkan ketidakadilan di sekitar batas: mahasiswa "
      "dengan IPK 2,99 diperlakukan sama dengan IPK 2,00. Selain itu kriteria sering saling bertentangan, "
      "misalnya IPK tinggi tetapi keluarga mampu. Logika fuzzy cocok untuk masalah ini karena setiap kriteria "
      "dinilai secara bertingkat (derajat keanggotaan 0–1) dan pengetahuan panitia dapat dituliskan sebagai "
      "aturan IF–THEN yang mudah dipahami.")
    A("")
    A("**Tujuan sistem:** memberikan skor kelayakan 0–100 beserta kategorinya untuk setiap pendaftar, "
      "secara konsisten dan dapat ditelusuri (setiap skor dapat dijelaskan dari aturan yang aktif).")
    A("")
    A("**Pengguna:** panitia/tim seleksi beasiswa di tingkat program studi, fakultas, atau bagian kemahasiswaan. "
      "Sistem dipakai untuk menyaring dan mengurutkan pendaftar sebelum verifikasi berkas dan wawancara.")
    A("")
    A("**Variabel sistem:**")
    A("")
    A("| Jenis | Variabel | Semesta | Kategori linguistik |\n|---|---|---|---|")
    for k in config.INPUT_KEYS:
        i = config.INPUTS[k]
        A(f"| Input | {i['label']} | {fmt(i['semesta'][0])}–{fmt(i['semesta'][1])} {i['satuan']} | "
          f"{', '.join(i['mf'])} |")
    A(f"| Output | {config.OUTPUT['label']} | 0–100 | {', '.join(config.OUTPUT['mf'])} |")
    A("")
    A("**Arti skor kelayakan:**")
    A("")
    A("| Rentang skor | Kategori | Interpretasi untuk panitia |\n|---|---|---|")
    interp = {
        "Tidak Layak": "Belum direkomendasikan; kebutuhan dan/atau merit rendah.",
        "Cukup Layak": "Dipertimbangkan bila kuota masih tersedia; perlu verifikasi tambahan.",
        "Layak": "Direkomendasikan untuk lanjut ke tahap verifikasi/wawancara.",
        "Sangat Layak": "Prioritas utama penerima beasiswa.",
    }
    for lo, hi, nama in config.KATEGORI_SKOR:
        hi_t = "100" if hi > 100 else f"< {fmt(hi)}"
        A(f"| {fmt(lo)} – {hi_t} | {nama} | {interp[nama]} |")
    A("")
    A("Batas 35, 55, dan 75 adalah titik potong fungsi keanggotaan output yang bersebelahan, sehingga kategori "
      "yang ditampilkan selalu sama dengan kategori yang memiliki derajat keanggotaan terbesar pada skor tersebut.")
    A("")
    A("> **Penegasan:** skor kelayakan adalah *rekomendasi pendukung keputusan*, bukan keputusan final. "
      "Keputusan tetap berada pada panitia setelah verifikasi dokumen, wawancara, dan pertimbangan kuota.")
    A("")

    # ---------------------------------------------------------------- BAB 2
    A("## 2. Fungsi Keanggotaan")
    A("")
    A("### 2.1 Pemilihan bentuk fungsi")
    A("")
    A("- **Segitiga** dipakai untuk kategori tengah yang memiliki satu nilai paling khas (misalnya IPK 3,00 "
      "sebagai syarat umum beasiswa; 3 tanggungan sebagai keluarga tipikal).")
    A("- **Trapesium** dipakai bila ada rentang nilai yang sama-sama dianggap penuh anggota (misalnya "
      "penghasilan Sedang 4–6 juta).")
    A("- **Bahu kiri/kanan (trapesium)** dipakai untuk kategori di ujung semesta agar nilai ekstrem "
      "(IPK 4,00 atau penghasilan 15 juta) tetap bernilai μ = 1, bukan turun lagi.")
    A("- Fungsi linear dipilih karena mudah dihitung manual, mudah dijelaskan kepada panitia, dan cukup "
      "untuk data yang tidak memerlukan kehalusan turunan (seperti pada MF Gauss).")
    A("- Kategori yang bersebelahan dibuat **saling tumpang tindih** dan berpotongan di μ = 0,5 sehingga "
      "tidak ada celah dan transisi antar-kategori berlangsung bertahap.")
    A("")
    A("Notasi parameter: segitiga (a, b, c) dengan puncak di b; trapesium (a, b, c, d) dengan μ = 1 pada [b, c].")
    A("")
    A("### 2.2 Parameter dan persamaan")
    A("")
    alasan = {
        "ipk": "IPK < 2,50 umumnya di bawah syarat minimum beasiswa sehingga penuh \"Rendah\". "
               "3,00 adalah syarat umum beasiswa sehingga menjadi puncak \"Sedang\". IPK ≥ 3,50 setara "
               "predikat dengan pujian sehingga penuh \"Tinggi\".",
        "penghasilan": "≤ Rp2 juta/bulan setara atau di bawah upah minimum di banyak daerah (penuh \"Rendah\"). "
                       "Rp4–6 juta dianggap kelas menengah (penuh \"Sedang\"). ≥ Rp9 juta dianggap mampu "
                       "(penuh \"Tinggi\"). Sisi Sedang→Tinggi dibuat lebih landai (6–9 juta) karena perbedaan "
                       "kemampuan ekonomi di rentang ini lebih kabur.",
        "tanggungan": "0–1 tanggungan berarti beban ringan, 3 tanggungan dianggap keluarga tipikal, dan ≥ 5 "
                      "tanggungan dianggap beban berat. Variabel ini diperlakukan kontinu agar data rata-rata "
                      "(misalnya 3,5) tetap dapat diproses.",
        "prestasi": "Skor prestasi (lomba, organisasi, karya) 0–100. Skor ≤ 30 penuh \"Rendah\", 50 khas "
                    "\"Sedang\", ≥ 70 penuh \"Tinggi\". Lebar transisi 20 poin dipakai seragam.",
        "kelayakan": "Empat kategori dengan lebar transisi 20 poin yang seragam. Titik potong 35/55/75 "
                     "menjadi batas interpretasi skor. Bahu \"Tidak Layak\" (0–25) dan \"Sangat Layak\" (85–100) "
                     "menampung skor ekstrem.",
    }
    for k in config.INPUT_KEYS:
        A(bagian_mf(k, config.INPUTS[k], None, alasan[k]))
    A(bagian_mf("kelayakan", config.OUTPUT, None, alasan["kelayakan"]))
    A("### 2.3 Bukti tidak ada celah")
    A("")
    A("Fungsi `cek_celah_mf()` (file `fuzzy/coverage.py`) menyisir setiap semesta dengan 10.001 titik dan "
      "menghitung max μ dari semua kategori di setiap titik. Sistem dinyatakan tanpa celah bila nilai minimum "
      "dari max μ tersebut > 0.")
    A("")
    A(tabel(celah, judul={"variabel": "Variabel", "tanpa_celah": "Tanpa celah",
                          "min_dari_max_mu": "min(max μ)", "titik_terlemah": "Titik terlemah"}))
    A("")
    A("Di setiap variabel, titik terlemah adalah titik potong dua kategori dengan μ = 0,5, sehingga "
      "setiap nilai input selalu termasuk minimal satu kategori dengan derajat ≥ 0,5.")
    A("")

    # ---------------------------------------------------------------- BAB 3
    A("## 3. Basis Aturan")
    A("")
    A(f"Basis aturan terdiri atas **{len(config.RULES)} aturan** yang disusun dalam tiga kelompok. "
      "Seluruh anteseden digabung dengan operator AND (MIN). Aturan disimpan sebagai data (list of dict) "
      "di `config.py`, bukan sebagai if-else bersarang.")
    A("")
    A("- **Kelompok A (R1–R9): IPK × Penghasilan.** Menggabungkan merit akademik dengan kebutuhan ekonomi.")
    A("- **Kelompok B (R10–R18): Prestasi × Tanggungan.** Menggabungkan merit non-akademik dengan beban keluarga.")
    A("- **Kelompok C (R19–R22): aturan silang.** Menangkap interaksi penting antar-kelompok.")
    A("")
    A("Konsekuen kelompok A dan B disusun secara sistematis: setiap kategori diberi skor ordinal "
      "(Rendah/Sedikit = 0, Sedang = 1, Tinggi/Banyak = 2; untuk penghasilan dibalik karena makin rendah "
      "makin membutuhkan). Jumlah skor 0–1 → Tidak Layak, 2 → Cukup Layak, 3 → Layak, 4 → Sangat Layak. "
      "Dengan cara ini **tidak ada aturan yang arahnya bertentangan**: menaikkan input yang \"baik\" "
      "tidak pernah memindahkan konsekuen ke kategori yang lebih rendah.")
    A("")
    A("Aturan sengaja memakai sebagian anteseden (2 variabel). Alasannya, aturan lengkap 4 variabel "
      "membutuhkan 3⁴ = 81 aturan agar seluruh kombinasi tercakup, sedangkan 15–22 aturan 4-variabel "
      "pasti meninggalkan banyak kombinasi tanpa aturan aktif.")
    A("")
    A(tabel(aturan, judul={"id": "ID", "ipk": "IPK", "penghasilan": "Penghasilan", "tanggungan": "Tanggungan",
                           "prestasi": "Prestasi", "kelayakan": "→ Kelayakan", "alasan": "Alasan"}))
    A("")
    A("Tanda \"-\" berarti variabel tersebut tidak dipakai pada anteseden aturan itu.")
    A("")
    A("### 3.1 Uji cakupan aturan")
    A("")
    A("Skrip `scripts/uji_cakupan.py` menyisir grid seluruh kombinasi empat input pada tiga resolusi "
      "dan menghitung α semua aturan di setiap titik grid (tervektorisasi dengan NumPy). Sebuah kombinasi "
      "dikatakan tercakup bila minimal satu aturan memiliki α > 0.")
    A("")
    rows = []
    for g in cak["grid"]:
        rows.append({"Titik/variabel": g["titik_per_variabel"], "Total kombinasi": f"{g['total_kombinasi']:,}",
                     "Tercakup": f"{g['tercakup']:,}", "Persen": f"{g['persen']:.2f}%",
                     "Aturan aktif min–maks (rata-rata)":
                         f"{g['aturan_aktif_min']}–{g['aturan_aktif_maks']} ({g['aturan_aktif_rata2']:.2f})",
                     "min(α maks)": f"{g['min_alpha_maks']:.3f}"})
    A(tabel(pd.DataFrame(rows)))
    A("")
    kk = cak["kombinasi_kategori"]
    A(f"Selain grid numerik, dicek juga secara logis bahwa {kk['total'] - len(kk['tidak_tercakup'])} dari "
      f"{kk['total']} kombinasi kategori (3⁴) memiliki minimal satu aturan yang cocok. "
      "**Hasil: cakupan 100%, tidak ada kombinasi yang perlu diperbaiki.** Secara teoretis hal ini dijamin oleh "
      "kelompok A: untuk sembarang nilai input selalu ada satu kategori IPK dan satu kategori penghasilan "
      "dengan μ ≥ 0,5, dan kelompok A memuat seluruh 3 × 3 pasangan tersebut. Karena itu α maks di "
      "setiap titik selalu ≥ 0,5, dan setiap titik mengaktifkan minimal 2 aturan.")
    A("")

    # ---------------------------------------------------------------- BAB 4
    A("## 4. Implementasi Metode Mamdani")
    A("")
    A("Mesin inferensi ditulis sendiri dengan Python + NumPy agar setiap tahap dapat diperiksa. "
      "`scikit-fuzzy` hanya dipakai sebagai pembanding pada tahap validasi.")
    A("")
    A("| Komponen | File | Keterangan |\n|---|---|---|")
    A("| Parameter MF, grid output, aturan | `config.py` | Satu-satunya tempat mengubah parameter |")
    A("| Fungsi segitiga & trapesium | `fuzzy/membership.py` | `segitiga()`, `trapesium()`, `hitung_mf()` |")
    A("| Fuzzifikasi → centroid | `fuzzy/engine.py` | `fuzzifikasi()`, `alpha_predikat()`, `implikasi()`, `agregasi()`, `centroid()` |")
    A("| Cek celah & cakupan | `fuzzy/coverage.py` | `cek_celah_mf()`, `cek_cakupan_aturan()` |")
    A("| Antarmuka web | `app.py` | Streamlit |")
    A("")
    A("Tahapan inferensi untuk satu mahasiswa:")
    A("")
    A("1. **Fuzzifikasi**: setiap nilai crisp diubah menjadi derajat keanggotaan μ di setiap kategori.")
    A("2. **α-predikat**: untuk setiap aturan, α = MIN(μ anteseden).")
    A("3. **Implikasi MIN**: fungsi output konsekuen dipotong setinggi α, yaitu μ_i(z) = min(α_i, μ_konsekuen(z)).")
    A("4. **Agregasi MAX**: μ_agr(z) = max_i μ_i(z) atas semua aturan.")
    A("5. **Defuzzifikasi centroid diskrit** pada grid output.")
    A("")
    A(f"**Grid output:** z = 0; {fmt(config.OUTPUT_STEP)}; {fmt(2 * config.OUTPUT_STEP)}; …; 100, yaitu langkah "
      f"Δz = {fmt(config.OUTPUT_STEP)} dengan **{n_z} titik sampel**.")
    A("")
    A("$$z^* = \\frac{\\sum_{i=1}^{N} \\mu_{agr}(z_i)\\, z_i}{\\sum_{i=1}^{N} \\mu_{agr}(z_i)}$$")
    A("")
    A("Potongan inti kode (`fuzzy/engine.py`):")
    A("")
    A("```python")
    A("def alpha_predikat(mu, rules):")
    A("    for r in rules:                                   # AND = MIN")
    A("        komponen = {var: mu[var][kat] for var, kat in r['if'].items()}")
    A("        alpha = min(komponen.values())")
    A("")
    A("def implikasi(alphas, z):                             # implikasi MIN (clipping)")
    A("    return [np.minimum(a['alpha'], mf_out[a['then']]) for a in alphas]")
    A("")
    A("def agregasi(terpotong, z):                           # agregasi MAX")
    A("    return np.max(np.vstack(terpotong), axis=0)")
    A("")
    A("def centroid(z, mu):                                  # Σμ·z / Σμ")
    A("    return np.sum(mu * z) / np.sum(mu)")
    A("```")
    A("")
    A("Nilai input di luar semesta dipotong (clip) ke batas semesta, misalnya IPK 4,2 diperlakukan sebagai 4,0.")
    A("")

    # ---------------------------------------------------------------- BAB 5
    A("## 5. Contoh Perhitungan Lengkap")
    A("")
    A(f"Mahasiswa yang dipilih adalah **M09 (Indah)** dengan IPK {fmt(dc['ipk'])}, penghasilan "
      f"Rp{fmt(dc['penghasilan'])} juta, tanggungan {fmt(dc['tanggungan'])} orang, dan prestasi "
      f"{fmt(dc['prestasi'])}. Keempat nilainya berada di daerah tumpang tindih dua kategori, sehingga "
      "banyak aturan aktif dan setiap tahap Mamdani terlihat jelas.")
    A("")
    A(f"![Gambar: posisi nilai input pada fungsi keanggotaan]({IMG}detail_fuzzifikasi.png)")
    A("")
    A(detail)
    A("")
    A("Interpretasi: aturan dengan α terbesar mengarah ke **Layak** (R8, R22; α = 0,6). Kontribusi "
      "**Sangat Layak** (α = 0,5) menarik centroid ke kanan, sedangkan **Cukup Layak** (α = 0,4) menariknya "
      "ke kiri. Keseimbangan ketiganya menghasilkan skor sedikit di atas puncak Layak (65).")
    A("")

    # ---------------------------------------------------------------- BAB 6
    A("## 6. Pengujian")
    A("")
    A(f"Data uji berisi **{len(uji)} mahasiswa simulasi** (`data/data_mahasiswa.csv`) yang mencakup kondisi "
      "ekstrem, nilai tepat di titik parameter, daerah tumpang tindih, kriteria bertentangan, dan kasus normal. "
      "Hasil lengkap (input, μ setiap kategori, daftar aturan aktif beserta α, skor, dan kategori) tersimpan di "
      "`hasil/hasil_uji.csv`. Ringkasannya:")
    A("")
    ring = uji[["id", "nama_samaran", "ipk", "penghasilan", "tanggungan", "prestasi", "jumlah_aturan_aktif",
                "skor", "kategori_kelayakan", "kategori_uji"]].copy()
    ring["skor"] = ring["skor"].map(lambda v: f"{v:.2f}")
    A(tabel(ring, judul={"id": "ID", "nama_samaran": "Nama", "ipk": "IPK", "penghasilan": "Penghasilan (jt)",
                         "tanggungan": "Tanggungan", "prestasi": "Prestasi", "jumlah_aturan_aktif": "Aturan aktif",
                         "skor": "Skor", "kategori_kelayakan": "Kategori", "kategori_uji": "Jenis uji"}))
    A("")
    A("Contoh isi kolom aturan aktif (M09): `" + S["M09"]["aturan_aktif"] + "`.")
    A("")
    dist = uji["kategori_kelayakan"].value_counts()
    A("Distribusi kategori: " + ", ".join(f"{k} {int(dist.get(k, 0))}" for _, _, k in config.KATEGORI_SKOR) + ".")
    A("")
    A("### 6.1 Komentar kewajaran hasil")
    A("")
    A("**Kasus ekstrem.**")
    A("")
    A(f"- M01 (semua sangat baik) mendapat {sk('M01')} dan M02 (semua sangat buruk) mendapat {sk('M02')}. "
      "Urutannya benar. Kedua skor ini adalah batas atas dan bawah yang dapat dicapai sistem. Skor tidak "
      "mencapai 100 atau 0 karena **efek kompresi centroid**: titik berat daerah \"Sangat Layak\" sendiri "
      "berada di sekitar 87, dan pada kasus terbaik aturan R21/R22 (→ Layak) juga aktif penuh sehingga centroid "
      "bergeser ke sekitar 77.")
    A(f"- M03 (semua nilai maksimum: IPK 4, prestasi 100, tanggungan 8, tetapi penghasilan 15 juta) mendapat "
      f"{sk('M03')}. Hasil ini wajar karena merit dan beban keluarga sangat tinggi, tetapi keluarga mampu "
      "(R9 → Cukup Layak) sehingga tidak mencapai Sangat Layak.")
    A(f"- M04 (semua nol) mendapat {sk('M04')}. Keluarga sangat miskin (R1 → Cukup Layak), tetapi IPK dan "
      "prestasi nol (R19 → Tidak Layak) serta tanggungan sedikit (R10 → Tidak Layak). Hasilnya wajar.")
    A("")
    A("**Kasus batas (tepat di titik parameter).**")
    A("")
    A(f"- M05 (IPK 3,0; penghasilan 4; tanggungan 3; prestasi 50, semuanya tepat di puncak \"Sedang\") "
      f"mendapat {sk('M05')}. Hanya R5 dan R14 (→ Cukup Layak, α = 1) yang aktif, sehingga centroid tepat "
      "berada di puncak segitiga Cukup Layak (45). Ini menjadi bukti engine bekerja simetris dan benar.")
    A(f"- M06 (3,5; 2; 5; 70, tepat di awal μ = 1 kategori terbaik) mendapat {sk('M06')}, sama persis dengan M01. "
      "Kesamaan ini benar karena pada titik tersebut μ kategori terbaik sudah 1.")
    A(f"- M07 (2,5; 9; 1; 30) mendapat {sk('M07')}, sama dengan M02, dengan alasan yang sama.")
    A(f"- M08 (IPK 3,5 penuh Tinggi, penghasilan 6 penuh Sedang, tanggungan 1, prestasi 30) mendapat {sk('M08')}. "
      "R8 (→ Layak) dan R10 (→ Tidak Layak) sama-sama aktif dengan α = 1, sehingga centroid jatuh di tengah, "
      "tepat di sekitar batas Tidak Layak/Cukup Layak. Panitia sebaiknya meninjau kasus seperti ini secara manual.")
    A("")
    A("**Kasus tumpang tindih.**")
    A("")
    A(f"- M09 {sk('M09')}, M10 {sk('M10')}, dan M11 {sk('M11')} mengaktifkan 9–10 aturan. Skornya berada di "
      "antara kategori yang aktif, dan perubahan kecil input hanya menggeser skor secara halus (tidak melompat). "
      "Inilah keunggulan fuzzy dibanding ambang tegas.")
    A("")
    A("**Kasus bertentangan.**")
    A("")
    A(f"- M12 (IPK 3,9 dan prestasi 85, tetapi penghasilan 12 juta dan tanggungan 2) mendapat {sk('M12')}. "
      "Merit tinggi diimbangi oleh keluarga yang mampu. Hasil ini sesuai tujuan beasiswa berbasis kebutuhan.")
    A(f"- M13 (IPK 2,1 dan prestasi 25, tetapi sangat miskin dengan 7 tanggungan) mendapat {sk('M13')}. "
      "Empat aturan aktif penuh dengan konsekuen berbeda (TL, CL, CL, L), sehingga hasilnya berada di tengah. "
      "Sistem tidak menolak mentah-mentah, tetapi juga tidak memprioritaskan.")
    A(f"- M14 (prestasi 90, tetapi IPK 2,3) mendapat {sk('M14')}. M15 (IPK 3,8 dan miskin, tetapi prestasi 15) "
      f"mendapat {sk('M15')}. M15 lebih tinggi karena IPK berpasangan dengan penghasilan rendah di R7 "
      "(→ Sangat Layak). Ini menunjukkan bahwa dalam basis aturan ini **kombinasi IPK–penghasilan berbobot lebih "
      "besar daripada prestasi**, sesuai pola beasiswa umum yang mensyaratkan IPK.")
    A(f"- M16 (tanggungan 7, tetapi penghasilan 11 juta) mendapat {sk('M16')}. Penghasilan tinggi lebih "
      "dominan daripada jumlah tanggungan. Hasilnya wajar.")
    A("")
    A("**Kasus normal.** Skor M17–M22 tersebar dari Tidak Layak (M22, IPK 2,6 dengan penghasilan 8 juta) "
      "sampai Sangat Layak (M21, IPK 3,75, penghasilan 2,5 juta, tanggungan 6, prestasi 80). Urutannya "
      "sesuai intuisi.")
    A("")
    A(f"Secara keseluruhan, tidak ditemukan hasil yang janggal. Rentang skor efektif sistem adalah "
      f"{terburuk:.2f}–{terbaik:.2f}, bukan 0–100. Hal ini dibahas lebih lanjut di Bab 8.")
    A("")

    # ---------------------------------------------------------------- BAB 7
    A("## 7. Validasi dan Analisis Sensitivitas")
    A("")
    A("### 7.1 Validasi perhitungan manual vs program")
    A("")
    A("Perhitungan manual ditulis ulang secara terpisah di `scripts/validasi.py` (fungsi `manual()`). "
      "Perhitungan ini memakai Python murni tanpa NumPy dan tanpa memanggil engine maupun `config.py`. "
      "Setiap rumus MF diketik langsung beserta angka parameternya (misalnya `(3.0 - x) / (3.0 - 2.5)`), "
      "setiap aturan ditulis satu per satu, lalu agregasi dan centroid dihitung dengan perulangan biasa "
      "pada grid yang sama (Δz = 0,1).")
    A("")
    A(val_md)
    A("")
    v = val.copy()
    v["selisih_manual_program"] = v["selisih_manual_program"].map(lambda x: f"{x:.1e}")
    for c in ["skor_manual", "skor_program", "skor_skfuzzy"]:
        v[c] = v[c].map(lambda x: f"{x:.4f}")
    v["selisih_program_skfuzzy"] = v["selisih_program_skfuzzy"].map(lambda x: f"{x:.4f}")
    A(tabel(v, ["kasus", "skor_manual", "skor_program", "selisih_manual_program", "skor_skfuzzy",
                "selisih_program_skfuzzy"],
            {"kasus": "Kasus", "skor_manual": "Manual", "skor_program": "Program",
             "selisih_manual_program": "|Manual − Program|", "skor_skfuzzy": "scikit-fuzzy",
             "selisih_program_skfuzzy": "|Program − skfuzzy|"}))
    A("")
    A("**Hasil:** perhitungan manual dan program identik. Selisihnya hanya sekitar 10⁻¹³, yaitu sisa "
      "pembulatan bilangan floating point.")
    A("")
    A("**Pembanding scikit-fuzzy:** sistem yang sama (MF, aturan, AND = MIN, implikasi MIN, agregasi MAX, "
      "centroid) dibangun dengan `skfuzzy.control`. Selisihnya sekitar 0,02 poin. Penyebabnya adalah perbedaan "
      "cara menghitung centroid: scikit-fuzzy menghitung centroid **kontinu** (integral luas per segmen "
      "linear), sedangkan engine ini memakai **jumlahan diskrit**. Buktinya, bila grid engine diperhalus "
      "menjadi Δz = 0,001, skornya praktis sama dengan scikit-fuzzy (lihat tabel 7.2). Pada M17 selisihnya 0 "
      "karena daerah agregasinya simetris.")
    A("")
    A("### 7.2 Efek resolusi grid centroid")
    A("")
    A(tabel(grid))
    A("")
    A("Makin kasar grid, makin besar galat. Dengan Δz = 0,1 galatnya < 0,03 poin, jauh lebih kecil daripada "
      "lebar kategori (20 poin), sehingga Δz = 0,1 sudah memadai. Dengan Δz = 5 atau 10 galatnya bisa mencapai "
      "1–3 poin dan dapat memindahkan kategori pada kasus yang dekat batas.")
    A("")
    A("### 7.3 Analisis sensitivitas")
    A("")
    A(f"Setiap input diubah dari minimum ke maksimum semesta dalam 401 langkah, sementara tiga input lain "
      f"ditahan pada nilai dasar IPK {fmt(config.BASE_VALUES['ipk'])}, penghasilan "
      f"{fmt(config.BASE_VALUES['penghasilan'])} juta, tanggungan {fmt(config.BASE_VALUES['tanggungan'])}, "
      f"dan prestasi {fmt(config.BASE_VALUES['prestasi'])} (skor dasar {base:.2f}). "
      "Data lengkap ada di `hasil/sensitivitas.csv`.")
    A("")
    A(f"![Gambar: sensitivitas keempat input]({IMG}sensitivitas_semua.png)")
    A("")
    st = sens.copy()
    st["monoton_sesuai_arah"] = st["monoton_sesuai_arah"].map({True: "Ya", False: "Tidak"})
    A(tabel(st, ["variabel", "skor_di_min", "skor_di_maks", "rentang_skor", "arah_diharapkan",
                 "monoton_sesuai_arah", "titik_paling_tajam", "kemiringan_maks_per_satuan", "plateau"],
            {"variabel": "Variabel", "skor_di_min": "Skor di min", "skor_di_maks": "Skor di maks",
             "rentang_skor": "Rentang", "arah_diharapkan": "Arah diharapkan", "monoton_sesuai_arah": "Monoton",
             "titik_paling_tajam": "Titik paling tajam", "kemiringan_maks_per_satuan": "Kemiringan maks/satuan",
             "plateau": "Plateau (skor konstan)"}))
    A("")
    A("**Pola umum.** Keempat kurva **monoton** sesuai arah yang diharapkan: IPK, tanggungan, dan prestasi "
      "naik, sedangkan penghasilan turun. Tidak ada lompatan diskontinu; perubahan terbesar per langkah "
      "< 0,7 poin. Kurva berbentuk *tangga landai*: datar (plateau) di daerah μ = 1 sebuah kategori dan "
      "berubah hanya di daerah transisi tempat μ berubah. Dua mekanisme menjelaskan plateau:")
    A("")
    A("1. **Di dalam daerah datar MF** (μ = 1 atau 0), derajat keanggotaan tidak berubah, sehingga α semua "
      "aturan dan skor juga tidak berubah. Contohnya IPK 0–2,5 dan prestasi 0–30.")
    A("2. **Saturasi MIN/MAX**: walaupun μ suatu input masih berubah, α aturan dapat tertahan oleh μ input "
      "lain (operator MIN), atau potongan suatu kategori sudah lebih rendah daripada aturan lain berkonsekuen "
      "sama (operator MAX). Pada kondisi ini perubahan input tidak memengaruhi daerah agregasi.")
    A("")
    p = sens_d
    A(f"**IPK** (skor {p['ipk']['skor_di_min']:.2f} → {p['ipk']['skor_di_maks']:.2f}, rentang "
      f"{p['ipk']['rentang_skor']:.1f}). Kurva datar pada 0–2,5 karena IPK penuh \"Rendah\". Kenaikan paling "
      f"tajam terjadi di sekitar IPK {p['ipk']['titik_paling_tajam']:.2f}, ketika \"Rendah\" hilang dan "
      "\"Sedang\" mencapai puncak, sehingga potongan Tidak Layak (R2: IPK Rendah ∧ penghasilan Sedang) turun "
      "dari 1 ke 0 dalam selang 0,5 poin IPK. Ini adalah kemiringan tertinggi di antara semua variabel "
      f"(≈ {p['ipk']['kemiringan_maks_per_satuan']:.0f} poin skor per 1 poin IPK), karena semesta IPK sempit "
      "(0–4) dan transisi MF-nya hanya 0,5. Di atas 3,25 kurva hampir datar. Penyebabnya, kategori yang "
      "bertambah (Layak, berpuncak di 65) berpusat dekat centroid saat itu (≈ 65), sehingga menambah massa di "
      "sekitar centroid hampir tidak menggesernya.")
    A("")
    A(f"**Penghasilan** (skor {p['penghasilan']['skor_di_min']:.2f} → {p['penghasilan']['skor_di_maks']:.2f}). "
      "Pengaruhnya kecil pada 0–6 juta (hanya turun sekitar 1 poin di sekitar 3–3,5 juta) karena dengan IPK "
      "dasar 3,2 (Sedang 0,6; Tinggi 0,4), aturan R4/R7 yang memakai penghasilan Rendah tertahan oleh μ IPK "
      "(saturasi MIN). Penurunan tajam terjadi pada 6–7,8 juta, ketika \"Tinggi\" mulai naik dan R6 "
      "(IPK Sedang ∧ penghasilan Tinggi → Tidak Layak) aktif. Kurva mendatar mulai **7,8 juta, bukan 9 juta**. "
      "Pada 7,8 juta, μ_Tinggi = 0,6 sudah sama dengan μ IPK Sedang (0,6), sehingga α R6 = MIN(0,6; μ_Tinggi) "
      "tidak bisa naik lagi.")
    A("")
    A(f"**Tanggungan** (skor {p['tanggungan']['skor_di_min']:.2f} → {p['tanggungan']['skor_di_maks']:.2f}, "
      f"rentang {p['tanggungan']['rentang_skor']:.1f}). Kurva datar pada 0–1,8, naik tajam di sekitar "
      f"{p['tanggungan']['titik_paling_tajam']:.1f} (Sedikit → Sedang: aturan Tidak Layak R13 hilang), lalu "
      "datar mulai 4 tanggungan. Plateau di atas 4 terjadi karena prestasi dasar 60 hanya \"Tinggi\" 0,5, "
      "sehingga α R18 (Prestasi Tinggi ∧ Tanggungan Banyak → Sangat Layak) tertahan di 0,5. Menambah "
      "tanggungan dari 4 ke 8 tidak lagi menaikkan skor.")
    A("")
    A(f"**Prestasi** (skor {p['prestasi']['skor_di_min']:.2f} → {p['prestasi']['skor_di_maks']:.2f}). "
      "Polanya mirip tanggungan karena keduanya berpasangan di kelompok B. Kurva datar pada 0–38, naik paling "
      f"tajam di sekitar {p['prestasi']['titik_paling_tajam']:.0f}, lalu datar mulai 60. Plateau di atas 60 "
      "terjadi karena μ tanggungan dasar (Banyak 0,5) menahan α R18, dan μ IPK Tinggi (0,4) menahan α R22.")
    A("")
    A("**Kesimpulan sensitivitas.** Sistem stabil (tanpa lompatan) dan arahnya konsisten. IPK adalah input yang "
      "paling menentukan per satuan, sedangkan tanggungan dan prestasi memiliki rentang pengaruh total terbesar "
      "pada nilai dasar ini. Banyaknya plateau menunjukkan bahwa dengan operator MIN, satu kriteria yang "
      "\"setengah-setengah\" dapat membatasi pengaruh kriteria lain.")
    A("")
    for k in config.INPUT_KEYS:
        A(f"![Gambar: sensitivitas terhadap {config.INPUTS[k]['label']}]({IMG}sensitivitas_{k}.png)")
        A("")

    # ---------------------------------------------------------------- BAB 8
    A("## 8. Keterbatasan dan Saran Pengembangan")
    A("")
    A("1. **Subjektivitas parameter MF.** Titik seperti \"penghasilan ≥ 9 juta = Tinggi\" atau \"IPK 3,0 = "
      "Sedang\" ditentukan oleh penyusun berdasarkan kebiasaan syarat beasiswa, bukan dari data atau "
      "survei pakar. Daerah lain (misalnya dengan UMR berbeda) memerlukan parameter yang berbeda. Saran: "
      "tentukan parameter melalui diskusi dengan panitia, gunakan distribusi data pendaftar sebenarnya "
      "(misalnya persentil), atau sesuaikan per wilayah.")
    A("2. **Kualitas dan kelengkapan aturan.** Aturan 2-anteseden menjamin cakupan, tetapi tidak dapat "
      "menangkap semua interaksi 4 variabel. Karena itu kelompok A dan B berdiri setara, sehingga bobot "
      "relatif antar-kriteria muncul secara implisit dari struktur aturan, bukan dinyatakan eksplisit. "
      "Saran: validasi aturan bersama pakar, tambahkan bobot aturan, atau bandingkan dengan aturan lengkap 81 kombinasi.")
    A("3. **Data simulasi.** Ke-22 data dibuat untuk menguji perilaku sistem (ekstrem, batas, tumpang tindih, "
      "bertentangan), bukan data pendaftar nyata. Belum ada \"kebenaran dasar\" (keputusan panitia) yang dapat "
      "dipakai untuk mengukur akurasi. Saran: uji dengan data historis seleksi dan hitung kesesuaiannya "
      "dengan keputusan panitia.")
    A(f"4. **Efek resolusi grid centroid.** Centroid dihitung secara diskrit. Dengan Δz = {fmt(config.OUTPUT_STEP)} "
      "galatnya < 0,03 poin terhadap centroid kontinu, tetapi grid kasar (Δz ≥ 5) dapat menggeser skor "
      "1–3 poin (Bab 7.2).")
    A(f"5. **Kompresi skor oleh centroid.** Skor efektif hanya {terburuk:.1f}–{terbaik:.1f}, bukan 0–100, "
      "karena centroid selalu berada di dalam daerah agregasi dan tidak pernah mencapai ujung semesta. "
      "Saran: interpretasikan skor relatif terhadap kategori, atau pertimbangkan metode defuzzifikasi lain "
      "(misalnya mean of maximum) maupun penyesuaian bahu output.")
    A("6. **Plateau dan saturasi** (Bab 7.3). Pada beberapa kombinasi, perbaikan satu kriteria tidak "
      "menaikkan skor. Hal ini benar secara logika MIN/MAX, tetapi dapat terasa kurang adil. Saran: bandingkan "
      "dengan operator AND = PRODUCT atau metode Sugeno.")
    A("7. **Pengembangan lain:** tambah kriteria (status yatim/piatu, kepemilikan rumah, daya listrik), "
      "tambah fitur akun panitia dan riwayat penilaian pada aplikasi web, dan optimasi parameter MF "
      "(misalnya dengan algoritma genetika) bila data historis tersedia.")
    A("")

    # ---------------------------------------------------------------- penutup
    A("## 9. Kesimpulan")
    A("")
    A(f"Sistem pendukung keputusan kelayakan beasiswa berbasis fuzzy Mamdani telah dibangun dengan 4 input, "
      f"1 output, dan {len(config.RULES)} aturan. Fungsi keanggotaan terbukti tanpa celah dan basis aturan "
      "mencakup 100% kombinasi input. Hasil engine identik dengan perhitungan manual dan hanya berselisih "
      "sekitar 0,02 poin dengan scikit-fuzzy (karena perbedaan cara menghitung centroid). Respons sistem "
      "monoton dan masuk akal pada kasus ekstrem, batas, tumpang tindih, maupun kriteria bertentangan. Skor "
      "yang dihasilkan berfungsi sebagai rekomendasi untuk panitia, bukan keputusan final.")
    A("")
    A("## Pembagian Kontribusi Anggota")
    A("")
    A("| No | Nama | NIM | Kontribusi |\n|---|---|---|---|")
    for i in range(1, 5):
        A(f"| {i} |  |  |  |")
    A("")
    A("## Lampiran: Cara Menjalankan Program")
    A("")
    A("```bash")
    A("pip install -r requirements.txt")
    A("python scripts/grafik_mf.py      # grafik MF")
    A("python scripts/uji_cakupan.py    # uji celah & cakupan aturan")
    A("python scripts/run_all.py        # pengujian 22 data")
    A("python scripts/detail_satu.py    # perhitungan lengkap 1 mahasiswa")
    A("python scripts/sensitivitas.py   # analisis sensitivitas")
    A("python scripts/validasi.py       # validasi manual vs program vs scikit-fuzzy")
    A("python scripts/buat_laporan.py   # laporan .md dan .docx")
    A("pytest                           # pengujian kode")
    A("streamlit run app.py             # aplikasi web")
    A("```")
    A("")

    md_path = os.path.join(LAP, "laporan.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("tersimpan:", md_path)
    docx_path = konversi(md_path, os.path.join(LAP, "laporan.docx"))
    print("tersimpan:", docx_path)


if __name__ == "__main__":
    main()
