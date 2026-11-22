"""Multi-format novel exporter: Markdown, clean TXT, standalone HTML reader, and valid EPUB3."""

from __future__ import annotations

import html
import re
import zipfile
from pathlib import Path
from typing import Literal

from inkforge.genres.blueprints import get_genre
from inkforge.models import Chapter, NovelProject, utc_now_iso


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|\s]+", "_", name.strip())
    return cleaned[:64] or "novel"


def _paragraphs(content: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n|\n+", content.strip()) if p.strip()]


def render_markdown(project: NovelProject, chapters: list[Chapter]) -> str:
    bp = get_genre(project.genre_id)
    lines = [
        f"# {project.title}",
        "",
        f"> **题材**：{bp.name}（{bp.en_name}）  ",
        f"> **核心简介**：{project.bible.logline or project.premise}",
        "",
        "---",
        "",
    ]
    written = [c for c in chapters if c.content.strip()]
    if not written:
        lines.append("*（尚未生成正文内容）*")
        return "\n".join(lines)

    for ch in written:
        lines.append(f"## 第 {ch.chapter_number} 章  {ch.title}")
        lines.append("")
        for p in _paragraphs(ch.content):
            lines.append(p)
            lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_txt(project: NovelProject, chapters: list[Chapter]) -> str:
    bp = get_genre(project.genre_id)
    lines = [
        f"《{project.title}》",
        f"题材：{bp.name}",
        f"简介：{project.bible.logline or project.premise}",
        "=" * 40,
        "",
    ]
    for ch in chapters:
        if not ch.content.strip():
            continue
        lines.append(f"第{ch.chapter_number}章 {ch.title}")
        lines.append("")
        for p in _paragraphs(ch.content):
            lines.append("　　" + p)
            lines.append("")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_html(project: NovelProject, chapters: list[Chapter]) -> str:
    bp = get_genre(project.genre_id)
    written = [c for c in chapters if c.content.strip()]
    toc_items = "\n".join(
        f'<li><a href="#ch-{ch.chapter_number}">第 {ch.chapter_number} 章 · {html.escape(ch.title)}</a></li>'
        for ch in written
    )
    body_sections = []
    for ch in written:
        ps = "\n".join(f"<p>{html.escape(p)}</p>" for p in _paragraphs(ch.content))
        body_sections.append(
            f'<article id="ch-{ch.chapter_number}">'
            f'<h2>第 {ch.chapter_number} 章　{html.escape(ch.title)}</h2>'
            f"{ps}"
            f"</article>"
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{html.escape(project.title)} — InkForge 电子书</title>
<style>
  :root {{ --bg: #F6F8F7; --paper: #FFFFFF; --ink: #142126; --muted: #52646B; --accent: #1B5E52; --line: #DCE4E1; }}
  body {{ margin: 0; background: var(--bg); color: var(--ink); font-family: "Songti SC", "Noto Serif SC", Georgia, serif; line-height: 1.95; }}
  .wrap {{ max-width: 740px; margin: 40px auto; background: var(--paper); border: 1px solid var(--line); padding: 56px 64px; }}
  h1 {{ margin: 0 0 8px; font-size: 2rem; letter-spacing: 0.04em; }}
  .meta {{ color: var(--muted); font-size: 0.95rem; margin-bottom: 28px; padding-bottom: 20px; border-bottom: 1px solid var(--line); }}
  nav ul {{ list-style: none; padding: 0; margin: 0 0 40px; columns: 2; gap: 24px; }}
  nav a {{ color: var(--accent); text-decoration: none; font-size: 0.96rem; }}
  nav a:hover {{ text-decoration: underline; }}
  article {{ margin-top: 48px; padding-top: 32px; border-top: 1px solid var(--line); }}
  h2 {{ font-size: 1.35rem; margin: 0 0 24px; color: var(--ink); }}
  p {{ text-indent: 2em; margin: 0 0 1.15em; font-size: 1.08rem; }}
  @media (max-width: 680px) {{ .wrap {{ margin: 0; padding: 28px 20px; border: none; }} nav ul {{ columns: 1; }} }}
</style>
</head>
<body>
  <div class="wrap">
    <h1>{html.escape(project.title)}</h1>
    <div class="meta">{html.escape(bp.name)} · {html.escape(project.bible.logline or project.premise)}</div>
    <nav><ul>{toc_items}</ul></nav>
    {''.join(body_sections) or '<p>尚未生成正文内容。</p>'}
  </div>
</body>
</html>
"""


def write_epub(project: NovelProject, chapters: list[Chapter], out_path: Path) -> Path:
    """Create a valid, dependency-free EPUB3 archive using Python stdlib zipfile."""
    written = [c for c in chapters if c.content.strip()]
    book_id = f"urn:uuid:inkforge-{project.id}"
    modified = utc_now_iso().replace("+00:00", "Z")
    lang = "zh-CN" if project.language == "zh" else "en"

    css = (
        "body { font-family: serif; line-height: 1.85; color: #1a1a1a; margin: 1.2em; }\n"
        "h1, h2 { font-weight: 600; margin-bottom: 1em; }\n"
        "p { text-indent: 2em; margin: 0 0 0.9em; }\n"
    )

    container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

    manifest_items = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="style" href="style.css" media-type="text/css"/>',
    ]
    spine_items = []
    nav_links = []
    chapter_files: list[tuple[str, str]] = []

    for idx, ch in enumerate(written, 1):
        fname = f"chapter_{idx:03d}.xhtml"
        cid = f"ch{idx:03d}"
        manifest_items.append(
            f'<item id="{cid}" href="{fname}" media-type="application/xhtml+xml"/>'
        )
        spine_items.append(f'<itemref idref="{cid}"/>')
        label = f"第 {ch.chapter_number} 章 {ch.title}"
        nav_links.append(f'<li><a href="{fname}">{html.escape(label)}</a></li>')

        ps = "\n".join(f"<p>{html.escape(p)}</p>" for p in _paragraphs(ch.content))
        xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{lang}">
<head>
  <title>{html.escape(label)}</title>
  <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
  <h2>{html.escape(label)}</h2>
  {ps}
</body>
</html>
"""
        chapter_files.append((f"OEBPS/{fname}", xhtml))

    if not chapter_files:
        fname = "chapter_001.xhtml"
        manifest_items.append(
            f'<item id="ch001" href="{fname}" media-type="application/xhtml+xml"/>'
        )
        spine_items.append('<itemref idref="ch001"/>')
        nav_links.append(f'<li><a href="{fname}">{html.escape(project.title)}</a></li>')
        chapter_files.append(
            (
                f"OEBPS/{fname}",
                f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{lang}">
<head><title>{html.escape(project.title)}</title><link rel="stylesheet" type="text/css" href="style.css"/></head>
<body><h1>{html.escape(project.title)}</h1><p>{html.escape(project.premise)}</p></body>
</html>
""",
            )
        )

    nav_xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{lang}">
<head><title>目录</title><link rel="stylesheet" type="text/css" href="style.css"/></head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>{html.escape(project.title)}</h1>
    <ol>
      {''.join(nav_links)}
    </ol>
  </nav>
</body>
</html>
"""

    content_opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookId">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="BookId">{book_id}</dc:identifier>
    <dc:title>{html.escape(project.title)}</dc:title>
    <dc:language>{lang}</dc:language>
    <dc:creator>InkForge Studio</dc:creator>
    <dc:description>{html.escape(project.bible.logline or project.premise)}</dc:description>
    <meta property="dcterms:modified">{modified}</meta>
  </metadata>
  <manifest>
    {''.join(manifest_items)}
  </manifest>
  <spine>
    {''.join(spine_items)}
  </spine>
</package>
"""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w") as zf:
        # EPUB spec requires uncompressed mimetype as the very first entry
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", container_xml, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/content.opf", content_opf, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/nav.xhtml", nav_xhtml, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/style.css", css, compress_type=zipfile.ZIP_DEFLATED)
        for arc_name, body in chapter_files:
            zf.writestr(arc_name, body, compress_type=zipfile.ZIP_DEFLATED)
    return out_path


def export_project(
    project: NovelProject,
    chapters: list[Chapter],
    output_dir: Path,
    fmt: Literal["md", "txt", "html", "epub"] = "md",
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = _safe_filename(project.title)
    out_path = output_dir / f"{stem}.{fmt}"

    if fmt == "md":
        out_path.write_text(render_markdown(project, chapters), encoding="utf-8")
    elif fmt == "txt":
        out_path.write_text(render_txt(project, chapters), encoding="utf-8")
    elif fmt == "html":
        out_path.write_text(render_html(project, chapters), encoding="utf-8")
    elif fmt == "epub":
        write_epub(project, chapters, out_path)
    else:
        raise ValueError(f"不支持的导出格式：{fmt}")
    return out_path
