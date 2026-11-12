# 天使遊戲資料更新

每次遊戲改版後，整理資源檔裡物品、兌換、裝扮等資料的變動。
網站由 GitHub Pages 發布，新版本推上來後自動在 Discord 公告。

## 結構

| 路徑 | 內容 |
|---|---|
| `updates.json` | 版本清單（標題、摘要、重點、圖卡），新到舊 |
| `versions/<版本>/report.md` | 差異報告 |
| `versions/<版本>/cards/*.png` | 分類圖卡 |
| `versions/<版本>/items.html` | 物品圖鑑（圖示內嵌） |
| `site/build.py`、`site/style.css` | 建成靜態網站 |
| `.github/workflows/publish.yml` | push 到 main → 建置 → 部署 Pages → 公告 |
| `.github/scripts/announce.py` | 發 Discord webhook |

## 公告規則

- 這次 push 的 `updates.json` 比上一個 commit **多出來的版本**才發，一個版本一則。
- 改舊報告、改樣式不會重發。
- 第一次 push 不會自動發。要發（或重發）某版：Actions → 發布網站與公告 → Run workflow，填版本號。
- 沒設 `DISCORD_WEBHOOK_URL` secret 時只部署、不發。

## 本機預覽

```bash
pip install markdown
python site/build.py
python -m http.server -d _site 8000
```

看公告內容但不送出：

```bash
DRY_RUN=1 ANNOUNCE_VERSION=0.1.0.9 SITE_URL=https://example.github.io/repo python .github/scripts/announce.py
```
