"""Rule evaluation."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .parser import Label
from .rules import Rule, Spec


@dataclass
class Finding:
    rule_id: str
    status: str  # pass | fail
    severity: str
    message: str
    reference: str
    evidence: str = ""
    location: str = ""


def _check(rule: Rule, label: Label) -> tuple[bool, str, str]:
    p = rule.params
    if rule.type == "section_present":
        found = label.find(p["code"])
        return (
            bool(found),
            f"{len(found)} section(s) with code {p['code']}",
            found[0].xpath if found else "",
        )
    if rule.type == "text_not_empty":
        found = label.find(p["code"])
        if not found:
            return False, f"section {p['code']} missing", ""
        ok = any(s.full_text for s in found)
        return ok, f"{sum(len(s.full_text) for s in found)} chars of text", found[0].xpath
    if rule.type == "field_present":
        v = label.fields.get(p["field"])
        return bool(v), f"{p['field']}={v!r}", ""
    if rule.type == "section_order":
        pos = []
        for c in p["codes"]:
            f = label.find(c)
            if not f:
                return False, f"section {c} missing, order undecidable", ""
            pos.append(f[0].order)
        return pos == sorted(pos), f"document positions {pos} for {p['codes']}", ""
    if rule.type == "regex_in_section":
        found = label.find(p["code"])
        if not found:
            return False, f"section {p['code']} missing", ""
        rx = re.compile(p["pattern"], re.IGNORECASE)
        m = next((rx.search(s.full_text) for s in found if rx.search(s.full_text)), None)
        negate = p.get("must_not_match", False)
        ok = (m is None) if negate else (m is not None)
        return ok, f"match={m.group(0)!r}" if m else "no match", found[0].xpath
    raise ValueError(rule.type)


def run(spec: Spec, label: Label) -> list[Finding]:
    out = []
    for r in spec.rules:
        if r.applies_if_section and not label.find(r.applies_if_section):
            out.append(
                Finding(r.id, "skip", r.severity, r.message, r.reference, "precondition not met")
            )
            continue
        ok, evidence, loc = _check(r, label)
        out.append(
            Finding(
                r.id, "pass" if ok else "fail", r.severity, r.message, r.reference, evidence, loc
            )
        )
    return out


def has_errors(findings: list[Finding]) -> bool:
    return any(f.status == "fail" and f.severity == "error" for f in findings)
