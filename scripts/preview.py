#!/usr/bin/env python3
"""Docs preview for the Space-Thriving-Manual.

This repository is a Markdown "manual" with no compiled application. The closest
thing to "running the app" is browsing the manual, so this script renders every
Markdown file into a small browsable static site and can serve it locally.

Usage:
    python3 scripts/preview.py            # build the static site into ./_preview
    python3 scripts/preview.py --serve    # build, then serve on http://localhost:8099
    python3 scripts/preview.py --serve --port 9000 --host 0.0.0.0

Requires the `markdown` package (see .cursor/environment.json install step):
    pip3 install --user markdown
"""
from __future__ import annotations

import argparse
import functools
import http.server
import shutil
import socketserver
from pathlib import Path

import markdown

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "_preview"

CSS = """
body{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
max-width:820px;margin:0 auto;padding:2rem 1.5rem;line-height:1.6;
background:#0b1020;color:#e6ebff}
a{color:#8ab4ff}h1,h2,h3{color:#cdd7ff}
.card{background:#141b33;border:1px solid #24305a;border-radius:12px;
padding:1rem 1.25rem;margin:.75rem 0}
code,pre{background:#0f1730;border-radius:6px;padding:.1rem .3rem}
.nav{display:flex;flex-wrap:wrap;gap:.5rem;margin-bottom:1.5rem}
.nav a{background:#1c264a;padding:.35rem .7rem;border-radius:20px;text-decoration:none}
.crumbs{color:#7f8bb5;font-size:.9rem;margin-bottom:1rem}
img{max-width:100%;border-radius:10px}
"""


def find_markdown() -> list[Path]:
    files = []
    for path in sorted(REPO.rglob("*.md")):
        parts = set(path.parts)
        if ".git" in parts or "_preview" in parts:
            continue
        files.append(path)
    return files


def out_name(rel: Path) -> str:
    return str(rel).replace("/", "__").replace(".md", ".html")


def build() -> Path:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    (OUT / "style.css").write_text(CSS)

    files = find_markdown()
    md = markdown.Markdown(extensions=["fenced_code", "tables", "toc"])

    links = [(str(p.relative_to(REPO)), out_name(p.relative_to(REPO))) for p in files]
    nav = '<div class="nav">' + "".join(
        f'<a href="{out}">{name}</a>' for name, out in links
    ) + "</div>"

    for path in files:
        rel = path.relative_to(REPO)
        md.reset()
        body = md.convert(path.read_text())
        (OUT / out_name(rel)).write_text(
            f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{rel}</title><link rel="stylesheet" href="style.css"></head>
<body><a href="index.html">&larr; Manual Index</a>
<div class="crumbs">{rel}</div>{nav}
<div class="card">{body}</div></body></html>"""
        )

    cards = "".join(
        f'<div class="card"><a href="{out}"><b>{name}</b></a></div>'
        for name, out in links
    )
    (OUT / "index.html").write_text(
        f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Space-Thriving-Manual</title><link rel="stylesheet" href="style.css"></head>
<body><h1>Space-Thriving-Manual &mdash; Docs Preview</h1>
<p>Rendered {len(files)} Markdown documents from the repository.</p>
{nav}{cards}</body></html>"""
    )

    print(f"Rendered {len(files)} documents to {OUT}")
    return OUT


def serve(host: str, port: int) -> None:
    directory = str(build())
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=directory)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer((host, port), handler) as httpd:
        print(f"Serving docs preview at http://{host}:{port}/ (Ctrl+C to stop)")
        httpd.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build/serve the Space-Thriving-Manual docs preview.")
    parser.add_argument("--serve", action="store_true", help="serve the site after building")
    parser.add_argument("--host", default="127.0.0.1", help="host to bind when serving")
    parser.add_argument("--port", type=int, default=8099, help="port to bind when serving")
    args = parser.parse_args()

    if args.serve:
        serve(args.host, args.port)
    else:
        build()


if __name__ == "__main__":
    main()
