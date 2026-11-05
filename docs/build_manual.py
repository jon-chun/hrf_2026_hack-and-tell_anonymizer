#!/usr/bin/env python3
"""Build docs/MANUAL.pdf (gstack make-pdf) and docs/MANUAL.docx (pandoc) from docs/MANUAL.md."""
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

DOCS = Path(__file__).resolve().parent
PDF_TOOL = Path.home() / ".claude/skills/gstack/make-pdf/dist/pdf"
TITLE = "Privacy and Grant Tools for Civil Society: User Manual"
# Print-only widths. These stay out of MANUAL.md because GitHub would show them as literal text.
WIDTHS = {"anonymizer-pipeline": "52%", "gate-decisions": "52%", "grant-critic-pipeline": "72%",
          "surrogate-consistency": "58%", "data-boundary": "75%", "leak-results": "100%", "edit-priorities": "100%"}
BORDERS = "".join(f'<w:{side} w:val="single" w:sz="4" w:space="0" w:color="BFBFBF"/>'
                  for side in ("top", "left", "bottom", "right", "insideH", "insideV"))


def print_source(for_pdf: bool) -> str:
    text = (DOCS / "MANUAL.md").read_text(encoding="utf-8")
    text = re.sub(r"^# User Manual\n", "", text, flags=re.M)
    text = re.sub(r" ?This manual is available as .*?\n", "\n", text, count=1)
    if for_pdf:
        # The PDF has its own contents page. Move the introduction under Part 1 so it does not fill a page alone.
        intro, rest = re.split(r"\*\*Contents\*\*\n.*?\n---\n", text, maxsplit=1, flags=re.S)
        text = rest.replace("# Part 1: Before you start\n", f"# Part 1: Before you start\n\n{intro.strip()}\n", 1)

    def image(m):
        # page=portrait stops make-pdf moving wide figures to a landscape page, away from their captions.
        extra = " page=portrait" if for_pdf else ""
        return f"({m[1]}){{width={WIDTHS[m[2]]}{extra}}}"
    text = re.sub(r"\((figures/([\w-]+)\.png)\)", image, text)

    # Repository links do not work in a standalone file, so show the path instead.
    def plain(m):
        label, target = m[1], m[2].removeprefix("../")
        return label if label.strip("`") == target or label.strip("`") in target else f"{label} (`{target}`)"
    return re.sub(r"(?<!!)\[([^\]]+)\]\((\.\./[^)]+)\)", plain, text)


def rewrite_part(path: Path, part: str, edit) -> None:
    """Replace one XML part of a docx archive, keeping the others unchanged."""
    with zipfile.ZipFile(path) as old:
        items = [(info, old.read(info.filename)) for info in old.infolist()]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as new:
        for info, data in items:
            new.writestr(info, edit(data.decode("utf-8")).encode("utf-8") if info.filename == part else data)


def style_reference(styles: str) -> str:
    """Use a plain sans font, a common monospace font and ruled tables."""
    styles = re.sub(r"<w:rFonts [^>]*Theme[^>]*/>", '<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial" w:eastAsia="Arial"/>', styles)
    styles = re.sub(r'(w:styleId="Table">.*?)(<w:tblCellMar>)', rf"\1<w:tblBorders>{BORDERS}</w:tblBorders>\2", styles, count=1, flags=re.S)
    return styles.replace("Consolas", "Courier New")


def add_code_style(styles: str) -> str:
    """Pandoc omits the code block style when highlighting is off, so define it with light shading."""
    style = ('<w:style w:type="paragraph" w:customStyle="1" w:styleId="SourceCode"><w:name w:val="Source Code"/>'
             '<w:basedOn w:val="Normal"/><w:pPr><w:shd w:val="clear" w:color="auto" w:fill="F3F3F3"/></w:pPr></w:style>')
    return styles.replace("</w:styles>", style + "</w:styles>")


def declare_png(types: str) -> str:
    """Pandoc declares each image separately. Strict validators also expect a default entry for the extension."""
    return re.sub(r"(<Types[^>]*>)", r'\1<Default Extension="png" ContentType="image/png"/>', types, count=1)


def keep_figures_with_captions(document: str) -> str:
    return re.sub(r'(<w:pPr>\s*<w:pStyle w:val="[^"]+"\s*/>)(\s*</w:pPr>\s*<w:r>(?:\s*<w:rPr\s*/>)?\s*<w:drawing>)',
                  r"\1<w:keepNext/>\2", document)


def build_docx(work: Path) -> None:
    source, reference, out = work / "manual.md", work / "reference.docx", DOCS / "MANUAL.docx"
    source.write_text(print_source(for_pdf=False), encoding="utf-8")
    reference.write_bytes(subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"],
                                         check=True, capture_output=True, timeout=30).stdout)
    rewrite_part(reference, "word/styles.xml", style_reference)
    subprocess.run(["pandoc", str(source), "-f", "gfm+attributes", "-o", str(out), "--reference-doc", str(reference),
                    "--resource-path", str(DOCS), "--syntax-highlighting=none", "--metadata", f"title={TITLE}"], check=True, timeout=120)
    rewrite_part(out, "word/document.xml", keep_figures_with_captions)
    rewrite_part(out, "word/styles.xml", add_code_style)
    rewrite_part(out, "[Content_Types].xml", declare_png)


def build_pdf() -> None:
    # make-pdf resolves images relative to the source file, so this copy must sit in docs/.
    source = DOCS / ".MANUAL.print.md"
    source.write_text(print_source(for_pdf=True), encoding="utf-8")
    try:
        subprocess.run([str(PDF_TOOL), "generate", "--title", TITLE, "--no-confidential", "--strict", "--quiet",
                        "--cover", "--toc", str(source), str(DOCS / "MANUAL.pdf")], check=True, timeout=180)
    finally:
        source.unlink(missing_ok=True)


def main() -> None:
    build_pdf()
    with tempfile.TemporaryDirectory() as tmp:
        build_docx(Path(tmp))


if __name__ == "__main__":
    main()
