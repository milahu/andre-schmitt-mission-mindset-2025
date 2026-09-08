#!/usr/bin/env python3

import glob
import os
import re
import shutil
import subprocess
import sys
import zipfile
import shlex
from datetime import datetime
from pathlib import Path

from _shared import (
    load_config,
    get_page_num,
)


src = Path("090-ocr")

# write EPUB file
# dst = Path(Path(__file__).stem + ".epub")

# write unpacked EPUB files to workdir
dst = Path(".")


config = load_config()


if dst != Path(".") and dst.exists():
    print(f"error: output exists: {dst}")
    sys.exit(1)


# downscale to 300 dpi
# 600 dpi -> 300 dpi: 90 MB -> 60 MB
scale = 300 / config.scan_resolution


hocr_to_epub_fxl = "hocr-to-epub-fxl"

# TODO dont commit
if 1:
    hocr_to_epub_fxl = "/home/user/src/archive-hocr-tools/bin/hocr-to-epub-fxl"

args = [
    hocr_to_epub_fxl,
    "--output", str(dst),
]

if dst == Path("."):
    args.append("--output-unpacked")


def git_modified():
    return subprocess.check_output(
        ["git", "show", "-s", "--format=%cI", "HEAD"],
        text=True,
    ).strip()


def stat_modified(path):
    ts = Path(path).stat().st_mtime
    dt = datetime.fromtimestamp(ts).astimezone()
    return dt.isoformat(timespec="seconds")


doc_modified = max(
    git_modified(),
    stat_modified(src),
)


args += [
    "--scale", str(scale),
    "--image-format", "avif",
    "--text-format", "html",
    # TODO? move these config items to 000-config.py
    "--doc-modified", doc_modified,
    "--doc-title", "Mission Mindset",
    "--doc-subtitle", "Dein Praxisbuch für klare Führung in unsicheren Zeiten: Als Führungskraft souverän handeln und entscheiden – mit dem Mindset und den Strategien von Eliteeinheiten",
    # "--doc-subject", "",
    "--doc-date", "2025-08-21",
    "--doc-edition", "1",
    "--doc-extent", "292 pages",
    "--color-image-pages", "295,296",
    "--doc-author", "André Schmitt",
    # "--doc-introducer", "",
    # "--doc-contributor", "",
    # "--doc-translator", "",
    "--doc-publisher", "Kniga Verlag",
    "--doc-language", "de", # german
    # "--doc-language", "en", # english
    "--doc-isbn", "9783910385641",
    "--doc-cover-image", "072-deskew-fix-page-size/295.tiff",
    "--canonical-url-base", "https://milahu.github.io/andre-schmitt-mission-mindset-2025/",
    "--doc-description", """
**Wie du als Führungskraft fokussierte Entscheidungen triffst, mentale Stärke entwickelst und mit dem Mindset der Elite auch in Krisen klar bleibst**

Fühlst du dich in deiner Führungsrolle manchmal überfordert –
als müsstest du jederzeit funktionieren, entscheiden, motivieren, während innerlich der Druck steigt?
Fehlt dir in turbulenten Zeiten die Klarheit, um fokussiert und ruhig zu bleiben?

Hast du das Gefühl, deinen Ansprüchen nicht gerecht zu werden,
weil du zwischen Verantwortung, Erwartungen und Unsicherheiten zerrieben wirst?

Wünschst du dir mehr Resilienz, innere Stärke
und einen klaren Kompass, der dich auch in chaotischen Situationen sicher navigiert?

Dann aufgepasst:

Wenn du als Führungskraft nach Strategien suchst,
um auch in unsicheren Zeiten kraftvoll,
authentisch und klar zu führen – ohne dich zu verbiegen oder auszubrennen, …

… dann ist dieses Buch dein Wegweiser für mehr mentale Stärke,
Fokus und souveränes Handeln im Alltag.

In *„Mission Mindset: Dein Praxisbuch für klare Führung in unsicheren Zeiten“* zeigt dir der Autor
– selbst erfahrener Kommandosoldat, Krisenexperte und Unternehmer –
wie du mit dem Wissen und den Prinzipien aus Spezialeinheiten dein persönliches Führungs-Mindset stärkst und dich auf jedem Terrain behauptest.

In diesem kraftvollen Praxisbuch lernst du:

- Wie du selbst in Stresssituationen souverän entscheidest und handlungsfähig bleibst – auch wenn andere längst im Alarmmodus sind.
- Was starke Führung wirklich(!) ausmacht – und wie du mit Klarheit, Haltung und Empathie dein Team sicher durch Veränderungen führst.
- Wie du Rückschläge, Unsicherheiten und Druck mental verarbeitest und in Stärke verwandelst – ohne dich selbst zu verlieren.
- Welche mentalen Modelle, Strategien und Reizkontroll-Techniken Spezialeinheiten nutzen – und wie du sie im Business-Alltag effektiv einsetzt.
- Warum Resilienz und emotionale Kontrolle die wahren Erfolgsfaktoren sind – und wie du sie systematisch aufbaust.

Und obendrein profitierst du durch …

… ELITE-MINDSET FÜR DEN FÜHRUNGSALLTAG:
Taktische Klarheit, mentale Werkzeuge und ein unerschütterlicher Fokus –
inspiriert von den Besten, übersetzt für den Führungsalltag.

… AUTHENTISCHE ERFAHRUNG:
Der Autor zeigt offen und ehrlich, wie man durch Widrigkeiten wächst –
und wie echtes Leadership in der Praxis funktioniert, jenseits von Buzzwords.

… STRATEGIEN FÜR SOUVERÄNITÄT IN JEDER LAGE:
Ob Veränderungsprozesse, Teamführung oder persönlicher Umbruch –
dieses Buch liefert konkrete Methoden für Klarheit und Entscheidungsstärke.

Kaum zu glauben? Dann überzeuge dich selbst:

Bist du bereit, deine Führungsrolle neu zu definieren – kraftvoll, klar und resilient?

Dann sichere dir jetzt dein Exemplar von *„Mission Mindset“* –
und lerne, wie du mit innerer Stärke, Fokus und Elite-Strategien zu der Führungskraft wirst, die andere brauchen – gerade in unsicheren Zeiten.
""",
]


print(">", shlex.join(args + sys.argv[1:]) + f" {src}/*.hocr")


hocr_files = list(src.glob("*.hocr"))

hocr_files.sort()

subprocess.run(
    args + sys.argv[1:] + hocr_files,
    check=True,
)


if dst == Path("."):
    print("done ./index.xhtml")
    sys.exit(0)


print(f"done {dst}")


# extract the EPUB content files

# rm -rf $dst.unzip
unzip_dir = Path(str(dst) + ".unzip")
shutil.rmtree(unzip_dir, ignore_errors=True)
unzip_dir.mkdir()


# unzip -q ../$dst
with zipfile.ZipFile(dst) as z:
    z.extractall(unzip_dir)


print(f"done {unzip_dir}/index.html")
