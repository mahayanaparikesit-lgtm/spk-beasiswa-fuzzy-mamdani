"""
Antarmuka web SPK Kelayakan Beasiswa (Fuzzy Mamdani).
Jalankan:  streamlit run app.py
Tata letak mengikuti mockup dashboard: sidebar navigasi, kartu KPI berikon + badge,
grafik area utama (8 kolom) + panel samping (4 kolom), tabel dan daftar catatan di bawah.
"""
import io
import os

import altair as alt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

import config
from fuzzy.batch import proses_dataframe
from fuzzy.engine import inferensi
from fuzzy.membership import hitung_mf
from fuzzy.plotting import gambar_implikasi

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_CONTOH = os.path.join(ROOT, "data", "data_mahasiswa.csv")
LAPORAN = os.path.join(ROOT, "laporan", "laporan.docx")

# Warna (selaras dengan mockup)
BIRU = "#2563EB"
BIRU_TUA = "#1D4ED8"
TEKS = "#0F172A"
TEKS2 = "#64748B"
GARIS = "#E2E8F0"
SERI = ["#2A78D6", "#EB6834", "#1BAF7A", "#EDA100"]  # palet kategori tervalidasi
WARNA_KATEGORI = {"Tidak Layak": "merah", "Cukup Layak": "kuning", "Layak": "biru", "Sangat Layak": "hijau"}

st.set_page_config(page_title="SPK Kelayakan Beasiswa", page_icon="🎓", layout="wide")

# ---------------------------------------------------------------------------
# Gaya
# ---------------------------------------------------------------------------
CSS = f"""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,500,0,0" rel="stylesheet">
<style>
html, body, .stApp, .stMarkdown, button, input {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background: #ECEFF3; }}
/* sembunyikan tombol Deploy & menu, tetapi biarkan tombol buka-sidebar (ada di dalam stToolbar) */
[data-testid="stAppDeployButton"], [data-testid="stMainMenu"], [data-testid="stToolbarActions"],
[data-testid="stDecoration"] {{ display: none; }}
[data-testid="stExpandSidebarButton"] {{ background: #F7F8FA; border-radius: 10px; color: {BIRU_TUA};
    box-shadow: 0 1px 3px rgba(15,23,42,.12); }}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 40px; padding-bottom: 48px; max-width: 1360px; }}
.ms {{ font-family: 'Material Symbols Rounded'; font-weight: normal; font-style: normal; font-size: 20px;
       line-height: 1; display: inline-block; vertical-align: middle; -webkit-font-smoothing: antialiased; }}

/* Sidebar */
[data-testid="stSidebar"] {{ background: #E3E7ED; border-right: 1px solid #D8DDE5; }}
[data-testid="stSidebar"] .block-container, [data-testid="stSidebarUserContent"] {{ padding-top: 24px; }}
.logo {{ display: flex; align-items: center; gap: 12px; margin: 0 0 24px 4px; }}
.logo .ikon {{ width: 40px; height: 40px; border-radius: 10px; background: {BIRU}; color: #fff;
              display: flex; align-items: center; justify-content: center; }}
.logo .nama {{ color: {BIRU_TUA}; font-weight: 700; font-size: 18px; line-height: 1.1; }}
.logo .sub {{ color: {TEKS2}; font-size: 10px; letter-spacing: .08em; font-weight: 600; }}
[data-testid="stSidebar"] [data-testid="stRadio"], [data-testid="stSidebar"] [data-testid="stRadio"] > div,
[data-testid="stSidebar"] [role="radiogroup"] {{ gap: 4px; width: 100%; display: flex; flex-direction: column;
    align-items: stretch; }}
[data-testid="stSidebar"] label[data-testid="stRadioOption"] {{ width: 100% !important; box-sizing: border-box; }}
[data-testid="stSidebar"] [role="radiogroup"] label {{ padding: 10px 12px; border-radius: 10px; width: 100%;
    margin: 0; cursor: pointer; transition: background .15s; }}
[data-testid="stSidebar"] [role="radiogroup"] label > div > div:first-child:not([data-testid]) {{ display: none; }}
[data-testid="stSidebar"] [role="radiogroup"] label p {{ font-size: 14px; font-weight: 500; color: #334155; }}
[data-testid="stSidebar"] [role="radiogroup"] label p span[role="img"] {{ margin-right: 6px; color: #475569; }}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {{ background: #EDF0F4; }}
[data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"] {{ background: #F7F8FA;
    box-shadow: 0 1px 2px rgba(15,23,42,.06); }}
[data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"] p,
[data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"] p span[role="img"] {{ color: {BIRU_TUA}; font-weight: 600; }}
.judul-sidebar {{ color: {TEKS2}; font-size: 11px; font-weight: 600; letter-spacing: .08em; margin: 8px 0 4px 4px; }}

/* Header halaman */
.hjudul {{ font-size: 28px !important; font-weight: 700; color: {TEKS}; letter-spacing: -.01em; margin: 0; line-height: 1.2; }}
.hsub {{ color: {TEKS2}; font-size: 14px; margin-top: 4px; }}

/* Kartu */
.kpi {{ background: #F7F8FA; border-radius: 16px; padding: 20px; box-shadow: 0 1px 3px rgba(15,23,42,.06);
        height: 100%; }}
.kpi .atas {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }}
.kpi .ikon {{ width: 36px; height: 36px; border-radius: 10px; background: #DBE6FB; color: {BIRU_TUA};
             display: flex; align-items: center; justify-content: center; }}
.kpi .label {{ color: #334155; font-size: 13px; font-weight: 500; margin-bottom: 4px; }}
.kpi .nilai {{ color: {TEKS}; font-size: 28px; font-weight: 700; letter-spacing: -.02em;
              font-variant-numeric: tabular-nums; }}
.kpi .unit {{ color: {TEKS2}; font-size: 13px; font-weight: 500; margin-left: 4px; }}
.badge {{ display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px; border-radius: 999px;
         font-size: 11px; font-weight: 600; white-space: nowrap; }}
.badge.hijau {{ background: #DCFCE7; color: #15803D; }}
.badge.merah {{ background: #FEE2E2; color: #B91C1C; }}
.badge.kuning {{ background: #FEF3C7; color: #B45309; }}
.badge.biru {{ background: #DBEAFE; color: {BIRU_TUA}; }}
.badge.abu {{ background: #E2E8F0; color: #475569; }}
div[class*="st-key-kartu"] {{ background: #F7F8FA; border-radius: 16px; padding: 20px 24px;
    box-shadow: 0 1px 3px rgba(15,23,42,.06); }}
.kjudul {{ font-size: 16px; font-weight: 600; color: {TEKS}; margin: 0; }}
.kjudul-baris {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
.legenda {{ display: flex; gap: 16px; color: {TEKS2}; font-size: 12px; }}
.legenda i {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }}
.ksub {{ color: {TEKS2}; font-size: 11px; font-weight: 600; letter-spacing: .08em; margin: -4px 0 12px 0; }}

/* Progress bar derajat keanggotaan */
.pb {{ margin: 16px 0 0 0; }}
.pb .baris {{ display: flex; justify-content: space-between; font-size: 13px; color: #334155; margin-bottom: 8px; }}
.pb .baris b {{ color: {BIRU_TUA}; font-weight: 600; }}
.pb .rel {{ height: 8px; background: #E2E8F0; border-radius: 999px; overflow: hidden; }}
.pb .isi {{ height: 100%; background: linear-gradient(90deg, {BIRU_TUA}, #3B82F6); border-radius: 999px; }}
.pb .ket {{ color: {TEKS2}; font-size: 11px; margin-top: 6px; }}

/* Tabel */
.gulir {{ overflow-x: auto; }}
table.tb {{ width: 100%; border-collapse: collapse; font-size: 13px; min-width: 560px; }}
.kjudul-baris {{ flex-wrap: wrap; gap: 8px; }}
table.tb th {{ text-align: left; color: {TEKS2}; font-size: 11px; font-weight: 600; letter-spacing: .06em;
              padding: 12px; background: #EEF1F5; }}
table.tb td {{ padding: 12px; border-bottom: 1px solid {GARIS}; color: #1E293B; vertical-align: middle; }}
table.tb tr:hover td {{ background: #F1F4F8; }}
table.tb td.num {{ font-variant-numeric: tabular-nums; font-weight: 600; }}
.alfa {{ display: flex; align-items: center; gap: 8px; }}
.alfa .rel {{ width: 64px; height: 6px; background: #E2E8F0; border-radius: 999px; overflow: hidden; }}
.alfa .isi {{ height: 100%; background: {BIRU}; }}

/* Catatan (event list) */
.ev {{ display: flex; gap: 12px; align-items: flex-start; background: #FFFFFF; border-radius: 12px;
      padding: 14px; margin-bottom: 10px; box-shadow: 0 1px 2px rgba(15,23,42,.05); }}
.ev.kritis {{ border-left: 3px solid #DC2626; }}
.ev .ikon {{ width: 34px; height: 34px; min-width: 34px; border-radius: 8px; display: flex;
            align-items: center; justify-content: center; }}
.ev .ikon.merah {{ background: #FEE2E2; color: #B91C1C; }}
.ev .ikon.biru {{ background: #DBEAFE; color: {BIRU_TUA}; }}
.ev .ikon.hijau {{ background: #DCFCE7; color: #15803D; }}
.ev .t {{ font-size: 13px; font-weight: 600; color: {TEKS}; }}
.ev .d {{ font-size: 12px; color: {TEKS2}; margin-top: 2px; }}

/* Tombol */
.stDownloadButton button, .stButton button {{ border-radius: 10px; font-weight: 600; }}
.stDownloadButton button[kind="primary"] {{ background: linear-gradient(180deg, #3B82F6, {BIRU_TUA}); border: 0;
    box-shadow: 0 4px 12px rgba(37,99,235,.3); }}
[data-testid="stSidebar"] .stDownloadButton button {{ width: 100%; padding: 12px; }}
</style>
"""
# baris kosong di dalam <style> memutus blok HTML pada parser Markdown Streamlit
st.markdown("\n".join(b for b in CSS.splitlines() if b.strip()), unsafe_allow_html=True)


def ikon(nama):
    return f'<span class="ms">{nama}</span>'


def kartu_kpi(ikon_nama, label, nilai, unit="", badge="", warna_badge="abu"):
    b = f'<span class="badge {warna_badge}">{badge}</span>' if badge else ""
    st.markdown(f'<div class="kpi"><div class="atas"><div class="ikon">{ikon(ikon_nama)}</div>{b}</div>'
                f'<div class="label">{label}</div><div class="nilai">{nilai}<span class="unit">{unit}</span></div></div>',
                unsafe_allow_html=True)


def judul_kartu(judul, sub="", legenda=""):
    st.markdown(f'<div class="kjudul-baris"><p class="kjudul">{judul}</p>{legenda}</div>'
                + (f'<div class="ksub">{sub}</div>' if sub else ""), unsafe_allow_html=True)


def tampil_fig(fig):
    fig.patch.set_alpha(0)
    for ax in fig.axes:
        ax.set_facecolor("none")
    st.pyplot(fig, width="stretch")
    plt.close(fig)


def gaya_altair(chart, tinggi=300):
    return (chart.properties(height=tinggi, background="transparent")
            .configure_view(strokeWidth=0)
            .configure_axis(grid=True, gridColor=GARIS, domain=False, tickColor=GARIS, labelColor=TEKS2,
                            titleColor=TEKS2, labelFont="Inter", titleFont="Inter", labelFontSize=11,
                            titleFontSize=11, titleFontWeight=500)
            .configure_legend(labelFont="Inter", labelColor=TEKS2, orient="top", title=None, symbolType="circle"))


def chart_agregasi(res):
    z = res["z"]
    df = pd.DataFrame({"z": z, "μ": res["agregasi"]})
    mf = pd.concat([pd.DataFrame({"z": z, "μ": hitung_mf(z, spec), "Kategori": k})
                    for k, spec in config.OUTPUT["mf"].items()])
    x = alt.X("z:Q", title="Skor kelayakan z", scale=alt.Scale(domain=[0, 100]))
    y = alt.Y("μ:Q", title="Derajat keanggotaan μ", scale=alt.Scale(domain=[0, 1.1]))
    garis_mf = alt.Chart(mf).mark_line(strokeDash=[4, 4], strokeWidth=1, opacity=.55).encode(
        x=x, y=y, color=alt.Color("Kategori:N", sort=list(config.OUTPUT["mf"]),
                                  scale=alt.Scale(domain=list(config.OUTPUT["mf"]), range=SERI), legend=None))
    area = alt.Chart(df).mark_area(
        interpolate="monotone", line={"color": BIRU_TUA, "strokeWidth": 2.5},
        color=alt.Gradient(gradient="linear", x1=1, x2=1, y1=1, y2=0,
                           stops=[alt.GradientStop(color="rgba(37,99,235,0.02)", offset=0),
                                  alt.GradientStop(color="rgba(37,99,235,0.28)", offset=1)])
    ).encode(x=x, y=y, tooltip=[alt.Tooltip("z:Q", format=".1f"), alt.Tooltip("μ:Q", format=".3f")])
    c = pd.DataFrame({"z": [res["skor"]], "lbl": [f"z* = {res['skor']:.2f}"]})
    garis_c = alt.Chart(c).mark_rule(color="#DC2626", strokeWidth=2).encode(x="z:Q")
    teks_c = alt.Chart(c).mark_text(align="left", dx=6, color="#DC2626", fontWeight=600,
                                    font="Inter").encode(x="z:Q", y=alt.value(36), text="lbl:N")
    lbl = pd.DataFrame({"z": [12.5, 45, 65, 92.5], "t": list(config.OUTPUT["mf"])})
    teks_k = alt.Chart(lbl).mark_text(color=TEKS2, fontSize=10, font="Inter").encode(
        x="z:Q", y=alt.value(4), text="t:N")
    return gaya_altair(garis_mf + area + garis_c + teks_c + teks_k, 300)


def chart_mf(var, nilai_kini):
    info = config.OUTPUT if var == config.OUTPUT["key"] else config.INPUTS[var]
    lo, hi = info["semesta"]
    x = np.linspace(lo, hi, 601)
    df = pd.concat([pd.DataFrame({"x": x, "μ": hitung_mf(x, spec), "Kategori": k})
                    for k, spec in info["mf"].items()])
    kats = list(info["mf"])
    judul_x = f"{info['label']} ({info['satuan']})" if info["satuan"] else info["label"]
    garis = alt.Chart(df).mark_line(strokeWidth=2.5).encode(
        x=alt.X("x:Q", title=judul_x, scale=alt.Scale(domain=[lo, hi], nice=False)),
        y=alt.Y("μ:Q", title="μ", scale=alt.Scale(domain=[0, 1.05])),
        color=alt.Color("Kategori:N", sort=kats, scale=alt.Scale(domain=kats, range=SERI[:len(kats)])),
        tooltip=["Kategori", alt.Tooltip("x:Q", format=".2f"), alt.Tooltip("μ:Q", format=".3f")])
    rule = alt.Chart(pd.DataFrame({"x": [nilai_kini]})).mark_rule(color=TEKS, strokeDash=[4, 3]).encode(x="x:Q")
    return gaya_altair(garis + rule, 230)


def catatan(res):
    """Catatan untuk panitia: (jenis, judul, deskripsi)."""
    mu, skor = res["mu"], res["skor"]
    out = []
    if mu["ipk"]["Tinggi"] >= 0.5 and mu["penghasilan"]["Tinggi"] >= 0.5:
        out.append(("kritis", "Kriteria bertentangan", "IPK tinggi tetapi penghasilan orang tua tinggi."))
    if mu["ipk"]["Rendah"] >= 0.5 and mu["penghasilan"]["Rendah"] >= 0.5:
        out.append(("kritis", "Kriteria bertentangan", "IPK rendah tetapi keluarga berpenghasilan rendah."))
    if mu["prestasi"]["Tinggi"] >= 0.5 and mu["ipk"]["Rendah"] >= 0.5:
        out.append(("kritis", "Kriteria bertentangan", "Prestasi tinggi tetapi IPK rendah."))
    for lo, _, _ in config.KATEGORI_SKOR[1:]:
        if abs(skor - lo) < 2.0:
            out.append(("kritis", "Dekat batas kategori",
                        f"Skor {skor:.2f} berjarak < 2 poin dari batas {lo:g}. Disarankan peninjauan manual."))
    if not out:
        out.append(("ok", "Tidak ada konflik kriteria", "Skor tidak berada di dekat batas kategori."))
    out.append(("info", "Rekomendasi, bukan keputusan final",
                "Keputusan tetap pada panitia setelah verifikasi berkas dan wawancara."))
    return out


def html_catatan(daftar):
    peta = {"kritis": ("merah", "warning"), "info": ("biru", "info"), "ok": ("hijau", "check_circle")}
    h = ""
    for jenis, t, d in daftar:
        warna, ic = peta[jenis]
        h += (f'<div class="ev {"kritis" if jenis == "kritis" else ""}"><div class="ikon {warna}">{ikon(ic)}</div>'
              f'<div><div class="t">{t}</div><div class="d">{d}</div></div></div>')
    return h


def label_ant(r):
    return " ∧ ".join(f"{config.INPUTS[v]['label']} <b>{c}</b>" for v, c in r["if"].items())


# ---------------------------------------------------------------------------
# State input & kasus contoh
# ---------------------------------------------------------------------------
contoh = pd.read_csv(DATA_CONTOH)
for k, v in config.DETAIL_CASE.items():
    st.session_state.setdefault(f"in_{k}", float(v) if k in ("ipk", "penghasilan") else int(v))


def muat_contoh():
    pilih = st.session_state.get("pilih_contoh")
    if not pilih:
        return
    r = contoh[contoh["id"] == pilih.split(" ")[0]].iloc[0]
    st.session_state["in_ipk"] = float(r["ipk"])
    st.session_state["in_penghasilan"] = float(r["penghasilan"])
    st.session_state["in_tanggungan"] = int(round(r["tanggungan"]))
    st.session_state["in_prestasi"] = int(round(r["prestasi"]))


# ---------------------------------------------------------------------------
# Sidebar: logo, navigasi, input
# ---------------------------------------------------------------------------
HALAMAN = {
    "dashboard": ("dashboard", "Dashboard"),
    "detail": ("calculate", "Detail Perhitungan"),
    "data": ("table_chart", "Data Mahasiswa"),
    "mf": ("show_chart", "Fungsi Keanggotaan"),
    "aturan": ("account_tree", "Basis Aturan"),
}
with st.sidebar:
    st.markdown(f'<div class="logo"><div class="ikon">{ikon("school")}</div><div>'
                f'<div class="nama">BeasiswaFuzzy</div><div class="sub">DECISION SUPPORT</div></div></div>',
                unsafe_allow_html=True)
    hal = st.radio("Navigasi", list(HALAMAN), label_visibility="collapsed",
                   format_func=lambda k: f":material/{HALAMAN[k][0]}: {HALAMAN[k][1]}")
    st.markdown('<div class="judul-sidebar">INPUT MAHASISWA</div>', unsafe_allow_html=True)
    ipk = st.slider("IPK", 0.0, 4.0, step=0.01, key="in_ipk")
    pgh = st.slider("Penghasilan orang tua (juta Rp/bulan)", 0.0, 15.0, step=0.1, key="in_penghasilan")
    tg = st.slider("Jumlah tanggungan (orang)", 0, 8, step=1, key="in_tanggungan")
    pr = st.slider("Skor prestasi (0–100)", 0, 100, step=1, key="in_prestasi")
    st.write("")
    if os.path.exists(LAPORAN):
        with open(LAPORAN, "rb") as f:
            st.download_button(":material/description: Unduh Laporan", f.read(), "laporan.docx",
                               type="primary", width="stretch")

nilai = {"ipk": ipk, "penghasilan": pgh, "tanggungan": tg, "prestasi": pr}
res = inferensi(nilai)
aktif = [a for a in res["alphas"] if a["alpha"] > 0]


def header(judul, sub, aksi=True):
    kiri, k2, k3 = st.columns([6, 2.2, 1.6], vertical_alignment="center")
    with kiri:
        st.markdown(f'<div class="hjudul">{judul}</div><div class="hsub">{sub}</div>', unsafe_allow_html=True)
    if aksi:
        with k2:
            opsi = [f"{r.id} {r.nama_samaran}" for r in contoh.itertuples()]
            st.selectbox("Kasus contoh", opsi, index=None, key="pilih_contoh", on_change=muat_contoh,
                         label_visibility="collapsed", placeholder="Muat kasus contoh…")
        with k3:
            buf = io.StringIO()
            proses_dataframe(pd.DataFrame([nilai])).to_csv(buf, index=False)
            st.download_button(":material/download: Ekspor Hasil", buf.getvalue(), "hasil_penilaian.csv",
                               "text/csv", type="primary", width="stretch")
    st.write("")


# ---------------------------------------------------------------------------
# Halaman: Dashboard
# ---------------------------------------------------------------------------
if hal == "dashboard":
    header("Ringkasan Penilaian", "Rekomendasi kelayakan beasiswa berbasis logika fuzzy Mamdani.")
    lo_kat = max(lo for lo, _, _ in config.KATEGORI_SKOR if lo <= res["skor"])
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kartu_kpi("insights", "Skor Kelayakan", f"{res['skor']:.2f}", "/100",
                  f"+{res['skor'] - lo_kat:.1f} dari ambang", "hijau")
    with c2:
        kartu_kpi("workspace_premium", "Kategori Rekomendasi", res["kategori"], "",
                  "Rekomendasi", WARNA_KATEGORI[res["kategori"]])
    with c3:
        kartu_kpi("account_tree", "Aturan Aktif", f"{len(aktif)}", f"/ {len(config.RULES)}",
                  f"{100 * len(aktif) / len(config.RULES):.0f}% basis", "biru")
    with c4:
        terkuat = max(aktif, key=lambda a: a["alpha"])
        kartu_kpi("tune", "α-Predikat Terkuat", f"{terkuat['alpha']:.2f}", "",
                  f"{terkuat['id']} → {terkuat['then']}", "abu")
    st.write("")

    kiri, kanan = st.columns([8, 4], gap="medium")
    with kiri:
        with st.container(key="kartu_grafik"):
            judul_kartu("Daerah Agregasi dan Titik Centroid", legenda=(
                f'<div class="legenda"><span><i style="background:{BIRU}"></i>Agregasi MAX</span>'
                f'<span><i style="background:#DC2626"></i>Centroid</span></div>'))
            st.altair_chart(chart_agregasi(res), width="stretch")
    with kanan:
        with st.container(key="kartu_mu"):
            judul_kartu("Derajat Keanggotaan")
            h = ""
            for k in config.INPUT_KEYS:
                dom = max(res["mu"][k], key=res["mu"][k].get)
                m = res["mu"][k][dom]
                lain = " · ".join(f"{kat} {v:.2f}" for kat, v in res["mu"][k].items() if v > 0 and kat != dom)
                h += (f'<div class="pb"><div class="baris"><span>{config.INPUTS[k]["label"]}</span>'
                      f'<b>{dom} {m:.2f}</b></div><div class="rel"><div class="isi" style="width:{m * 100:.0f}%">'
                      f'</div></div><div class="ket">{lain or "keanggotaan penuh"}</div></div>')
            st.markdown(h, unsafe_allow_html=True)
    st.write("")

    kiri, kanan = st.columns([8, 4], gap="medium")
    with kiri:
        with st.container(key="kartu_aturan"):
            judul_kartu("Aturan Aktif", "α-PREDIKAT SETIAP ATURAN (AND = MIN)")
            baris = ""
            for a in sorted(aktif, key=lambda a: -a["alpha"]):
                kuat = ("Kuat", "hijau") if a["alpha"] >= 0.5 else (("Sedang", "biru") if a["alpha"] >= 0.25
                                                                    else ("Lemah", "abu"))
                baris += (f'<tr><td class="num">{a["id"]}</td><td>{label_ant(a)}</td>'
                          f'<td><span class="badge {WARNA_KATEGORI[a["then"]]}">{a["then"]}</span></td>'
                          f'<td><div class="alfa"><div class="rel"><div class="isi" style="width:{a["alpha"] * 100:.0f}%">'
                          f'</div></div><span class="num">{a["alpha"]:.3f}</span></div></td>'
                          f'<td><span class="badge {kuat[1]}">{kuat[0]}</span></td></tr>')
            st.markdown('<div class="gulir"><table class="tb"><tr><th>ATURAN</th><th>ANTESEDEN</th><th>KONSEKUEN</th>'
                        f'<th>α</th><th>KEKUATAN</th></tr>{baris}</table></div>', unsafe_allow_html=True)
    with kanan:
        with st.container(key="kartu_catatan"):
            judul_kartu("Catatan untuk Panitia")
            st.markdown(html_catatan(catatan(res)), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Halaman: Detail perhitungan
# ---------------------------------------------------------------------------
elif hal == "detail":
    header("Detail Perhitungan", "Langkah Mamdani untuk input saat ini: fuzzifikasi → α → implikasi → agregasi → centroid.")
    with st.container(key="kartu_fuzz"):
        judul_kartu("1. Fuzzifikasi", "DERAJAT KEANGGOTAAN SETIAP KATEGORI")
        baris = ""
        for k in config.INPUT_KEYS:
            for kat, m in res["mu"][k].items():
                spec = config.INPUTS[k]["mf"][kat]
                par = f"{spec[0]}({', '.join(f'{v:g}' for v in spec[1])})"
                baris += (f'<tr><td>{config.INPUTS[k]["label"]}</td><td class="num">{nilai[k]:g}</td><td>{kat}</td>'
                          f'<td style="color:{TEKS2}">{par}</td><td class="num">{m:.4f}</td></tr>')
        st.markdown('<div class="gulir"><table class="tb"><tr><th>VARIABEL</th><th>NILAI</th><th>KATEGORI</th><th>PARAMETER</th>'
                    f'<th>μ</th></tr>{baris}</table></div>', unsafe_allow_html=True)
    st.write("")
    with st.container(key="kartu_alpha"):
        judul_kartu("2. α-Predikat Setiap Aturan", "AND = MIN")
        hanya = st.toggle("Tampilkan hanya aturan aktif (α > 0)", value=True)
        baris = ""
        for a in res["alphas"]:
            if hanya and a["alpha"] <= 0:
                continue
            mins = ", ".join(f"{m:.3f}" for m in a["komponen"].values())
            baris += (f'<tr><td class="num">{a["id"]}</td><td>{label_ant(a)}</td><td>MIN({mins})</td>'
                      f'<td class="num">{a["alpha"]:.4f}</td>'
                      f'<td><span class="badge {WARNA_KATEGORI[a["then"]]}">{a["then"]}</span></td></tr>')
        st.markdown('<div class="gulir"><table class="tb"><tr><th>ATURAN</th><th>ANTESEDEN</th><th>PERHITUNGAN</th><th>α</th>'
                    f'<th>KONSEKUEN</th></tr>{baris}</table></div>', unsafe_allow_html=True)
    st.write("")
    with st.container(key="kartu_impl"):
        judul_kartu("3. Implikasi MIN (Clipping)", "FUNGSI OUTPUT TERPOTONG SETINGGI α")
        tampil_fig(gambar_implikasi(res, tema="terang"))
    st.write("")
    with st.container(key="kartu_centroid"):
        judul_kartu("4–5. Agregasi MAX dan Centroid")
        st.altair_chart(chart_agregasi(res), width="stretch")
        st.latex(r"z^* = \frac{\sum_i \mu_{agr}(z_i)\,z_i}{\sum_i \mu_{agr}(z_i)} = "
                 rf"\frac{{{res['sum_mu_z']:.3f}}}{{{res['sum_mu']:.3f}}} = {res['skor']:.3f}")
        st.caption(f"Grid output: z = 0, {config.OUTPUT_STEP:g}, …, 100 ({len(res['z'])} titik).")

# ---------------------------------------------------------------------------
# Halaman: Data mahasiswa (CSV)
# ---------------------------------------------------------------------------
elif hal == "data":
    header("Data Mahasiswa", "Proses banyak pendaftar sekaligus dari file CSV.", aksi=False)
    with st.container(key="kartu_unggah"):
        judul_kartu("Unggah Data", "KOLOM WAJIB: IPK, PENGHASILAN (JUTA), TANGGUNGAN, PRESTASI")
        unggah = st.file_uploader("Unggah CSV", type=["csv"], label_visibility="collapsed")
    df_in, sumber = (pd.read_csv(unggah), unggah.name) if unggah is not None else (contoh, "data contoh (22 mahasiswa)")
    try:
        df_out = proses_dataframe(df_in)
    except ValueError as e:
        st.markdown(html_catatan([("kritis", "Format CSV tidak sesuai", str(e))]), unsafe_allow_html=True)
    else:
        st.write("")
        hit = df_out["kategori_kelayakan"].value_counts()
        ikon_kat = {"Tidak Layak": "cancel", "Cukup Layak": "help", "Layak": "check_circle",
                    "Sangat Layak": "workspace_premium"}
        for col, (_, _, nama) in zip(st.columns(4), config.KATEGORI_SKOR):
            with col:
                n = int(hit.get(nama, 0))
                kartu_kpi(ikon_kat[nama], nama, n, "mahasiswa", f"{100 * n / len(df_out):.0f}%",
                          WARNA_KATEGORI[nama])
        st.write("")
        with st.container(key="kartu_tabel"):
            judul_kartu("Hasil Penilaian", f"SUMBER: {sumber.upper()} · DIURUTKAN DARI SKOR TERTINGGI")
            tampil = [c for c in ["id", "nama_samaran", "ipk", "penghasilan", "tanggungan", "prestasi",
                                  "jumlah_aturan_aktif", "skor", "kategori_kelayakan"] if c in df_out.columns]
            st.dataframe(df_out[tampil].sort_values("skor", ascending=False), hide_index=True, width="stretch",
                         column_config={"skor": st.column_config.ProgressColumn("skor", min_value=0, max_value=100,
                                                                                format="%.2f")})
            with st.expander("Kolom lengkap (μ dan aturan aktif)"):
                st.dataframe(df_out, hide_index=True, width="stretch")
            buf = io.StringIO()
            df_out.to_csv(buf, index=False)
            st.download_button(":material/download: Unduh Hasil (CSV)", buf.getvalue(), "hasil_kelayakan.csv",
                               "text/csv", type="primary")

# ---------------------------------------------------------------------------
# Halaman: Fungsi keanggotaan
# ---------------------------------------------------------------------------
elif hal == "mf":
    header("Fungsi Keanggotaan", "Garis putus-putus vertikal menandai nilai input saat ini.", aksi=False)
    kol = st.columns(2, gap="medium")
    for i, k in enumerate(config.INPUT_KEYS):
        with kol[i % 2]:
            with st.container(key=f"kartu_mf_{k}"):
                judul_kartu(config.INPUTS[k]["label"])
                st.altair_chart(chart_mf(k, nilai[k]), width="stretch")
            st.write("")
    with st.container(key="kartu_mf_out"):
        judul_kartu(config.OUTPUT["label"], "<35 TIDAK LAYAK · 35–55 CUKUP · 55–75 LAYAK · ≥75 SANGAT LAYAK")
        st.altair_chart(chart_mf(config.OUTPUT["key"], res["skor"]), width="stretch")

# ---------------------------------------------------------------------------
# Halaman: Basis aturan
# ---------------------------------------------------------------------------
elif hal == "aturan":
    header("Basis Aturan", f"{len(config.RULES)} aturan IF–THEN · AND = MIN · aturan aktif untuk input saat ini ditandai.",
           aksi=False)
    with st.container(key="kartu_rules"):
        baris = ""
        ids_aktif = {a["id"]: a["alpha"] for a in aktif}
        for r in config.RULES:
            sel = "".join(f'<td>{r["if"].get(k, "–")}</td>' for k in config.INPUT_KEYS)
            st_aktif = (f'<span class="badge hijau">α {ids_aktif[r["id"]]:.2f}</span>' if r["id"] in ids_aktif
                        else '<span class="badge abu">tidak aktif</span>')
            baris += (f'<tr><td class="num">{r["id"]}</td>{sel}'
                      f'<td><span class="badge {WARNA_KATEGORI[r["then"]]}">{r["then"]}</span></td>'
                      f'<td style="color:{TEKS2}">{r["alasan"]}</td><td>{st_aktif}</td></tr>')
        kepala = "".join(f"<th>{config.INPUTS[k]['label'].upper()}</th>" for k in config.INPUT_KEYS)
        st.markdown(f'<div class="gulir"><table class="tb"><tr><th>ID</th>{kepala}<th>KELAYAKAN</th><th>ALASAN</th><th>STATUS</th></tr>'
                    f'{baris}</table></div>', unsafe_allow_html=True)
