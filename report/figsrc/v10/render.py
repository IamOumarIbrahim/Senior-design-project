"""Print every figure page to PDF with headless Chrome and copy it into Figures/v10/.

python render.py            -> all figures defined in figures.py
python render.py r1 n1      -> only those
Also writes out/<name>.png previews (rendered from the PDF itself).
"""
import os, sys, shutil, subprocess, pathlib
import fitz  # PyMuPDF
import figures_final as figures

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "out"
DEST = HERE.parent.parent / "Figures" / "v10"
CHROME = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
          r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]
OUT.mkdir(exist_ok=True)
DEST.mkdir(parents=True, exist_ok=True)
chrome = next(c for c in CHROME if os.path.exists(c))

names = sys.argv[1:] or list(figures.FIGS)
for name in names:
    fig = figures.FIGS[name]()
    page = HERE / f"fig_{name}.html"            # next to fonts/ and assets/ so relative urls resolve
    page.write_text(fig.html(name), encoding="utf-8")
    pdf = OUT / f"{name}.pdf"
    if pdf.exists():
        pdf.unlink()
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--allow-file-access-from-files",
                    "--run-all-compositor-stages-before-draw", "--virtual-time-budget=4000",
                    f"--print-to-pdf={pdf}", page.as_uri()], check=True, capture_output=True, timeout=120)
    doc = fitz.open(pdf)
    if len(doc) != 1:
        print(f"WARNING {name}: {len(doc)} pages (content overflowed the canvas)")
    doc[0].get_pixmap(dpi=150).save(OUT / f"{name}.png")
    doc.close()
    shutil.copy(pdf, DEST / f"{name}.pdf")
    print("rendered", name, "->", DEST / f"{name}.pdf")
