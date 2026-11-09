#!/usr/bin/env python3
"""Make a PDF from the same .md source build_docx.py uses (no Word/LibreOffice needed).

Usage: python3 scripts/make_pdf.py <file.md> [more.md ...]  -> writes <file>.pdf next to each source
Renders simple HTML (same layout as the .docx: Arial, one column, real bullets).
- macOS: macOS's text system via scripts/html2pdf.swift (built in, nothing to install).
- Windows / Linux: a headless Edge, Chrome or Chromium "print to PDF" (Edge ships with Windows 10 and 11;
  on Linux install chromium or google-chrome). Set CHROME_PATH to point at a specific browser.
- No browser found: LibreOffice (`soffice --headless`) converts the .docx instead (Linux: apt/dnf install libreoffice).
- Set PDF_RENDERER=browser or PDF_RENDERER=libreoffice to force one (handy for testing on a Mac).
- Last resort: open the .docx in Word (or Google Docs) and Save As / Download as PDF.
"""
import html, os, pathlib, re, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
# macOS's HTML importer maps CSS px 1:1 to points (pt would render 33% larger); browsers need real pt.
CSS = """body{{font-family:Arial,Helvetica,'Liberation Sans','Arimo',sans-serif;font-size:10{u};line-height:1.25;color:#000}}
h1{{font-size:16{u};margin:0 0 2{u} 0}}
h2{{font-size:11{u};margin:10{u} 0 4{u} 0;text-transform:uppercase}}
p{{margin:0 0 4{u} 0}}
p.emp{{font-weight:bold;margin:7{u} 0 1{u} 0}}
p.role{{font-weight:bold;font-style:italic;margin:3{u} 0 1{u} 0}}
ul{{margin:0 0 2{u} 0;padding-left:14{u}}}
li{{margin:0 0 1.5{u} 0}}
p.gap{{font-size:10{u};line-height:1;margin:0}}
p.gap-sm{{font-size:5{u};line-height:1;margin:0}}"""
# Browsers honor every margin (macOS ignores most), so tighten them to match the Mac layout and page count.
BROWSER_CSS = ("@page{size:letter;margin:0.5in}body{line-height:1.2}h2{margin:0 0 2pt 0}p{margin:0 0 2pt 0}"
               "p.emp{margin:2pt 0 0 0}p.role{margin:0}ul{margin:0;padding-left:30pt}li{margin:0}")


def use_browser():
    return os.environ.get("PDF_RENDERER") in ("browser", "libreoffice") or (sys.platform != "darwin" and not os.environ.get("PDF_RENDERER"))


def find_soffice():
    pf = [os.environ.get(k, "") for k in ("PROGRAMFILES", "PROGRAMFILES(X86)")]
    candidates = [shutil.which(n) or "" for n in ("soffice", "libreoffice")]
    candidates += [os.path.join(p, r"LibreOffice\program\soffice.exe") for p in pf if p]
    candidates += ["/Applications/LibreOffice.app/Contents/MacOS/soffice"]
    return next((c for c in candidates if c and os.path.exists(c)), None)


def libreoffice_pdf(md_path, pdf_path):
    """Fallback without a browser: build the .docx from the same source, then let LibreOffice convert it."""
    exe = find_soffice()
    if not exe:
        print("No Edge/Chrome/Chromium or LibreOffice found. Install one (or set CHROME_PATH), "
              "or open the .docx in Word and Save As PDF.", file=sys.stderr)
        return False
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_docx, zipfile
    pdf_path = pathlib.Path(pdf_path).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        docx = pathlib.Path(tmp) / (pdf_path.stem + ".docx")
        with zipfile.ZipFile(docx, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in build_docx.build(str(md_path)).items():
                z.writestr(name, data)
        subprocess.run([exe, "--headless", f"-env:UserInstallation={pathlib.Path(tmp, 'lo').as_uri()}",
                        "--convert-to", "pdf", "--outdir", tmp, str(docx)], capture_output=True, text=True, timeout=180)
        out = docx.with_suffix(".pdf")
        if out.exists():
            shutil.move(str(out), pdf_path)
    ok = pdf_path.exists() and pdf_path.stat().st_size > 0
    print(f"wrote {pdf_path}" if ok else f"failed {md_path}")
    return ok


def find_browser():
    """Edge or Chrome on Windows, Chrome/Chromium elsewhere. CHROME_PATH wins."""
    if os.environ.get("CHROME_PATH"):
        return os.environ["CHROME_PATH"]
    pf = [os.environ.get(k, "") for k in ("PROGRAMFILES(X86)", "PROGRAMFILES", "LOCALAPPDATA")]
    candidates = [os.path.join(p, sub) for p in pf if p for sub in (
        r"Microsoft\Edge\Application\msedge.exe", r"Google\Chrome\Application\chrome.exe")]
    candidates += ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                   "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
    candidates += [shutil.which(n) or "" for n in ("msedge", "google-chrome", "chromium", "chromium-browser", "chrome")]
    return next((c for c in candidates if c and os.path.exists(c)), None)


def browser_pdf(html_path, pdf_path):
    """Print one HTML file to PDF with a headless Chromium browser. Returns True on success."""
    exe = find_browser()
    if not exe:
        print("No Edge/Chrome/Chromium found. Set CHROME_PATH, or open the .docx in Word and Save As PDF.", file=sys.stderr)
        return False
    pdf_path = pathlib.Path(pdf_path).resolve()
    with tempfile.TemporaryDirectory() as profile:  # a throwaway profile, so an open browser window doesn't interfere
        subprocess.run([exe, "--headless", "--disable-gpu", "--no-first-run", f"--user-data-dir={profile}",
                        "--no-pdf-header-footer", "--print-to-pdf-no-header", f"--print-to-pdf={pdf_path}",
                        pathlib.Path(html_path).resolve().as_uri()], capture_output=True, text=True, timeout=120)
    ok = pdf_path.exists() and pdf_path.stat().st_size > 0
    print(f"wrote {pdf_path}" if ok else f"failed {html_path}")
    return ok


def render(pairs):
    """pairs = [html1, pdf1, html2, pdf2, ...]. Returns a process-style exit code."""
    if use_browser():
        return 0 if all([browser_pdf(pairs[i], pairs[i + 1]) for i in range(0, len(pairs), 2)]) else 1
    r = subprocess.run(["swift", str(ROOT / "scripts" / "html2pdf.swift"), *pairs], capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode:
        print("\n".join(l for l in r.stderr.splitlines() if "CFURL" not in l), file=sys.stderr)
    return r.returncode


def inline(t):
    t = html.escape(t)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)


def to_html(md, browser=False):
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    u = "pt" if browser else "px"
    out, in_list = [], False
    for line in md.splitlines():
        line = line.rstrip()
        is_item = line.lstrip().startswith("- ")
        if in_list and not is_item:
            out.append("</ul>"); in_list = False
        if not line.strip():
            continue
        if line.startswith("# "):
            name, _, tag = line[2:].partition(" | ")
            tag_html = f"<span style='font-size:12{u};font-weight:normal'>&nbsp;&nbsp;|&nbsp;&nbsp;{inline(tag.strip())}</span>" if tag else ""
            out.append(f"<h1>{inline(name.strip())}{tag_html}</h1>")
        elif line.startswith("## "):
            if any(o.startswith("<h2>") or o.startswith("<p>") for o in out[1:]):
                out.append("<p class='gap'>&nbsp;</p>")  # blank line before each section after the first (macOS ignores most CSS margins)
            out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("#### "):
            out.append(f'<p class="role">{inline(" | ".join(p.strip() for p in line[5:].split("|")))}</p>')
        elif line.startswith("### "):
            if not out[-1].startswith("<h2>"):
                out.append("<p class='gap-sm'>&nbsp;</p>")  # small break between employers
            out.append(f'<p class="emp">{inline(" | ".join(p.strip() for p in line[4:].split("|")))}</p>')
        elif is_item:
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append(f"<li>{inline(line.lstrip()[2:])}</li>")
        else:
            out.append(f"<p>{inline(line)}</p>")
    if in_list:
        out.append("</ul>")
    css = CSS.format(u=u) + (BROWSER_CSS if browser else "")
    return f"<html><head><meta charset='utf-8'><style>{css}</style></head><body>{''.join(out)}</body></html>"


if __name__ == "__main__":
    srcs = [pathlib.Path(a).resolve() for a in sys.argv[1:]]
    if os.environ.get("PDF_RENDERER") == "libreoffice" or (use_browser() and not find_browser() and find_soffice()):
        sys.exit(0 if all([libreoffice_pdf(s, s.with_suffix(".pdf")) for s in srcs]) else 1)
    pairs = []
    tmp = pathlib.Path(tempfile.mkdtemp())
    for src in srcs:
        h = tmp / (src.parent.name + "-" + src.stem + ".html")
        h.write_text(to_html(src.read_text(encoding="utf-8"), browser=use_browser()), encoding="utf-8")
        pairs += [str(h), str(src.with_suffix(".pdf"))]
    sys.exit(render(pairs))
