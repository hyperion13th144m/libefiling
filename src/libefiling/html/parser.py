"""Parse the structured text inside the PRE block of a JPO e-filing HTM file."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ── character normalization ───────────────────────────────────────────────────

_DIGIT_MAP = str.maketrans("０１２３４５６７８９", "0123456789")


def _to_ascii(s: str) -> str:
    return s.translate(_DIGIT_MAP)


def _zfill4(s: str) -> str:
    return _to_ascii(s).zfill(4)


# ── regular expressions ───────────────────────────────────────────────────────

# 　【０００１】  ← paragraph number (4-5 full-width digits, optional leading whitespace)
_PARA_NUM_RE = re.compile(r"^[　\s]*【([０-９]{4,5})】\s*$")

# 【書類名】テキスト
_DOC_SECTION_RE = re.compile(r"^【書類名】(.+)")

# 【発明の名称】テキスト  (inside 明細書 block, first field)
_INVENTION_TITLE_RE = re.compile(r"^【発明の名称】(.+)")

# 【請求項N】  N is ASCII or full-width digits
_CLAIM_NUM_RE = re.compile(r"^【請求項([０-９\d]+)】\s*$")

# 【図N】  in the drawings section (top-level, no leading whitespace)
_FIGURE_HEADER_RE = re.compile(r"^【図([０-９\d]+)】\s*$")

# <IMG SRC="..." WIDTH="..." HEIGHT="...">
_IMG_RE = re.compile(
    r'<IMG\s[^>]*SRC="([^"]+)"[^>]*>',
    re.IGNORECASE,
)
_WIDTH_RE = re.compile(r'WIDTH="(\d+)"', re.IGNORECASE)
_HEIGHT_RE = re.compile(r'HEIGHT="(\d+)"', re.IGNORECASE)

# section header at column 0: 【something】  (no full-width-digit-only content)
_SECTION_HDR_RE = re.compile(r"^【([^】]+)】")

# inline patcit: 　　【特許文献N】テキスト
_PATCIT_LINE_RE = re.compile(r"^[　\s]+【特許文献([０-９\d]+)】(.+)")

# inline figref: 　　【図N】テキスト
_FIGREF_LINE_RE = re.compile(r"^[　\s]+【図([０-９\d]+)】(.+)")


# ── data model ────────────────────────────────────────────────────────────────


@dataclass
class Para:
    num: str  # ASCII digits, e.g. "0001"; "" for unnumbered
    content_lines: list[str] = field(default_factory=list)


@dataclass
class DescSection:
    name: str
    paragraphs: list[Para] = field(default_factory=list)


@dataclass
class Inventor:
    name: str = ""
    address: str = ""


@dataclass
class Applicant:
    registered_number: str = ""
    name: str = ""


@dataclass
class Agent:
    registered_number: str = ""
    name: str = ""


@dataclass
class SubmissionItem:
    doc_name: str = ""
    count: int = 1


@dataclass
class Figure:
    num: int
    src: str  # original filename of the GIF
    width: int
    height: int


@dataclass
class HtmlPatent:
    # ── 特許願 ──────────────────────────────────────────────────────────────
    file_reference_id: str = ""
    addressed_to: str = ""
    ipc_list: list[str] = field(default_factory=list)
    inventors: list[Inventor] = field(default_factory=list)
    applicants: list[Applicant] = field(default_factory=list)
    agents: list[Agent] = field(default_factory=list)
    selected_agents: list[Agent] = field(default_factory=list)
    law_of_industrial: str = ""
    fee_amount: int = 0
    fee_account: str = ""
    submission_items: list[SubmissionItem] = field(default_factory=list)
    power_of_attorney_ids: list[str] = field(default_factory=list)

    # ── 明細書 ──────────────────────────────────────────────────────────────
    desc_sections: list[DescSection] = field(default_factory=list)

    # ── 特許請求の範囲 ─────────────────────────────────────────────────────
    # claim_texts[0] = claim 1 text (already joined), etc.
    claim_texts: list[str] = field(default_factory=list)

    # ── 要約書 ──────────────────────────────────────────────────────────────
    # Each element is one "item" line in the abstract (joined continuations)
    abstract_items: list[str] = field(default_factory=list)

    # ── 図面 ────────────────────────────────────────────────────────────────
    figures: list[Figure] = field(default_factory=list)

    # ── derived ─────────────────────────────────────────────────────────────
    dtd_version: str = "1.0"


# ── public entry point ────────────────────────────────────────────────────────


def parse(lines: list[str]) -> HtmlPatent:
    doc = HtmlPatent()

    for name, section_lines in _split_doc_sections(lines):
        if name == "特許願":
            _parse_application(section_lines, doc)
        elif name == "明細書":
            _parse_description(section_lines, doc)
        elif name == "特許請求の範囲":
            _parse_claims(section_lines, doc)
        elif name == "要約書":
            _parse_abstract(section_lines, doc)
        elif name == "図面":
            _parse_drawings(section_lines, doc)

    # Determine DTD version from section names present
    names = {s.name for s in doc.desc_sections}
    if "発明の概要" in names or "先行技術文献" in names:
        doc.dtd_version = "1.6"
    else:
        doc.dtd_version = "1.0"

    return doc


# ── section splitter ──────────────────────────────────────────────────────────


def _split_doc_sections(lines: list[str]) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    current_name: str | None = None
    current_lines: list[str] = []

    for line in lines:
        m = _DOC_SECTION_RE.match(line)
        if m:
            if current_name is not None:
                sections.append((current_name, current_lines))
            current_name = m.group(1).strip()
            current_lines = []
        elif current_name is not None:
            current_lines.append(line)

    if current_name is not None:
        sections.append((current_name, current_lines))
    return sections


# ── 特許願 parser ─────────────────────────────────────────────────────────────


def _parse_application(lines: list[str], doc: HtmlPatent) -> None:
    i = 0
    cur_inventor: Inventor | None = None
    cur_applicant: Applicant | None = None
    cur_agent: Agent | None = None
    in_selected = False

    while i < len(lines):
        line = lines[i]

        def _field(tag: str) -> re.Match | None:
            return re.match(rf"^【{re.escape(tag)}】\s*(.*)", line)

        def _sub_field(tag: str) -> re.Match | None:
            return re.match(rf"^[　\s]+【{re.escape(tag)}】\s*(.*)", line)

        if m := _field("整理番号"):
            doc.file_reference_id = m.group(1).strip()
        elif m := _field("あて先"):
            doc.addressed_to = m.group(1).strip()
        elif m := _field("国際特許分類"):
            doc.ipc_list.append(m.group(1).rstrip("\r\n"))
        elif _field("発明者"):
            cur_inventor = Inventor()
            doc.inventors.append(cur_inventor)
            cur_applicant = cur_agent = None
        elif _field("特許出願人"):
            cur_applicant = Applicant()
            doc.applicants.append(cur_applicant)
            cur_inventor = cur_agent = None
        elif _field("代理人"):
            cur_agent = Agent()
            doc.agents.append(cur_agent)
            cur_inventor = cur_applicant = None
            in_selected = False
        elif _field("選任した代理人"):
            cur_agent = Agent()
            doc.selected_agents.append(cur_agent)
            cur_inventor = cur_applicant = None
            in_selected = True
        elif m := _sub_field("住所又は居所"):
            addr = m.group(1).strip()
            i += 1
            while i < len(lines) and lines[i] and not re.match(r"^[　\s]*【", lines[i]):
                addr += lines[i].rstrip("\r\n")
                i += 1
            if cur_inventor:
                cur_inventor.address = addr
            continue
        elif m := _sub_field("氏名"):
            if cur_inventor:
                cur_inventor.name = m.group(1).strip()
        elif m := _sub_field("氏名又は名称"):
            if cur_applicant:
                cur_applicant.name = m.group(1).strip()
            elif cur_agent:
                cur_agent.name = m.group(1).strip()
        elif m := _sub_field("識別番号"):
            if cur_applicant:
                cur_applicant.registered_number = m.group(1).strip()
            elif cur_agent:
                cur_agent.registered_number = m.group(1).strip()
        elif m := _field("国等の委託研究の成果に係る記載事項"):
            text = m.group(1).strip()
            i += 1
            while i < len(lines) and lines[i] and not re.match(r"^【", lines[i]):
                text += lines[i].strip()
                i += 1
            doc.law_of_industrial = text
            continue
        elif m := _sub_field("予納台帳番号"):
            doc.fee_account = m.group(1).strip()
        elif m := _sub_field("納付金額"):
            raw = m.group(1).strip().replace(",", "").replace("，", "").replace("円", "")
            try:
                doc.fee_amount = int(raw)
            except ValueError:
                pass
        elif m := re.match(r"^[　\s]+【物件名】\s*(.+?)\s+(\d+)\s*$", line):
            doc.submission_items.append(
                SubmissionItem(doc_name=m.group(1).strip(), count=int(m.group(2)))
            )
        elif m := _sub_field("包括委任状番号"):
            doc.power_of_attorney_ids.append(m.group(1).strip())

        i += 1


# ── 明細書 parser ─────────────────────────────────────────────────────────────


def _parse_description(lines: list[str], doc: HtmlPatent) -> None:
    cur_section: DescSection | None = None
    cur_para: Para | None = None

    for line in lines:
        # paragraph number?
        if m := _PARA_NUM_RE.match(line):
            num = _zfill4(m.group(1))
            cur_para = Para(num=num)
            if cur_section is not None:
                cur_section.paragraphs.append(cur_para)
            continue

        # section header at column 0?
        if m := _SECTION_HDR_RE.match(line):
            header = m.group(1)

            if header.startswith("発明の名称"):
                title = line[len("【発明の名称】"):].strip()
                sec = DescSection(name="発明の名称")
                sec.paragraphs.append(Para(num="", content_lines=[title]))
                doc.desc_sections.append(sec)
                cur_section = None
                cur_para = None
                continue

            # Not a paragraph number, not 書類名 → subsection header
            cur_section = DescSection(name=header)
            doc.desc_sections.append(cur_section)
            cur_para = None
            continue

        # content line
        if cur_para is not None and line:
            cur_para.content_lines.append(line)


# ── 特許請求の範囲 parser ─────────────────────────────────────────────────────


def _parse_claims(lines: list[str], doc: HtmlPatent) -> None:
    cur_lines: list[str] = []
    in_claim = False

    def _flush():
        if cur_lines:
            doc.claim_texts.append(_join_claim_lines(cur_lines))

    for line in lines:
        if m := _CLAIM_NUM_RE.match(line):
            _flush()
            cur_lines = []
            in_claim = True
        elif in_claim:
            cur_lines.append(line)

    _flush()


def _join_claim_lines(lines: list[str]) -> str:
    """Join claim lines: lines starting with 　 are semantic segments joined by <br />;
    lines without leading 　 are continuations joined directly."""
    segments: list[str] = []
    cur = ""
    for line in lines:
        if not line:
            continue
        if line.startswith("　") or line.startswith(" "):
            if cur:
                segments.append(cur)
            cur = line
        else:
            cur += line  # continuation: join without separator
    if cur:
        segments.append(cur)

    if len(segments) <= 1:
        return segments[0] if segments else ""
    return "<br />\n".join(segments)


# ── 要約書 parser ─────────────────────────────────────────────────────────────


def _parse_abstract(lines: list[str], doc: HtmlPatent) -> None:
    """Each 【...】 line starts a new item; continuation lines are joined."""
    cur_item: str | None = None

    for line in lines:
        if not line:
            continue
        if line.startswith("【"):
            if cur_item is not None:
                doc.abstract_items.append(cur_item)
            cur_item = line
        else:
            if cur_item is not None:
                cur_item += line  # join continuation
            else:
                cur_item = line

    if cur_item is not None:
        doc.abstract_items.append(cur_item)


# ── 図面 parser ───────────────────────────────────────────────────────────────


def _parse_drawings(lines: list[str], doc: HtmlPatent) -> None:
    cur_num: int | None = None

    for line in lines:
        if m := _FIGURE_HEADER_RE.match(line):
            cur_num = int(_to_ascii(m.group(1)))
            continue

        if cur_num is not None:
            if img_m := _IMG_RE.search(line):
                src = img_m.group(1)
                w_m = _WIDTH_RE.search(line)
                h_m = _HEIGHT_RE.search(line)
                width = int(w_m.group(1)) if w_m else 0
                height = int(h_m.group(1)) if h_m else 0
                doc.figures.append(Figure(num=cur_num, src=src, width=width, height=height))
                cur_num = None
