"""Parse an SPL (Structured Product Labeling) XML document into a simple model."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

NS = {"h": "urn:hl7-org:v3"}


@dataclass
class Section:
    code: str
    title: str
    text: str  # the section's own text
    full_text: str  # own text plus all nested subsections
    order: int  # document order, 0-based, across all nesting levels
    depth: int
    xpath: str


@dataclass
class Label:
    path: str
    set_id: str | None
    version: str | None
    effective_time: str | None
    doc_type_code: str | None
    sections: list[Section] = field(default_factory=list)
    fields: dict[str, str | None] = field(default_factory=dict)

    def find(self, code: str | list[str]) -> list[Section]:
        """Sections matching a LOINC code, or any code in a list (alternatives)."""
        codes = {code} if isinstance(code, str) else set(code)
        return [s for s in self.sections if s.code in codes]


def _attr(root, xp: str) -> str | None:
    r = root.xpath(xp, namespaces=NS)
    return r[0] if r else None


def parse_spl(path: str | Path) -> Label:
    # resolve_entities/no_network: label files are untrusted input.
    parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False)
    tree = etree.parse(str(path), parser)
    root = tree.getroot()
    label = Label(
        path=str(path),
        set_id=_attr(root, "h:setId/@root"),
        version=_attr(root, "h:versionNumber/@value"),
        effective_time=_attr(root, "h:effectiveTime/@value"),
        doc_type_code=_attr(root, "h:code/@code"),
    )
    label.fields = {
        "setId": label.set_id,
        "versionNumber": label.version,
        "effectiveTime": label.effective_time,
        "documentCode": label.doc_type_code,
        "ndc": _attr(root, "//h:code[@codeSystem='2.16.840.1.113883.6.69']/@code"),
    }
    for i, sec in enumerate(root.iterfind(".//h:section", NS)):
        code = sec.find("h:code", NS)
        title = sec.find("h:title", NS)
        text = sec.find("h:text", NS)
        depth = len(list(sec.iterancestors("{urn:hl7-org:v3}section")))
        label.sections.append(
            Section(
                code=code.get("code") if code is not None else "",
                title=" ".join(" ".join(title.itertext()).split()) if title is not None else "",
                text=" ".join(" ".join(text.itertext()).split()) if text is not None else "",
                full_text=" ".join(
                    " ".join(" ".join(t.itertext()).split()) for t in sec.iterfind(".//h:text", NS)
                ).strip(),
                order=i,
                depth=depth,
                xpath=tree.getpath(sec),
            )
        )
    return label
