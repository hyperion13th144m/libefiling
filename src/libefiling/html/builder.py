"""Build JPOXMLDOC01-appb.xml and JPOXMLDOC01-jpbibl.xml from HtmlPatent."""

from __future__ import annotations

import re

from .parser import DescSection, HtmlPatent, Para

# ── XML helpers ───────────────────────────────────────────────────────────────

_PATCIT_LINE_RE = re.compile(r"^[　\s]*【特許文献([０-９\d]+)】(.+)")
_FIGREF_LINE_RE = re.compile(r"^[　\s]*【図([０-９\d]+)】(.+)")

_DIGIT_MAP = str.maketrans("０１２３４５６７８９", "0123456789")


def _to_ascii(s: str) -> str:
    return s.translate(_DIGIT_MAP)


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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
    "実施例": "description-of-embodiments",
}

_CONTAINER_SECTIONS = {"発明の概要", "発明の開示"}
_CONTAINER_CHILDREN = {"発明が解決しようとする課題", "課題を解決するための手段", "発明の効果"}
_CONTAINER_TAG_MAP = {
    "発明の概要": "summary-of-invention",
    "発明の開示": "disclosure",
}
_OUTSIDE_CONTAINER = {
    "発明を実施するための形態",
    "発明を実施するための最良の形態",
    "産業上の利用可能性",
    "図面の簡単な説明",
    "符号の説明",
    "実施例",
}


# ── paragraph builders ────────────────────────────────────────────────────────


def _join_para_lines(lines: list[str]) -> str:
    """Join content lines into a single paragraph text.

    Lines starting with 　 (full-width space) are segment starters;
    other lines are continuations joined without separator.
    For description <p> elements we emit one contiguous text block.
    """
    result = ""
    for line in lines:
        if line.startswith("　") or line.startswith(" "):
            result += line
        else:
            result += line
    return result


def _para_tag(para: Para, extra_class: str = "normal") -> str:
    text = _join_para_lines(para.content_lines)
    return f'<p num="{para.num}">\n{_esc(text)}\n</p>'


def _patcit_para_tag(para: Para) -> str:
    lines_xml = []
    for ln in para.content_lines:
        if m := _PATCIT_LINE_RE.match(ln):
            n = int(_to_ascii(m.group(1)))
            text = _esc(m.group(2).strip())
            lines_xml.append(f'<patcit num="{n}"><text>{text}</text></patcit>')
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
            cur_text += ln  # continuation
    if cur_figref is not None:
        lines_xml.append(f'<figref num="{cur_figref}">{_esc(cur_text.strip())}</figref>')
    return f'<p num="{para.num}">\n' + "\n".join(lines_xml) + "\n</p>"


def _br_para_tag(para: Para) -> str:
    """Paragraph with <br /> after each content line (for 符号の説明 etc.)."""
    inner = "\n".join(f"{_esc(ln)}<br />" for ln in para.content_lines if ln)
    return f'<p num="{para.num}">\n{inner}\n</p>'


def _detect_para_type(section_name: str, para: Para) -> str:
    """Return 'patcit', 'figref', 'br', or 'normal'."""
    if section_name == "特許文献":
        return "patcit"
    if section_name == "図面の簡単な説明":
        return "figref"
    if section_name == "符号の説明":
        return "br"
    # Check inline content
    for ln in para.content_lines:
        if _PATCIT_LINE_RE.match(ln):
            return "patcit"
    return "normal"


def _emit_para(section_name: str, para: Para) -> str:
    kind = _detect_para_type(section_name, para)
    if kind == "patcit":
        return _patcit_para_tag(para)
    if kind == "figref":
        return _figref_para_tag(para)
    if kind == "br":
        return _br_para_tag(para)
    return _para_tag(para)


# ── appb.xml builder ──────────────────────────────────────────────────────────


def build_appb_xml(doc: HtmlPatent) -> str:
    out: list[str] = []
    out.append("<?xml version='1.0' encoding='utf-8'?>")
    out.append(
        f'<application-body country="JP" dtd-version="{doc.dtd_version}" lang="ja" status="n">'
    )
    out.append("<description>")

    # invention title
    title = _get_invention_title(doc)
    out.append(f"<invention-title>{_esc(title)}</invention-title>")

    container_tag: str | None = None
    in_citation = False

    for sec in doc.desc_sections:
        name = sec.name

        if name == "発明の名称":
            continue

        # ── citation list ────────────────────────────────────────────────────
        if name == "先行技術文献":
            in_citation = True
            out.append("<citation-list>")
            out.append("<patent-literature>")
            continue
        if name == "特許文献" and in_citation:
            for p in sec.paragraphs:
                out.append(_emit_para(name, p))
            continue
        if in_citation and name not in ("特許文献",):
            out.append("</patent-literature>")
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
                out.append(_emit_para(name, p))
            out.append(f"</{tag}>")
            continue

        # ── close container if open ──────────────────────────────────────────
        if container_tag and name in _OUTSIDE_CONTAINER:
            out.append(f"</{container_tag}>")
            container_tag = None

        # ── 符号の説明 → <heading> ───────────────────────────────────────────
        if name == "符号の説明":
            out.append("<heading>符号の説明</heading>")
            for p in sec.paragraphs:
                out.append(_emit_para(name, p))
            continue

        # ── description-of-drawings ─────────────────────────────────────────
        if name == "図面の簡単な説明":
            out.append("<description-of-drawings>")
            for p in sec.paragraphs:
                out.append(_emit_para(name, p))
            out.append("</description-of-drawings>")
            continue

        # ── generic section ──────────────────────────────────────────────────
        tag = _SECTION_TAG.get(name)
        if tag is None:
            continue
        out.append(f"<{tag}>")
        for p in sec.paragraphs:
            out.append(_emit_para(name, p))
        out.append(f"</{tag}>")

    # close citation list if still open (shouldn't happen, but be safe)
    if in_citation:
        out.append("</patent-literature>")
        out.append("</citation-list>")
    # close container if still open
    if container_tag:
        out.append(f"</{container_tag}>")

    out.append("</description>")

    # ── claims ───────────────────────────────────────────────────────────────
    out.append("<claims>")
    for i, text in enumerate(doc.claim_texts, 1):
        out.append(f'<claim num="{i}">')
        out.append("<claim-text>")
        out.append(text)
        out.append("</claim-text>")
        out.append("</claim>")
    out.append("</claims>")

    # ── abstract ─────────────────────────────────────────────────────────────
    out.append("<abstract>")
    out.append('<p num="">')
    for item in doc.abstract_items:
        out.append(f"{_esc(item)}<br />")
    out.append("<br />")
    out.append("")
    out.append("</p>")
    out.append("</abstract>")

    # ── drawings ─────────────────────────────────────────────────────────────
    out.append("<drawings>")
    for fig in doc.figures:
        out.append(f'<figure num="{fig.num}">')
        img_name = f"JPOXMLDOC01-appb-D{fig.num:06d}.gif"
        out.append(
            f'<img he="{fig.height}" wi="{fig.width}" file="{img_name}" img-format="gif" />'
        )
        out.append("</figure>")
    out.append("</drawings>")

    out.append("</application-body>")
    return "\n".join(out) + "\n"


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
