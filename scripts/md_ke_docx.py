"""
Konverter Markdown (subset) -> .docx dengan python-docx.

Didukung: judul #..####, paragraf, **tebal**, *miring*, `kode`, daftar "- " dan "1. ",
tabel pipa, gambar ![alt](path), blok kode ```, garis ---, dan persamaan $$...$$
(dirender ke PNG dengan matplotlib mathtext; \\begin{cases} dirender sebagai
fungsi sepotong-sepotong).
"""
import os
import re
import tempfile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|_[^_\s][^_]*_|`[^`]+`|\$[^$]+\$)")


def _inline(par, teks, ukuran=None):
    for bagian in INLINE.split(teks):
        if not bagian:
            continue
        if bagian.startswith("**") and bagian.endswith("**"):
            run = par.add_run(bagian[2:-2])
            run.bold = True
        elif (bagian.startswith("*") and bagian.endswith("*")) or (bagian.startswith("_") and bagian.endswith("_")):
            run = par.add_run(bagian[1:-1])
            run.italic = True
        elif bagian.startswith("`") and bagian.endswith("`"):
            run = par.add_run(bagian[1:-1])
            run.font.name = "Consolas"
        elif bagian.startswith("$") and bagian.endswith("$"):
            run = par.add_run(_latex_ke_teks(bagian[1:-1]))
            run.italic = True
        else:
            run = par.add_run(bagian)
        if ukuran:
            run.font.size = Pt(ukuran)


def _latex_ke_teks(s):
    ganti = {r"\mu": "μ", r"\alpha": "α", r"\leq": "≤", r"\geq": "≥", r"\le": "≤", r"\ge": "≥",
             r"\sum": "Σ", r"\cdot": "·", r"\times": "×", r"\Delta": "Δ", r"\to": "→", r"\,": " "}
    for k, v in ganti.items():
        s = s.replace(k, v)
    return re.sub(r"[{}\\]", "", s)


def _render_rumus(latex, path):
    """Render $$latex$$ ke PNG. Mendukung \\begin{cases}...\\end{cases}."""
    m = re.match(r"(.*?)\\begin\{cases\}(.*)\\end\{cases\}(.*)", latex, re.S)
    if not m:
        fig = plt.figure(figsize=(0.01, 0.01))
        fig.text(0, 0, f"${latex}$", fontsize=14)
        fig.savefig(path, dpi=200, bbox_inches="tight", pad_inches=0.08, transparent=False)
        plt.close(fig)
        return
    lhs = m.group(1).strip()
    baris = [b.split("&") for b in re.split(r"\\\\", m.group(2)) if b.strip()]
    n = len(baris)
    per_baris = 0.5  # inci per baris
    fig = plt.figure(figsize=(7, per_baris * n))
    r = fig.canvas.get_renderer()
    t = fig.text(0.0, 0.5, f"${lhs}$", fontsize=13, va="center")
    x0 = t.get_window_extent(r).x1 / fig.bbox.width + 0.005
    # kurung kurawal digambar sebagai path vektor setinggi seluruh baris
    lebar_kb = 0.025
    ax = fig.add_axes([x0, 0.03, lebar_kb, 0.94])
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    verts = [(1, 1), (0.5, 1), (0.5, 0.85), (0.5, 0.56), (0.5, 0.5), (0.1, 0.5),
             (0.5, 0.5), (0.5, 0.44), (0.5, 0.15), (0.5, 0), (1, 0)]
    kode = [Path.MOVETO, Path.CURVE3, Path.CURVE3, Path.LINETO, Path.CURVE3, Path.CURVE3,
            Path.CURVE3, Path.CURVE3, Path.LINETO, Path.CURVE3, Path.CURVE3]
    ax.add_patch(PathPatch(Path(verts, kode), fill=False, linewidth=1.4, color="black"))
    x1 = x0 + lebar_kb + 0.015
    lebar_maks = 0
    for i, (expr, *_) in enumerate(baris):
        y = 1 - (i + 0.5) / n
        tk = fig.text(x1, y, f"${expr.strip().rstrip(',').replace(chr(92) + 'frac', chr(92) + 'dfrac')},$",
                      fontsize=13, va="center")
        lebar_maks = max(lebar_maks, tk.get_window_extent(r).x1 / fig.bbox.width)
    for i, (expr, *kond) in enumerate(baris):
        y = 1 - (i + 0.5) / n
        if kond:
            fig.text(lebar_maks + 0.03, y, f"${kond[0].strip()}$", fontsize=13, va="center")
    fig.savefig(path, dpi=200, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def _shading(cell, warna):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), warna)
    tcPr.append(shd)


def _tabel(doc, baris):
    sel = [[c.strip() for c in b.strip().strip("|").split("|")] for b in baris]
    sel = [s for s in sel if not all(re.fullmatch(r":?-{2,}:?", c) for c in s if c)]
    kolom = max(len(s) for s in sel)
    tbl = doc.add_table(rows=len(sel), cols=kolom)
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    ukuran = 9 if kolom <= 6 else 8
    for i, s in enumerate(sel):
        for j in range(kolom):
            cell = tbl.cell(i, j)
            cell.text = ""
            _inline(cell.paragraphs[0], s[j] if j < len(s) else "", ukuran)
            if i == 0:
                for run in cell.paragraphs[0].runs:
                    run.bold = True
                _shading(cell, "DCE8F5")
    doc.add_paragraph()


def konversi(md_path, docx_path):
    base = os.path.dirname(os.path.abspath(md_path))
    with open(md_path, encoding="utf-8") as f:
        baris = f.read().splitlines()
    doc = Document()
    gaya = doc.styles["Normal"]
    gaya.font.name = "Calibri"
    gaya.font.size = Pt(11)
    for sec in doc.sections:
        sec.left_margin = sec.right_margin = Inches(1)
    tmp = tempfile.mkdtemp()
    n_rumus = 0
    i = 0
    while i < len(baris):
        b = baris[i]
        s = b.strip()
        if not s:
            i += 1
            continue
        if s.startswith("```"):
            j = i + 1
            kode = []
            while j < len(baris) and not baris[j].strip().startswith("```"):
                kode.append(baris[j])
                j += 1
            p = doc.add_paragraph()
            run = p.add_run("\n".join(kode))
            run.font.name = "Consolas"
            run.font.size = Pt(8.5)
            p.paragraph_format.left_indent = Inches(0.2)
            i = j + 1
            continue
        if s.startswith("$$"):
            isi = s
            j = i
            while not (isi.endswith("$$") and len(isi) > 2):
                j += 1
                isi += " " + baris[j].strip()
            latex = isi[2:-2].strip()
            n_rumus += 1
            path = os.path.join(tmp, f"rumus_{n_rumus}.png")
            try:
                _render_rumus(latex, path)
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.add_run().add_picture(path, height=Inches(min(0.3 + 0.3 * latex.count("\\\\"), 1.6))
                                        if "cases" in latex else None)
            except Exception:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(_latex_ke_teks(latex))
                run.italic = True
            i = j + 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", s)
        if m:
            lvl = len(m.group(1))
            if lvl == 1:
                h = doc.add_heading(m.group(2), level=0)
            else:
                h = doc.add_heading(m.group(2), level=lvl - 1)
            i += 1
            continue
        if s.startswith("|"):
            j = i
            while j < len(baris) and baris[j].strip().startswith("|"):
                j += 1
            _tabel(doc, baris[i:j])
            i = j
            continue
        m = re.match(r"^!\[(.*?)\]\((.*?)\)", s)
        if m:
            path = os.path.normpath(os.path.join(base, m.group(2)))
            if os.path.exists(path):
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.add_run().add_picture(path, width=Inches(6.3))
                if m.group(1):
                    cap = doc.add_paragraph()
                    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    r = cap.add_run(m.group(1))
                    r.italic = True
                    r.font.size = Pt(9)
                    r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
            i += 1
            continue
        if s == "---":
            i += 1
            continue
        if s.startswith("> "):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.3)
            _inline(p, s[2:])
            for r in p.runs:
                r.italic = True
            i += 1
            continue
        m = re.match(r"^(\s*)[-*]\s+(.*)", b)
        if m:
            p = doc.add_paragraph(style="List Bullet" if not m.group(1) else "List Bullet 2")
            _inline(p, m.group(2))
            i += 1
            continue
        m = re.match(r"^\d+\.\s+(.*)", s)
        if m:
            p = doc.add_paragraph(style="List Number")
            _inline(p, m.group(1))
            i += 1
            continue
        # paragraf biasa (gabung baris berurutan)
        teks = [s]
        j = i + 1
        while j < len(baris) and baris[j].strip() and not re.match(r"^(#|\||!\[|```|\$\$|[-*]\s|\d+\.\s|> )", baris[j].strip()):
            teks.append(baris[j].strip())
            j += 1
        p = doc.add_paragraph()
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        _inline(p, " ".join(teks))
        i = j
    doc.save(docx_path)
    return docx_path
