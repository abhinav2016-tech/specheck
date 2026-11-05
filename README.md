# specheck

Rule-based verification of pharma documentation (FDA SPL drug labels) against a machine-readable spec.

```bash
pip install -e ".[dev]"
specheck check label.xml --spec specs/plr_label_v1.yaml --out report.html
pytest
```

Exit code is 1 if any `error`-severity rule fails, so it drops into CI.

## Web app
`web/` is a static page that runs the same Python engine in-browser via Pyodide (no server;
labels never leave the machine). Local: `python scripts/build_web.py && python -m http.server -d web`.
Deployed on GitHub Pages and Vercel. A Streamlit version lives in `src/specheck/app.py`
(`pip install -e ".[ui]" && streamlit run src/specheck/app.py`); Streamlit cannot run on Vercel.

## Writing rules
`specs/plr_label_v1.yaml`. Types: `section_present`, `section_order`, `field_present`,
`regex_in_section`, `text_not_empty`. Each rule has `id`, `severity` (error|warning|info),
`message`, and an optional `reference` to the regulation it encodes.

## Real data
`python scripts/fetch_dailymed.py --drug metformin --n 10` downloads labels to `data/raw/`.
Sources: DailyMed, openFDA, CDISC pilot data (see docs).

## Limitations
- Not validated GxP/CSV software; makes no 21 CFR Part 11 claims.
- Checks structure and rules, not scientific or clinical correctness.
- The starter spec's LOINC codes and CFR citations must be verified against real labels before use.
- Unit-test fixtures are synthetic, not real label data.
