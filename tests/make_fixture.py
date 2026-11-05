"""Builds SYNTHETIC minimal SPL-shaped XML for unit tests. Not real label data."""

SECTIONS = [
    ("34067-9", "INDICATIONS AND USAGE", "Drug X is indicated for condition Y."),
    ("34068-7", "DOSAGE AND ADMINISTRATION", "Take 10 mg once daily."),
    ("34070-3", "CONTRAINDICATIONS", "Hypersensitivity."),
    ("43685-7", "WARNINGS AND PRECAUTIONS", "Monitor liver function."),
    ("34084-4", "ADVERSE REACTIONS", "Nausea, headache."),
]


def build(
    sections=SECTIONS, set_id="11111111-2222-3333-4444-555555555555", version="1", eff="20240101"
):
    parts = "".join(
        f'<component><section><code code="{c}" codeSystem="2.16.840.1.113883.6.1"/>'
        f"<title>{t}</title><text><paragraph>{x}</paragraph></text></section></component>"
        for c, t, x in sections
    )
    sid = f'<setId root="{set_id}"/>' if set_id else ""
    ver = f'<versionNumber value="{version}"/>' if version else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?><document xmlns="urn:hl7-org:v3">'
        '<code code="34391-3" codeSystem="2.16.840.1.113883.6.1"/>'
        f'{sid}<effectiveTime value="{eff}"/>{ver}'
        f"<component><structuredBody>{parts}</structuredBody></component></document>"
    )
