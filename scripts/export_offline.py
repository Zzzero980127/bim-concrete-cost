"""
產生可以直接雙擊開啟的離線版儀表板（單一 HTML 檔，不需要伺服器、不需要網路）。

做法：把 data.json、Tailwind、Chart.js、Font Awesome 圖示全部嵌進 index.html。
用法：python scripts/export_offline.py
輸出：專題資料夾裡的「BIM混凝土成本儀表板_離線版_<日期>.html」
"""

import base64
import json
import os
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TAILWIND_URL = "https://cdn.tailwindcss.com"
CHARTJS_URL = "https://cdn.jsdelivr.net/npm/chart.js"
FA_BASE = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0"


def download(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (bim-concrete-cost)"})
    with urllib.request.urlopen(req, timeout=60) as res:
        return res.read()


def inline_font_awesome():
    css = download(f"{FA_BASE}/css/all.min.css").decode("utf-8")

    def embed(match):
        name = match.group(1)
        if not name.endswith(".woff2"):
            return "url(data:,)"  # 只嵌 woff2，其他格式瀏覽器用不到
        font = base64.b64encode(download(f"{FA_BASE}/webfonts/{name}")).decode()
        return f"url(data:font/woff2;base64,{font})"

    return re.sub(r"url\(\.\./webfonts/([^)?#]+)[^)]*\)", embed, css)


def main():
    with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f:
        html = f.read()
    with open(os.path.join(ROOT, "data.json"), encoding="utf-8") as f:
        data = json.load(f)

    def script(code):
        return "<script>" + code.replace("</script", "<\\/script") + "</script>"

    replacements = {
        f'<script src="{TAILWIND_URL}"></script>': script(download(TAILWIND_URL).decode("utf-8")),
        f'<script src="{CHARTJS_URL}"></script>': script(download(CHARTJS_URL).decode("utf-8")),
        f'<link rel="stylesheet" href="{FA_BASE}/css/all.min.css">': "<style>" + inline_font_awesome() + "</style>",
    }
    for old, new in replacements.items():
        if old not in html:
            raise ValueError(f"index.html 裡找不到：{old}")
        html = html.replace(old, new)

    # 資料放在所有程式之前，頁面就不會去 fetch data.json
    embedded = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = html.replace("</head>", f"<script>window.EMBEDDED_DATA = {embedded};</script>\n</head>", 1)

    out = os.path.join(ROOT, f"BIM混凝土成本儀表板_離線版_{data['generated_at'][:10]}.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"已產生 {os.path.basename(out)}（{os.path.getsize(out) / 1024:,.0f} KB）")


if __name__ == "__main__":
    main()
