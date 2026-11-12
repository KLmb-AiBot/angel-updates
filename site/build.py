"""把 updates.json + versions/ 建成靜態網站（輸出到 --out，預設 _site/）。

需要：pip install markdown
本機預覽：python site/build.py && python -m http.server -d _site 8000
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SITE_NAME = "天使遊戲資料更新"


def page(title: str, body: str, depth: int) -> str:
    up = "../" * depth
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{up}style.css">
</head>
<body>
<header class="top"><a href="{up}index.html">{SITE_NAME}</a></header>
<main>
{body}
</main>
<footer>只整理遊戲公開資源檔的內容差異，不代表官方公告。</footer>
</body>
</html>
"""


def inline_md(text: str) -> str:
    """一段文字（摘要）轉成行內 HTML，不包 <p>。"""
    out = markdown.markdown(text)
    return out[3:-4] if out.startswith("<p>") and out.endswith("</p>") else out


def render_md(text: str) -> str:
    text = re.sub(r"\A#\s+.+\n", "", text)  # 標題由頁面自己顯示
    out = markdown.markdown(text, extensions=["tables", "sane_lists"])
    return out.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")


def version_page(e: dict) -> str:
    v = html.escape(e["version"])
    links = []
    if e.get("items"):
        links.append('<a class="btn" href="items.html">物品圖鑑（含圖示）</a>')
    if e.get("cards"):
        links.append('<a class="btn" href="#cards">分類圖卡</a>')
    body = [
        f'<p class="meta">{html.escape(e.get("from", ""))} → {v} · {html.escape(e["date"])}</p>',
        f"<h1>{html.escape(e['title'])}</h1>",
    ]
    if e.get("summary"):
        body.append(f'<p class="summary">{inline_md(e["summary"])}</p>')
    if links:
        body.append(f'<nav class="links">{"".join(links)}</nav>')
    md = (ROOT / "versions" / e["version"] / "report.md").read_text(encoding="utf-8")
    body.append(f'<article class="report">{render_md(md)}</article>')
    if e.get("cards"):
        figs = "".join(
            f'<figure><a href="{html.escape(c["file"])}"><img src="{html.escape(c["file"])}" '
            f'alt="{html.escape(c["title"])}" loading="lazy"></a><figcaption>{html.escape(c["title"])}</figcaption></figure>'
            for c in e["cards"]
        )
        body.append(f'<section id="cards"><h2>分類圖卡</h2><div class="cards">{figs}</div></section>')
    return page(f"{e['title']} · {SITE_NAME}", "\n".join(body), depth=2)


def index_page(entries: list[dict]) -> str:
    items = []
    for e in entries:
        hl = "".join(f"<li>{html.escape(h)}</li>" for h in e.get("highlights", [])[:6])
        summary = f"<p>{inline_md(e['summary'])}</p>" if e.get("summary") else ""
        items.append(
            f'<li class="entry"><a href="v/{html.escape(e["version"])}/index.html">'
            f'<span class="meta">{html.escape(e["date"])} · {html.escape(e.get("from", ""))} → {html.escape(e["version"])}</span>'
            f'<h2>{html.escape(e["title"])}</h2></a>{summary}{f"<ul>{hl}</ul>" if hl else ""}</li>'
        )
    body = (
        f"<h1>{SITE_NAME}</h1>\n"
        '<p class="lead">每次遊戲改版後，整理資源檔裡物品、兌換、裝扮等資料的變動。</p>\n'
        f'<ol class="list">{"".join(items)}</ol>'
    )
    return page(SITE_NAME, body, depth=0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "_site")
    args = ap.parse_args()
    entries = json.loads((ROOT / "updates.json").read_text(encoding="utf-8"))
    out: Path = args.out
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copy2(ROOT / "site" / "style.css", out / "style.css")
    shutil.copy2(ROOT / "updates.json", out / "updates.json")
    (out / ".nojekyll").write_text("")
    (out / "index.html").write_text(index_page(entries), encoding="utf-8")
    for e in entries:
        src = ROOT / "versions" / e["version"]
        dst = out / "v" / e["version"]
        dst.mkdir(parents=True)
        if (src / "cards").is_dir():
            shutil.copytree(src / "cards", dst / "cards")
        if (src / "items.html").exists():
            shutil.copy2(src / "items.html", dst / "items.html")
        (dst / "index.html").write_text(version_page(e), encoding="utf-8")
    print(f"建好 {len(entries)} 個版本 → {out}")


if __name__ == "__main__":
    main()
