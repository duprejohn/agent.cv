#!/usr/bin/env python3
"""Make a readable PDF from a prep/study markdown doc (tables, numbered lists, blockquotes, wrapped lines).

Usage: python3 scripts/doc_pdf.py <file.md> [more.md ...]  -> writes <file>.pdf next to each source
make_pdf.py is tuned for resumes and cover letters (one line per paragraph, no tables). Use this one for
interview prep sheets, study guides and other working docs. Uses the same renderer as make_pdf.py
(Mac: built in; Windows/Linux: headless Edge/Chrome/Chromium; see Platform notes in CLAUDE.md).
"""
import html, pathlib, re, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import make_pdf
CSS = """@page{size:letter;margin:0.5in}
body{font-family:Arial,Helvetica,sans-serif;font-size:10.5px;line-height:1.35;color:#111}
h1{font-size:17px;margin:0 0 6px 0;color:#1d4e89}
h2{font-size:13px;margin:14px 0 5px 0;color:#1d4e89;border-bottom:1px solid #1d4e89}
h3{font-size:11.5px;margin:10px 0 4px 0}
p{margin:0 0 5px 0}
ul,ol{margin:0 0 6px 0;padding-left:16px}
li{margin:0 0 2px 0}
blockquote{margin:4px 0 6px 10px;padding-left:8px;border-left:2px solid #2b78c2;color:#222}
table{border-collapse:collapse;width:100%;margin:2px 0 8px 0}
th,td{border:1px solid #bbb;padding:3px 5px;vertical-align:top;text-align:left}
th{background:#e8eef6}
code{font-family:Menlo,monospace;font-size:9.5px}
hr{border:0;border-top:1px solid #ccc;margin:8px 0}"""


def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", t)
    return t


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def to_html(md):
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    lines = md.splitlines()
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\|?\s*:?-{3,}", lines[i + 1].strip()):
            head = cells(s)
            out.append("<table><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr>")
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = cells(lines[i])
                row += [""] * (len(head) - len(row))
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row[:len(head)]) + "</tr>")
                i += 1
            out.append("</table>")
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", s)
        if m:
            n = min(len(m.group(1)), 3)
            out.append(f"<h{n}>{inline(m.group(2))}</h{n}>")
            i += 1
            continue
        if re.match(r"^-{3,}$", s):
            out.append("<hr>")
            i += 1
            continue
        if s.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append(f"<blockquote>{inline(' '.join(buf))}</blockquote>")
            continue
        lm = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)", line)
        if lm:
            tag = "ol" if lm.group(2)[0].isdigit() else "ul"
            out.append(f"<{tag}>")
            while i < len(lines):
                lm = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)", lines[i])
                if not lm:
                    break
                item = [lm.group(3)]
                i += 1
                # continuation lines (indented, not a new item or block)
                while i < len(lines) and lines[i].startswith((" ", "\t")) and lines[i].strip() and not re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
                    item.append(lines[i].strip())
                    i += 1
                out.append(f"<li>{inline(' '.join(item))}</li>")
            out.append(f"</{tag}>")
            continue
        buf = [s]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||>|-{3,}$|\s*([-*]|\d+\.)\s)", lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(buf))}</p>")
    return f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(out)}</body></html>"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    pairs = []
    tmp = pathlib.Path(tempfile.mkdtemp())
    for src in sys.argv[1:]:
        src = pathlib.Path(src).resolve()
        h = tmp / (src.parent.name + "-" + src.stem + ".html")
        h.write_text(to_html(src.read_text(encoding="utf-8")), encoding="utf-8")
        pairs += [str(h), str(src.with_suffix(".pdf"))]
    sys.exit(make_pdf.render(pairs))
