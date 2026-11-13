"""把新版本發到 Discord webhook（只用標準庫）。

環境變數：
  DISCORD_WEBHOOK_URL  webhook 網址（GitHub repo secret）；沒設就跳過不發
  SITE_URL             網站根網址（deploy-pages 給的 page_url）
  BEFORE_SHA           push 前的 commit；全 0 或空 = 第一次推送，不自動發
  ANNOUNCE_VERSION     手動指定要發的版本（workflow_dispatch 用），有值就只發它
  DRY_RUN=1            只印出要送的內容，不送出

新版本的判斷：這次 updates.json 有、BEFORE_SHA 的 updates.json 沒有的版本。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COLOR = 0x2C64A8
DESC_LIMIT = 4096


def load_manifest(ref: str | None) -> list[dict]:
    if ref is None:
        return json.loads((ROOT / "updates.json").read_text(encoding="utf-8"))
    try:
        raw = subprocess.run(
            ["git", "show", f"{ref}:updates.json"], cwd=ROOT, capture_output=True, check=True
        ).stdout.decode("utf-8")
    except subprocess.CalledProcessError:
        return []  # 那個 commit 還沒有 updates.json
    return json.loads(raw)


def pick_versions(current: list[dict]) -> list[dict]:
    manual = os.environ.get("ANNOUNCE_VERSION", "").strip()
    if manual:
        hit = [e for e in current if e["version"] == manual]
        if not hit:
            sys.exit(f"updates.json 裡沒有版本 {manual}")
        return hit
    before = os.environ.get("BEFORE_SHA", "").strip()
    if not before or set(before) == {"0"}:
        print("第一次推送（沒有前一個 commit），不自動公告；要發請用 workflow_dispatch 指定版本。")
        return []
    old = {e["version"] for e in load_manifest(before)}
    new = [e for e in current if e["version"] not in old]
    return list(reversed(new))  # 舊的先發


def build_payload(e: dict, site_url: str) -> dict:
    url = f"{site_url.rstrip('/')}/v/{e['version']}/" if site_url else None
    lines = []
    if e.get("summary"):
        lines.append(e["summary"])
    if e.get("highlights"):
        lines.append("")
        lines += [f"• {h}" for h in e["highlights"][:10]]
    if url:
        label = "完整內容與圖鑑" if e.get("items") else "完整內容"
        lines += ["", f"[{label}]({url})"]
    desc = "\n".join(lines)
    if len(desc) > DESC_LIMIT:
        desc = desc[: DESC_LIMIT - 1] + "…"
    embed = {
        "title": e["title"][:256],
        "description": desc,
        "color": COLOR,
        "footer": {"text": f"{e.get('from', '?')} → {e['version']} · {e['date']}"},
    }
    if url:
        embed["url"] = url
    return {"embeds": [embed], "allowed_mentions": {"parse": []}}


def send(webhook: str, payload: dict) -> None:
    req = urllib.request.Request(
        webhook + ("&" if "?" in webhook else "?") + "wait=true",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            # 預設的 Python-urllib UA 會被 Cloudflare 擋（error 1010）
            "User-Agent": "DiscordBot (https://github.com, 1.0)",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"  已送出（HTTP {r.status}）")
    except urllib.error.HTTPError as err:
        sys.exit(f"Discord 回應 HTTP {err.code}：{err.read().decode('utf-8', 'replace')[:300]}")


def main() -> None:
    versions = pick_versions(load_manifest(None))
    if not versions:
        print("沒有新版本要公告。")
        return
    site_url = os.environ.get("SITE_URL", "")
    webhook = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    dry = os.environ.get("DRY_RUN") == "1"
    if not webhook and not dry:
        print("::warning::沒有設定 DISCORD_WEBHOOK_URL secret，略過公告。")
        return
    for e in versions:
        payload = build_payload(e, site_url)
        print(f"公告 {e['version']}：{e['title']}")
        if dry:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            send(webhook, payload)


if __name__ == "__main__":
    main()
