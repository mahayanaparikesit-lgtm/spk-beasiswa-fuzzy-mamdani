"""Pengujian mesin fuzzy Mamdani."""
import itertools

import numpy as np
import pytest

import config
from fuzzy.coverage import cek_cakupan_aturan, cek_celah_mf, cek_kombinasi_kategori
from fuzzy.engine import inferensi, kategori_skor, skor_saja
from fuzzy.membership import mu_skalar, segitiga, trapesium

MF = {k: config.INPUTS[k]["mf"] for k in config.INPUT_KEYS}
MF_OUT = config.OUTPUT["mf"]


# --- nilai MF di titik-titik kunci ------------------------------------------
@pytest.mark.parametrize("var,kat,x,harap", [
    ("ipk", "Rendah", 0.0, 1.0), ("ipk", "Rendah", 2.5, 1.0), ("ipk", "Rendah", 2.75, 0.5),
    ("ipk", "Rendah", 3.0, 0.0), ("ipk", "Sedang", 3.0, 1.0), ("ipk", "Sedang", 3.25, 0.5),
    ("ipk", "Sedang", 2.5, 0.0), ("ipk", "Tinggi", 3.5, 1.0), ("ipk", "Tinggi", 4.0, 1.0),
    ("penghasilan", "Rendah", 3.0, 0.5), ("penghasilan", "Sedang", 5.0, 1.0),
    ("penghasilan", "Sedang", 7.5, 0.5), ("penghasilan", "Tinggi", 15.0, 1.0),
    ("tanggungan", "Sedikit", 0.0, 1.0), ("tanggungan", "Sedang", 2.0, 0.5),
    ("tanggungan", "Banyak", 8.0, 1.0), ("tanggungan", "Banyak", 4.0, 0.5),
    ("prestasi", "Rendah", 40.0, 0.5), ("prestasi", "Sedang", 50.0, 1.0),
    ("prestasi", "Tinggi", 100.0, 1.0), ("prestasi", "Tinggi", 60.0, 0.5),
])
def test_mf_titik_kunci(var, kat, x, harap):
    assert mu_skalar(x, MF[var][kat]) == pytest.approx(harap)


@pytest.mark.parametrize("kat,z,harap", [
    ("Tidak Layak", 0, 1.0), ("Tidak Layak", 35, 0.5), ("Cukup Layak", 45, 1.0),
    ("Cukup Layak", 55, 0.5), ("Layak", 65, 1.0), ("Layak", 75, 0.5),
    ("Sangat Layak", 100, 1.0), ("Sangat Layak", 65, 0.0),
])
def test_mf_output(kat, z, harap):
    assert mu_skalar(z, MF_OUT[kat]) == pytest.approx(harap)


def test_bentuk_dasar():
    x = np.array([0, 1, 2, 3, 4])
    assert np.allclose(segitiga(x, 1, 2, 3), [0, 0, 1, 0, 0])
    assert np.allclose(trapesium(x, 0, 1, 3, 4), [0, 1, 1, 1, 0])
    assert np.allclose(trapesium(x, 0, 0, 2, 4), [1, 1, 1, 0.5, 0])   # bahu kiri
    assert np.allclose(trapesium(x, 0, 2, 4, 4), [0, 0.5, 1, 1, 1])   # bahu kanan
    assert np.all((segitiga(np.linspace(-5, 5, 101), -1, 0, 1) >= 0)
                  & (segitiga(np.linspace(-5, 5, 101), -1, 0, 1) <= 1))


# --- tidak ada celah & cakupan ----------------------------------------------
def test_tidak_ada_celah_mf():
    for var, h in cek_celah_mf().items():
        assert h["ok"], f"Ada celah pada {var}: {h['titik_celah']}"


def test_cakupan_aturan_100_persen():
    c = cek_cakupan_aturan(25)
    assert c["persen"] == 100.0, c["contoh_tidak_tercakup"]
    assert cek_kombinasi_kategori()["tidak_tercakup"] == []


def test_minimal_15_aturan_memakai_4_variabel():
    assert len(config.RULES) >= 15
    dipakai = {v for r in config.RULES for v in r["if"]}
    assert dipakai == set(config.INPUT_KEYS)


# --- sifat output ------------------------------------------------------------
def test_skor_selalu_0_sampai_100():
    rng = np.random.default_rng(0)
    for _ in range(300):
        nilai = {k: rng.uniform(*config.INPUTS[k]["semesta"]) for k in config.INPUT_KEYS}
        s = skor_saja(nilai)
        assert 0 <= s <= 100
    # semua sudut semesta
    for sudut in itertools.product(*[config.INPUTS[k]["semesta"] for k in config.INPUT_KEYS]):
        s = skor_saja(dict(zip(config.INPUT_KEYS, sudut)))
        assert 0 <= s <= 100


def test_ekstrem_terbaik_lebih_besar_dari_terburuk():
    terbaik = skor_saja({"ipk": 4, "penghasilan": 0, "tanggungan": 8, "prestasi": 100})
    terburuk = skor_saja({"ipk": 0, "penghasilan": 15, "tanggungan": 0, "prestasi": 0})
    assert terbaik > terburuk
    assert kategori_skor(terbaik) == "Sangat Layak"
    assert kategori_skor(terburuk) == "Tidak Layak"


def test_kategori_skor_batas():
    assert kategori_skor(0) == "Tidak Layak"
    assert kategori_skor(34.99) == "Tidak Layak"
    assert kategori_skor(35) == "Cukup Layak"
    assert kategori_skor(55) == "Layak"
    assert kategori_skor(75) == "Sangat Layak"
    assert kategori_skor(100) == "Sangat Layak"


def test_input_di_luar_semesta_dipotong():
    a = skor_saja({"ipk": 5, "penghasilan": -3, "tanggungan": 12, "prestasi": 150})
    b = skor_saja({"ipk": 4, "penghasilan": 0, "tanggungan": 8, "prestasi": 100})
    assert a == pytest.approx(b)


def test_detail_case_banyak_aturan_aktif():
    res = inferensi(config.DETAIL_CASE)
    assert len(res["aktif"]) >= 8
    assert res["sum_mu"] > 0


# --- validasi manual = program -----------------------------------------------
def test_manual_sama_dengan_program():
    import validasi
    for nama, (i, p, t, s) in validasi.KASUS.items():
        manual = validasi.manual(i, p, t, s, [])
        program = skor_saja(dict(zip(config.INPUT_KEYS, (i, p, t, s))))
        assert manual == pytest.approx(program, abs=1e-9), nama


def test_sensitivitas_monoton():
    import sensitivitas
    for var in config.INPUT_KEYS:
        x, y = sensitivitas.sapuan(var)
        arah = sensitivitas.ARAH[var]
        assert np.all(arah * np.diff(y) >= -1e-9), var
