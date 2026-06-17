"""Build JPOXMLDOC01-appb.xml and JPOXMLDOC01-jpbibl.xml from HtmlPatent."""

from __future__ import annotations

import re
from pathlib import Path

from .parser import DescSection, HtmlPatent, Para

# ── XML helpers ───────────────────────────────────────────────────────────────

_PATCIT_LINE_RE = re.compile(r"^[　\s]*【特許文献([０-９\d]+)】(.+)")
_FIGREF_LINE_RE = re.compile(r"^[　\s]*【図([０-９\d]+)】(.+)")
_NPLCIT_LINE_RE = re.compile(r"^[　\s]*【非特許文献([０-９\d]+)】(.+)")
_CHEM_HDR_RE = re.compile(r"^[　\s]*【化([０-９\d]+)】\s*$")
_MATH_HDR_RE = re.compile(r"^[　\s]*【数([０-９\d]+)】\s*$")
_TABLE_HDR_RE = re.compile(r"^[　\s]*【表([０-９\d]+)】\s*$")

_IMG_RE = re.compile(r'<IMG\s[^>]*SRC="([^"]+)"[^>]*>', re.IGNORECASE)
_WIDTH_RE = re.compile(r'WIDTH="(\d+)"', re.IGNORECASE)
_HEIGHT_RE = re.compile(r'HEIGHT="(\d+)"', re.IGNORECASE)

_DIGIT_MAP = str.maketrans("０１２３４５６７８９", "0123456789")

# Inline HTML tags we convert to lowercase XML equivalents
_INLINE_TAG_RE = re.compile(r'<(/?)(SUB|SUP|U)>', re.IGNORECASE)

# Pattern to detect segment-ending punctuation (line is a "complete" segment)
_ITEM_START_RE = re.compile(r'^[（(][Ａ-Ｚ０-９A-Za-z0-9]+[）)]')
_MAX_LINE_LEN = 40  # JPO PRE-block word-wrap width (full-width chars)

# Kind → file prefix map
_KIND_PREFIX = {"chemistry": "C", "maths": "M", "tables": "T"}


def _to_ascii(s: str) -> str:
    return s.translate(_DIGIT_MAP)


_HTML_ENTITY_RE = re.compile(r'&(?:amp|lt|gt|apos|quot);')


def _decode_html_entities(s: str) -> str:
    """Decode basic HTML entities that JPO HTM files may contain."""
    return s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&apos;", "'").replace("&quot;", '"')


def _esc(s: str) -> str:
    s = _decode_html_entities(s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _esc_inline(s: str) -> str:
    """Convert inline HTML tags (SUB/SUP/U) to lowercase, escape remaining HTML chars."""
    s = _INLINE_TAG_RE.sub(lambda m: f"<{m.group(1)}{m.group(2).lower()}>", s)
    # Merge adjacent same-kind close+open pairs created by word-wrap splitting
    # e.g. </sub><sub> → (merge), </sup><sup> → (merge)
    s = re.sub(r'</(sub|sup|u)><\1>', '', s)
    # Split on our known lowercase inline tags, escape text segments
    parts = re.split(r'(</?(?:sub|sup|u)>)', s)
    result = []
    for part in parts:
        if re.match(r'^</?(?:sub|sup|u)>$', part):
            result.append(part)
        else:
            decoded = _decode_html_entities(part)
            result.append(decoded.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    return "".join(result)


def _strip_tags(s: str) -> str:
    return re.sub(r'<[^>]+>', '', s)


def _px_to_mm(px: int) -> float:
    return round(px * 25.4 / 96, 1)


# ── section name → XML element mapping ───────────────────────────────────────

_SECTION_TAG: dict[str, str] = {
    "技術分野": "technical-field",
    "背景技術": "background-art",
    "summary-of-invention": "summary-of-invention",
    "disclosure": "disclosure",
    "発明が解決しようとする課題": "tech-problem",
    "課題を解決するための手段": "tech-solution",
    "発明の効果": "advantageous-effects",
    "発明を実施するための形態": "description-of-embodiments",
    "発明を実施するための最良の形態": "best-mode",
    "産業上の利用可能性": "industrial-applicability",
    "図面の簡単な説明": "description-of-drawings",
}

_CONTAINER_SECTIONS = {"発明の概要", "発明の開示"}
_CONTAINER_CHILDREN = {"発明が解決しようとする課題", "課題を解決するための手段", "発明の効果"}
_CONTAINER_TAG_MAP = {
    "発明の概要": "summary-of-invention",
    "発明の開示": "disclosure",
}
# Sections that close the summary-of-invention/disclosure container
_OUTSIDE_CONTAINER = {
    "発明を実施するための形態",
    "発明を実施するための最良の形態",
    "産業上の利用可能性",
    "図面の簡単な説明",
    "符号の説明",
    "実施例",
}
# Sections that open description-of-embodiments (or best-mode)
_EMB_SECTIONS = {"発明を実施するための形態", "発明を実施するための最良の形態"}


# ── inline content builder ────────────────────────────────────────────────────


def _is_wordwrap(prev_raw: str, next_raw: str) -> bool:
    """Return True if next_raw is a word-wrap continuation of prev_raw.

    JPO HTM files wrap text at 40 full-width characters. A line that reaches
    exactly this width was cut by the formatter and continues on the next line,
    UNLESS the next line starts a new structural item (indented sentence or
    numbered/lettered item like （Ａ）).
    """
    stripped_len = len(_strip_tags(prev_raw.rstrip("\r\n")))
    if stripped_len < _MAX_LINE_LEN:
        return False  # line ended naturally → not word-wrap
    # max-width line; join unless next is a new structural item
    if re.match(r"^[　]", next_raw):
        return False  # new indented sentence
    if _ITEM_START_RE.match(next_raw):
        return False  # new numbered/lettered item
    return True


def _para_inline_xml(
    lines: list[str],
    img_counter: list[int],
    image_map: dict[str, str],
) -> str:
    """Build the inner XML of a <p> or <claim-text> element from raw content lines.

    Uses line-length-based word-wrap detection: lines hitting the 40-char maximum
    are joined with the next line unless the next starts a new structural item.
    """
    # Step 1: group lines into typed items
    # item = ('text', str) | ('block', kind, num, src, wi_mm, he_mm)
    items: list = []

    i = 0
    while i < len(lines):
        raw = lines[i].rstrip("\r\n")

        # Check for block headers (【化N】 etc.)
        block_kind: str | None = None
        block_num: int = 0
        for hdr_re, kind in (
            (_CHEM_HDR_RE, "chemistry"),
            (_MATH_HDR_RE, "maths"),
            (_TABLE_HDR_RE, "tables"),
        ):
            if m := hdr_re.match(raw):
                block_kind = kind
                block_num = int(_to_ascii(m.group(1)))
                break

        if block_kind is not None:
            # Look ahead for the IMG line
            if i + 1 < len(lines) and (img_m := _IMG_RE.search(lines[i + 1])):
                src = img_m.group(1)
                img_line = lines[i + 1]
                w_px = int(w_m.group(1)) if (w_m := _WIDTH_RE.search(img_line)) else 639
                h_px = int(h_m.group(1)) if (h_m := _HEIGHT_RE.search(img_line)) else 100
                wi = _px_to_mm(w_px)
                he = _px_to_mm(h_px)
                items.append(("block", block_kind, block_num, src, wi, he))
                i += 2
            else:
                # No IMG tag following; skip the header line
                i += 1
            continue

        # Regular text line – join with previous item if it was word-wrapped
        # items store ('text', accumulated_text, last_raw_line) so we check
        # the length of the LAST RAW LINE added, not the entire accumulated text.
        if raw and items and items[-1][0] == "text":
            _, prev_text, prev_last_raw = items[-1]
            if _is_wordwrap(prev_last_raw, raw):
                items[-1] = ("text", prev_text + raw, raw)
                i += 1
                continue

        items.append(("text", raw, raw))
        i += 1

    # Step 2: generate XML from items
    parts: list[str] = []
    for idx, item in enumerate(items):
        is_last = idx == len(items) - 1
        if item[0] == "text":
            text = item[1]
            if not text or not text.strip():
                # blank/space-only line
                xml_text = " <br />" if not is_last else " "
            else:
                xml_text = _esc_inline(text)
                if not is_last:
                    xml_text += "<br />"
            parts.append(xml_text)
        else:
            _, kind, num, src, wi, he = item
            img_counter[0] += 1
            n = img_counter[0]
            prefix = _KIND_PREFIX[kind]
            filename = f"JPOXMLDOC01-appb-{prefix}{n:06d}.tif"
            image_map[src] = filename
            img_tag = f'<img he="{he}" wi="{wi}" file="{filename}" img-format="tif" />'
            parts.append(f'<{kind} num="{num}">\n{img_tag}\n</{kind}>')

    return "\n".join(parts)


# ── paragraph builders ────────────────────────────────────────────────────────


def _para_tag(
    para: Para,
    img_counter: list[int],
    image_map: dict[str, str],
) -> str:
    content = _para_inline_xml(para.content_lines, img_counter, image_map)
    return f'<p num="{para.num}">\n{content}\n</p>'


def _patcit_para_tag(para: Para) -> str:
    lines_xml = []
    for ln in para.content_lines:
        if m := _PATCIT_LINE_RE.match(ln):
            n = int(_to_ascii(m.group(1)))
            text = _esc(m.group(2).strip())
            lines_xml.append(f'<patcit num="{n}"><text>{text}</text></patcit>')
    return f'<p num="{para.num}">\n' + "\n".join(lines_xml) + "\n</p>"


def _nplcit_para_tag(para: Para) -> str:
    lines_xml: list[str] = []
    cur_num: int | None = None
    cur_text = ""

    def _flush_nplcit() -> None:
        if cur_num is not None:
            lines_xml.append(
                f'<nplcit num="{cur_num}"><text>{_esc(cur_text.strip())}</text></nplcit>'
            )

    for ln in para.content_lines:
        if m := _NPLCIT_LINE_RE.match(ln):
            _flush_nplcit()
            cur_num = int(_to_ascii(m.group(1)))
            cur_text = m.group(2)
        elif cur_num is not None:
            cur_text += ln.rstrip("\r\n")

    _flush_nplcit()
    return f'<p num="{para.num}">\n' + "\n".join(lines_xml) + "\n</p>"


def _figref_para_tag(para: Para) -> str:
    lines_xml = []
    cur_figref: str | None = None
    cur_text = ""
    for ln in para.content_lines:
        if m := _FIGREF_LINE_RE.match(ln):
            if cur_figref is not None:
                lines_xml.append(f'<figref num="{cur_figref}">{_esc(cur_text.strip())}</figref>')
            cur_figref = _to_ascii(m.group(1))
            cur_text = m.group(2)
        elif cur_figref is not None:
            cur_text += ln
    if cur_figref is not None:
        lines_xml.append(f'<figref num="{cur_figref}">{_esc(cur_text.strip())}</figref>')
    return f'<p num="{para.num}">\n' + "\n".join(lines_xml) + "\n</p>"


def _br_para_tag(para: Para) -> str:
    """Paragraph with <br /> after each content line (for 符号の説明 etc.)."""
    inner = "\n".join(f"{_esc(ln)}<br />" for ln in para.content_lines if ln)
    return f'<p num="{para.num}">\n{inner}\n</p>'


def _detect_para_type(section_name: str, para: Para) -> str:
    """Return 'patcit', 'nplcit', 'figref', 'br', or 'normal'."""
    if section_name == "特許文献":
        return "patcit"
    if section_name == "非特許文献":
        return "nplcit"
    if section_name == "図面の簡単な説明":
        return "figref"
    if section_name == "符号の説明":
        return "br"
    for ln in para.content_lines:
        if _PATCIT_LINE_RE.match(ln):
            return "patcit"
    return "normal"


def _emit_para(
    section_name: str,
    para: Para,
    img_counter: list[int],
    image_map: dict[str, str],
) -> str:
    kind = _detect_para_type(section_name, para)
    if kind == "patcit":
        return _patcit_para_tag(para)
    if kind == "nplcit":
        return _nplcit_para_tag(para)
    if kind == "figref":
        return _figref_para_tag(para)
    if kind == "br":
        return _br_para_tag(para)
    return _para_tag(para, img_counter, image_map)


# ── appb.xml builder ──────────────────────────────────────────────────────────


def build_appb_xml(doc: HtmlPatent) -> tuple[str, dict[str, str]]:
    """Build JPOXMLDOC01-appb.xml content.

    Returns (xml_string, image_map) where image_map maps original image
    filenames (from HTML) to their new output filenames.
    """
    out: list[str] = []
    image_map: dict[str, str] = {}
    img_counter: list[int] = [0]

    out.append("<?xml version='1.0' encoding='utf-8'?>")
    out.append(
        f'<application-body country="JP" dtd-version="{doc.dtd_version}" lang="ja" status="n">'
    )
    out.append("<description>")

    title = _get_invention_title(doc)
    out.append(f"<invention-title>{_esc(title)}</invention-title>")

    container_tag: str | None = None
    in_citation = False
    in_patent_lit = False
    emb_tag: str | None = None        # open 'description-of-embodiments' or 'best-mode'
    in_emb_example = False             # inside <embodiments-example>

    for sec in doc.desc_sections:
        name = sec.name

        if name == "発明の名称":
            continue

        # ── citation list ────────────────────────────────────────────────────
        if name == "先行技術文献":
            in_citation = True
            in_patent_lit = False
            out.append("<citation-list>")
            continue

        if name == "特許文献" and in_citation:
            if in_patent_lit:
                out.append("</patent-literature>")
            out.append("<patent-literature>")
            in_patent_lit = True
            for p in sec.paragraphs:
                out.append(_emit_para(name, p, img_counter, image_map))
            continue

        if name == "非特許文献" and in_citation:
            if in_patent_lit:
                out.append("</patent-literature>")
                in_patent_lit = False
            out.append("<non-patent-literature>")
            for p in sec.paragraphs:
                out.append(_emit_para(name, p, img_counter, image_map))
            out.append("</non-patent-literature>")
            continue

        if in_citation and name not in ("特許文献", "非特許文献"):
            if in_patent_lit:
                out.append("</patent-literature>")
                in_patent_lit = False
            out.append("</citation-list>")
            in_citation = False
            # fall through to handle this section normally

        # ── container open ───────────────────────────────────────────────────
        if name in _CONTAINER_SECTIONS:
            container_tag = _CONTAINER_TAG_MAP[name]
            out.append(f"<{container_tag}>")
            continue

        # ── container children ───────────────────────────────────────────────
        if name in _CONTAINER_CHILDREN:
            tag = _SECTION_TAG[name]
            out.append(f"<{tag}>")
            for p in sec.paragraphs:
                out.append(_emit_para(name, p, img_counter, image_map))
            out.append(f"</{tag}>")
            continue

        # ── close container if open ──────────────────────────────────────────
        if container_tag and name in _OUTSIDE_CONTAINER:
            out.append(f"</{container_tag}>")
            container_tag = None

        # ── description-of-embodiments / best-mode ───────────────────────────
        if name in _EMB_SECTIONS:
            tag = _SECTION_TAG[name]
            emb_tag = tag
            out.append(f"<{tag}>")
            for p in sec.paragraphs:
                out.append(_emit_para(name, p, img_counter, image_map))
            # Don't close yet — 【実施例】 may follow
            continue

        # ── 実施例 → embodiments-example inside current emb_tag ──────────────
        if name == "実施例":
            if emb_tag and not in_emb_example:
                out.append("<embodiments-example>")
                in_emb_example = True
            for p in sec.paragraphs:
                out.append(_emit_para(name, p, img_counter, image_map))
            continue

        # ── close embodiments if still open ──────────────────────────────────
        if emb_tag:
            if in_emb_example:
                out.append("</embodiments-example>")
                in_emb_example = False
            out.append(f"</{emb_tag}>")
            emb_tag = None

        # ── 符号の説明 → <heading> ───────────────────────────────────────────
        if name == "符号の説明":
            out.append("<heading>符号の説明</heading>")
            for p in sec.paragraphs:
                out.append(_emit_para(name, p, img_counter, image_map))
            continue

        # ── description-of-drawings ─────────────────────────────────────────
        if name == "図面の簡単な説明":
            out.append("<description-of-drawings>")
            for p in sec.paragraphs:
                out.append(_emit_para(name, p, img_counter, image_map))
            out.append("</description-of-drawings>")
            continue

        # ── generic section ──────────────────────────────────────────────────
        tag = _SECTION_TAG.get(name)
        if tag is None:
            continue
        out.append(f"<{tag}>")
        for p in sec.paragraphs:
            out.append(_emit_para(name, p, img_counter, image_map))
        out.append(f"</{tag}>")

    # close any open blocks
    if in_citation:
        if in_patent_lit:
            out.append("</patent-literature>")
        out.append("</citation-list>")
    if container_tag:
        out.append(f"</{container_tag}>")
    if emb_tag:
        if in_emb_example:
            out.append("</embodiments-example>")
        out.append(f"</{emb_tag}>")

    out.append("</description>")

    # ── claims ───────────────────────────────────────────────────────────────
    out.append("<claims>")
    for i, raw_lines in enumerate(doc.claim_raw_lines, 1):
        # strip trailing blank lines
        trimmed = list(raw_lines)
        while trimmed and not trimmed[-1].strip():
            trimmed.pop()
        out.append(f'<claim num="{i}">')
        out.append("<claim-text>")
        content = _para_inline_xml(trimmed, img_counter, image_map)
        out.append(content)
        out.append("</claim-text>")
        out.append("</claim>")
    out.append("</claims>")

    # ── abstract ─────────────────────────────────────────────────────────────
    out.append("<abstract>")
    out.append('<p num="">')
    for idx, item in enumerate(doc.abstract_items):
        is_last = idx == len(doc.abstract_items) - 1
        suffix = "" if is_last else "<br />"
        out.append(f"{_esc(item)}{suffix}")
    out.append("</p>")
    out.append("</abstract>")

    # ── drawings ─────────────────────────────────────────────────────────────
    out.append("<drawings>")
    for fig in doc.figures:
        img_counter[0] += 1
        n = img_counter[0]
        ext = Path(fig.src).suffix.lower()
        img_name = f"JPOXMLDOC01-appb-D{n:06d}{ext}"
        image_map[fig.src] = img_name
        wi = _px_to_mm(fig.width)
        he = _px_to_mm(fig.height)
        img_format = ext.lstrip(".")
        out.append(f'<figure num="{fig.num}">')
        out.append(f'<img he="{he}" wi="{wi}" file="{img_name}" img-format="{img_format}" />')
        out.append("</figure>")
    out.append("</drawings>")

    out.append("</application-body>")
    return "\n".join(out) + "\n", image_map


def _get_invention_title(doc: HtmlPatent) -> str:
    for sec in doc.desc_sections:
        if sec.name == "発明の名称" and sec.paragraphs:
            return sec.paragraphs[0].content_lines[0] if sec.paragraphs[0].content_lines else ""
    return ""


# ── jpbibl.xml builder ────────────────────────────────────────────────────────


def build_jpbibl_xml(doc: HtmlPatent) -> str:
    out: list[str] = []
    out.append("<?xml version='1.0' encoding='utf-8'?>")
    out.append('<jp:pat-app-doc xmlns:jp="http://www.jpo.go.jp" lang="ja" dtd-version="1.0">')
    out.append('<jp:application-a63 jp:kind-of-law="patent">')
    out.append("<jp:document-code>A163</jp:document-code>")
    out.append(f"<jp:file-reference-id>{_esc(doc.file_reference_id)}</jp:file-reference-id>")
    out.append(f"<jp:addressed-to-person>{_esc(doc.addressed_to)}</jp:addressed-to-person>")

    if doc.ipc_list:
        out.append("<jp:ipc-article>")
        for ipc in doc.ipc_list:
            out.append(f"<jp:ipc>{_esc(ipc)}</jp:ipc>")
        out.append("</jp:ipc-article>")

    if doc.inventors:
        out.append("<jp:inventors>")
        for inv in doc.inventors:
            out.append("<jp:inventor>")
            out.append("<jp:addressbook>")
            out.append(f"<jp:name>{_esc(inv.name)}</jp:name>")
            if inv.address:
                out.append("<jp:address>")
                out.append(f"<jp:text>{_esc(inv.address)}</jp:text>")
                out.append("</jp:address>")
            out.append("</jp:addressbook>")
            out.append("</jp:inventor>")
        out.append("</jp:inventors>")

    if doc.applicants:
        out.append("<jp:applicants>")
        for app in doc.applicants:
            out.append("<jp:applicant>")
            out.append("<jp:addressbook>")
            out.append(f"<jp:name>{_esc(app.name)}</jp:name>")
            out.append(f"<jp:registered-number>{_esc(app.registered_number)}</jp:registered-number>")
            out.append("</jp:addressbook>")
            out.append("</jp:applicant>")
        out.append("</jp:applicants>")

    if doc.agents:
        out.append("<jp:agents>")
        for ag in doc.agents:
            out.append('<jp:agent jp:kind-of-agent="representative">')
            out.append("<jp:addressbook>")
            out.append(f"<jp:name>{_esc(ag.name)}</jp:name>")
            out.append(f"<jp:registered-number>{_esc(ag.registered_number)}</jp:registered-number>")
            out.append("</jp:addressbook>")
            out.append("<jp:attorney />")
            out.append("</jp:agent>")
        out.append("</jp:agents>")

    if doc.selected_agents:
        out.append("<jp:attorney-change-article>")
        for ag in doc.selected_agents:
            out.append('<jp:agent jp:kind-of-agent="representative">')
            out.append("<jp:addressbook>")
            out.append(f"<jp:name>{_esc(ag.name)}</jp:name>")
            out.append(f"<jp:registered-number>{_esc(ag.registered_number)}</jp:registered-number>")
            out.append("</jp:addressbook>")
            out.append("<jp:attorney />")
            out.append("</jp:agent>")
        out.append("</jp:attorney-change-article>")

    if doc.law_of_industrial:
        out.append(f"<jp:law-of-industrial-regenerate>{_esc(doc.law_of_industrial)}</jp:law-of-industrial-regenerate>")

    out.append("<jp:charge-article>")
    out.append("<jp:payment>")
    out.append(f'<jp:fee amount="{doc.fee_amount}" currency="yen" />')
    out.append(f'<jp:account number="{_esc(doc.fee_account)}" account-type="deposit" />')
    out.append("</jp:payment>")
    out.append("</jp:charge-article>")

    if doc.submission_items or doc.power_of_attorney_ids:
        out.append("<jp:submission-object-list-article>")
        for item in doc.submission_items:
            out.append("<jp:list-group>")
            out.append(f"<jp:document-name>{_esc(item.doc_name)}</jp:document-name>")
            out.append(f"<jp:number-of-object>{item.count}</jp:number-of-object>")
            out.append("</jp:list-group>")
        for pid in doc.power_of_attorney_ids:
            out.append("<jp:list-group>")
            out.append(f"<jp:general-power-of-attorney-id>{_esc(pid)}</jp:general-power-of-attorney-id>")
            out.append("</jp:list-group>")
        out.append("</jp:submission-object-list-article>")

    out.append("</jp:application-a63>")
    out.append("</jp:pat-app-doc>")
    return "\n".join(out) + "\n"
