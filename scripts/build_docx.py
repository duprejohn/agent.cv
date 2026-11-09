#!/usr/bin/env python3
"""Build an ATS-friendly .docx from a simple markdown source (no dependencies).

Usage: python3 scripts/build_docx.py <source.md> [out.docx]

Source format (one element per line):
  # Name | Tagline       -> name line (large, bold); optional tagline after " | " in smaller regular type
  plain text             -> paragraph (supports **bold**)
  ## Section             -> section heading (caps, bottom rule)
  ### Company | Place | Dates   -> bold employer line
  #### Title | Dates     -> bold-italic role line
  - bullet               -> real Word bullet (numbering), not a typed glyph
  <!-- comment -->       -> ignored (use for notes/confirmations)
  blank line             -> ignored (spacing comes from styles)
Single column, no tables, no text boxes, no header/footer: parses cleanly in applicant-tracking systems.
"""
import re, sys, zipfile
from xml.sax.saxutils import escape

FONT = "Arial"
BODY = 20  # half-points (10pt)


def runs(text, bold=False, italic=False, size=BODY):
    out = []
    for i, part in enumerate(re.split(r"\*\*", text)):
        if not part:
            continue
        b = bold or (i % 2 == 1)
        rpr = f'<w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}"/>'
        rpr += "<w:b/>" if b else ""
        rpr += "<w:i/>" if italic else ""
        rpr += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
        out.append(f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{escape(part)}</w:t></w:r>')
    return "".join(out)


def para(inner, before=0, after=60, extra=""):
    return f'<w:p><w:pPr>{extra}<w:spacing w:before="{before}" w:after="{after}"/></w:pPr>{inner}</w:p>'


def split_line(text, bold, italic, before):
    # Inline "A | B | Dates" keeps reading order identical for ATS parsers (no tabs or columns).
    inner = runs(" | ".join(p.strip() for p in text.split("|")), bold=bold, italic=italic)
    return para(inner, before=before, after=20, extra='<w:keepNext/>')


def build(src):
    body = []
    text = re.sub(r"<!--.*?-->", "", open(src, encoding="utf-8").read(), flags=re.S)
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("# "):
            name, _, tag = line[2:].partition(" | ")
            inner = runs(name.strip(), bold=True, size=32)
            if tag:
                inner += runs("  |  " + tag.strip(), size=24)
            body.append(para(inner, after=20))
        elif line.startswith("## "):
            border = '<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="444444"/></w:pBdr><w:keepNext/>'
            body.append(para(runs(line[3:].upper(), bold=True, size=22), before=200, after=80, extra=border))
        elif line.startswith("#### "):
            body.append(split_line(line[5:], bold=True, italic=True, before=60))
        elif line.startswith("### "):
            body.append(split_line(line[4:], bold=True, italic=False, before=140))
        elif line.lstrip().startswith("- "):
            numpr = '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr><w:ind w:left="360" w:hanging="220"/>'
            body.append(para(runs(line.lstrip()[2:]), after=30, extra=numpr))
        else:
            body.append(para(runs(line), after=80))
    sect = ('<w:sectPr><w:pgSz w:w="12240" w:h="15840"/>'
            '<w:pgMar w:top="720" w:right="720" w:bottom="720" w:left="720" w:header="0" w:footer="0" w:gutter="0"/></w:sectPr>')
    ns = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    doc = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {ns}><w:body>{"".join(body)}{sect}</w:body></w:document>'
    numbering = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:numbering {ns}>'
                 '<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="singleLevel"/>'
                 '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/>'
                 '<w:pPr><w:ind w:left="360" w:hanging="220"/></w:pPr>'
                 f'<w:rPr><w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}"/></w:rPr></w:lvl></w:abstractNum>'
                 '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num></w:numbering>')
    styles = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles {ns}><w:docDefaults><w:rPrDefault><w:rPr>'
              f'<w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}"/><w:sz w:val="{BODY}"/><w:lang w:val="en-US"/></w:rPr></w:rPrDefault>'
              '<w:pPrDefault><w:pPr><w:spacing w:line="252" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
              '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style></w:styles>')
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
          '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
          '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
          '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>')
    docrels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
               '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
               '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/></Relationships>')
    name = escape(next((l[2:].partition(" | ")[0].strip() for l in text.splitlines() if l.startswith("# ")), ""))
    core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            f'xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>{name}</dc:title><dc:creator>{name}</dc:creator></cp:coreProperties>')
    return {"[Content_Types].xml": ct, "_rels/.rels": rels, "word/_rels/document.xml.rels": docrels,
            "word/document.xml": doc, "word/styles.xml": styles, "word/numbering.xml": numbering, "docProps/core.xml": core}


if __name__ == "__main__":
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else re.sub(r"\.md$", ".docx", src)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in build(src).items():
            z.writestr(name, data)
    print("wrote", out)
