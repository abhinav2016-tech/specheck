from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .engine import Finding
from .parser import Label
from .rules import Spec


def to_json(spec: Spec, label: Label, findings: list[Finding]) -> str:
    return json.dumps(
        {
            "spec": {"name": spec.name, "version": spec.version},
            "document": {"path": label.path, "setId": label.set_id, "version": label.version},
            "summary": {
                "total": len(findings),
                "failed": sum(f.status == "fail" for f in findings),
            },
            "findings": [asdict(f) for f in findings],
        },
        indent=2,
    )


def to_html(spec: Spec, label: Label, findings: list[Finding]) -> str:
    env = Environment(
        loader=FileSystemLoader(Path(__file__).parent / "templates"),
        autoescape=select_autoescape(["html"]),
    )
    return env.get_template("report.html").render(spec=spec, label=label, findings=findings)
