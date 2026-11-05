"""Streamlit UI: upload an SPL label + spec, see findings, download reports.

Run: streamlit run src/specheck/app.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from specheck.engine import has_errors, run
from specheck.parser import parse_spl
from specheck.report import to_html, to_json
from specheck.rules import SpecError, load_spec

BUNDLED = Path(__file__).parent / "specs" / "plr_label_v1.yaml"
COLORS = {"pass": "#e8f6ec", "fail": "#fde8e8", "skip": "#f0f0f0"}


def _tmp(data: bytes, suffix: str) -> Path:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(data)
    return Path(f.name)


def main() -> None:
    st.set_page_config(page_title="specheck", layout="wide")
    st.title("specheck")
    st.caption("Verify an FDA SPL drug label against a machine-readable spec.")

    with st.sidebar:
        st.header("Spec")
        up_spec = st.file_uploader("Custom spec (YAML)", type=["yaml", "yml"])
        st.caption("Default: bundled `plr_label_v1`")
        st.warning("Not validated GxP software. Structural checks only.", icon="⚠️")

    up_label = st.file_uploader("SPL label (XML)", type=["xml"])
    if not up_label:
        st.info("Upload a label to begin. Real labels: dailymed.nlm.nih.gov")
        return

    try:
        spec_path = _tmp(up_spec.getvalue(), ".yaml") if up_spec else BUNDLED
        spec = load_spec(spec_path)
    except (SpecError, Exception) as e:  # noqa: BLE001 (surface any spec problem to the user)
        st.error(f"Spec error: {e}")
        return
    try:
        label = parse_spl(_tmp(up_label.getvalue(), ".xml"))
    except Exception as e:  # noqa: BLE001
        st.error(f"Could not parse label XML: {e}")
        return
    label.path = up_label.name

    findings = run(spec, label)
    failed = [f for f in findings if f.status == "fail"]
    errors = [f for f in failed if f.severity == "error"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Verdict", "FAIL" if has_errors(findings) else "PASS")
    c2.metric("Errors", len(errors))
    c3.metric("Warnings/info", len(failed) - len(errors))
    c4.metric("Rules run", len(findings))
    st.write(
        f"**setId** `{label.set_id}` · **version** {label.version} · "
        f"**effective** {label.effective_time} · **sections** {len(label.sections)}"
    )

    only_fail = st.toggle("Show only failures", value=False)
    rows = [
        {
            "Rule": f.rule_id,
            "Status": f.status,
            "Severity": f.severity,
            "Message": f.message,
            "Evidence": f.evidence,
            "Reference": f.reference,
        }
        for f in findings
        if not only_fail or f.status == "fail"
    ]
    df = pd.DataFrame(rows)
    st.dataframe(
        df.style.apply(
            lambda r: [f"background-color: {COLORS.get(r['Status'], '')}; color: #111"] * len(r),
            axis=1,
        ),
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("Parsed sections"):
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "#": s.order,
                        "depth": s.depth,
                        "code": s.code,
                        "title": s.title,
                        "chars": len(s.full_text),
                    }
                    for s in label.sections
                ]
            ),
            hide_index=True,
        )

    d1, d2 = st.columns(2)
    d1.download_button(
        "Download HTML report", to_html(spec, label, findings), "specheck_report.html", "text/html"
    )
    d2.download_button(
        "Download JSON report",
        to_json(spec, label, findings),
        "specheck_report.json",
        "application/json",
    )


main()
