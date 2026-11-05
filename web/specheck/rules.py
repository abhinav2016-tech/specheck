"""Spec loading and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

RULE_TYPES = {
    "section_present",
    "section_order",
    "field_present",
    "regex_in_section",
    "text_not_empty",
}
SEVERITIES = {"error", "warning", "info"}
REQUIRED_KEYS = {
    "section_present": ["code"],
    "section_order": ["codes"],
    "field_present": ["field"],
    "regex_in_section": ["code", "pattern"],
    "text_not_empty": ["code"],
}


class SpecError(ValueError):
    pass


@dataclass
class Rule:
    id: str
    type: str
    severity: str
    message: str
    reference: str = ""
    applies_if_section: list[str] | str | None = None  # skip rule unless this section code exists
    params: dict = field(default_factory=dict)


@dataclass
class Spec:
    name: str
    version: str
    rules: list[Rule]


def load_spec(path: str | Path) -> Spec:
    data = yaml.safe_load(Path(path).read_text())
    if not isinstance(data, dict) or "rules" not in data:
        raise SpecError("spec must be a mapping with a 'rules' list")
    rules, seen = [], set()
    for raw in data["rules"]:
        raw = dict(raw)
        rid, rtype = raw.pop("id", None), raw.pop("type", None)
        if not rid or rid in seen:
            raise SpecError(f"missing or duplicate rule id: {rid!r}")
        seen.add(rid)
        if rtype not in RULE_TYPES:
            raise SpecError(f"{rid}: unknown rule type {rtype!r}")
        sev = raw.pop("severity", "error")
        if sev not in SEVERITIES:
            raise SpecError(f"{rid}: bad severity {sev!r}")
        msg = raw.pop("message", rid)
        ref = raw.pop("reference", "")
        cond = raw.pop("applies_if_section", None)
        for k in REQUIRED_KEYS[rtype]:
            if k not in raw:
                raise SpecError(f"{rid}: rule type {rtype} requires '{k}'")
        rules.append(Rule(rid, rtype, sev, msg, ref, cond, raw))
    return Spec(str(data.get("spec", "unnamed")), str(data.get("version", "0")), rules)
