from pathlib import Path

import pytest
from make_fixture import SECTIONS, build
from typer.testing import CliRunner

from specheck.cli import app
from specheck.engine import has_errors, run
from specheck.parser import parse_spl
from specheck.rules import SpecError, load_spec

SPEC = Path(__file__).parent.parent / "specs" / "plr_label_v1.yaml"


def write(tmp_path, xml):
    p = tmp_path / "label.xml"
    p.write_text(xml)
    return p


def fails(tmp_path, xml):
    return {
        f.rule_id
        for f in run(load_spec(SPEC), parse_spl(write(tmp_path, xml)))
        if f.status == "fail"
    }


def test_good_label_has_no_errors(tmp_path):
    f = run(load_spec(SPEC), parse_spl(write(tmp_path, build())))
    assert not has_errors(f)
    assert {x.rule_id for x in f if x.status == "fail"} == {"SEC-006"}  # warning only


def test_missing_section_detected(tmp_path):
    xml = build([s for s in SECTIONS if s[0] != "34070-3"])
    assert {"SEC-003", "ORD-001"} <= fails(tmp_path, xml)


def test_wrong_order_detected(tmp_path):
    xml = build(list(reversed(SECTIONS)))
    assert "ORD-001" in fails(tmp_path, xml)


def test_missing_header_fields(tmp_path):
    assert {"FLD-001", "FLD-002"} <= fails(tmp_path, build(set_id="", version=""))


def test_dose_without_unit_warns(tmp_path):
    secs = [(c, t, "Take as directed." if c == "34068-7" else x) for c, t, x in SECTIONS]
    assert "DOS-001" in fails(tmp_path, build(secs))


def test_empty_dosage_text(tmp_path):
    secs = [(c, t, "" if c == "34068-7" else x) for c, t, x in SECTIONS]
    assert "TXT-001" in fails(tmp_path, build(secs))


def test_xxe_not_resolved(tmp_path):
    evil = build().replace("?>", '?><!DOCTYPE d [<!ENTITY x SYSTEM "file:///etc/passwd">]>', 1)
    evil = evil.replace("Drug X is", "&x; is")
    label = parse_spl(write(tmp_path, evil))
    assert "root:" not in " ".join(s.text for s in label.sections)


def test_bad_spec_rejected(tmp_path):
    p = tmp_path / "s.yaml"
    p.write_text("rules:\n  - {id: A, type: nope}\n")
    with pytest.raises(SpecError):
        load_spec(p)


def test_cli_exit_codes_and_reports(tmp_path):
    r = CliRunner()
    good = write(tmp_path, build())
    out = tmp_path / "r.html"
    res = r.invoke(app, ["check", str(good), "-s", str(SPEC), "-o", str(out)])
    assert res.exit_code == 0 and "<table>" in out.read_text()
    bad = write(tmp_path, build(list(reversed(SECTIONS))))
    res = r.invoke(app, ["check", str(bad), "-s", str(SPEC), "-o", str(tmp_path / "r.json")])
    assert res.exit_code == 1


def test_alternative_codes_accept_non_plr_warnings(tmp_path):
    secs = [
        (("34071-9" if False else "34071-1") if c == "43685-7" else c, t, x) for c, t, x in SECTIONS
    ]
    assert not fails(tmp_path, build(secs)) - {"SEC-006"}


def test_dosage_text_in_nested_subsection_counts(tmp_path):
    xml = build()
    nested = (
        '<component><section><code code="34068-7"/><title>DOSAGE</title><text/>'
        '<component><section><code code="42229-5"/><text>Take 5 mg daily.</text></section></component>'
        "</section></component>"
    )
    old = '<component><section><code code="34068-7" codeSystem="2.16.840.1.113883.6.1"/><title>DOSAGE AND ADMINISTRATION</title><text><paragraph>Take 10 mg once daily.</paragraph></text></section></component>'
    assert old in xml
    f = fails(tmp_path, xml.replace(old, nested))
    assert "TXT-001" not in f and "DOS-001" not in f


def test_order_rule_skipped_for_non_plr(tmp_path):
    secs = [("34071-1" if c == "43685-7" else c, t, x) for c, t, x in reversed(SECTIONS)]
    findings = run(load_spec(SPEC), parse_spl(write(tmp_path, build(secs))))
    assert next(f for f in findings if f.rule_id == "ORD-001").status == "skip"


def test_ui_end_to_end(tmp_path):
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(Path(__file__).parent.parent / "src" / "specheck" / "app.py"))
    at.run(timeout=30)
    assert not at.exception and at.info  # prompts for upload
