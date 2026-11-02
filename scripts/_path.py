"""Tambahkan root projek ke sys.path agar skrip bisa dijalankan dari mana saja."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
HASIL = os.path.join(ROOT, "hasil")
os.makedirs(HASIL, exist_ok=True)
