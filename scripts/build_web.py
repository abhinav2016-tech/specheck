"""Copy the pure-Python engine into web/ so the static page can load it into Pyodide."""

import json
import pathlib
import shutil

root = pathlib.Path(__file__).resolve().parent.parent
src, dst = root / "src" / "specheck", root / "web" / "specheck"
shutil.rmtree(dst, ignore_errors=True)
(dst / "templates").mkdir(parents=True)
(dst / "specs").mkdir()
files = ["__init__.py", "parser.py", "rules.py", "engine.py", "report.py"]
for f in files:
    shutil.copy(src / f, dst / f)
shutil.copy(src / "templates" / "report.html", dst / "templates" / "report.html")
shutil.copy(root / "specs" / "plr_label_v1.yaml", dst / "specs" / "plr_label_v1.yaml")
manifest = files + ["templates/report.html", "specs/plr_label_v1.yaml"]
(dst / "manifest.json").write_text(json.dumps(manifest))
print("built", len(manifest), "files")
