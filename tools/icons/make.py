#!/usr/bin/env python3
"""畫出兩端的圖示，並放進兩個 app 裡。

看板端：古代的告示牌。鄉民端：一個人站在告示牌前面看（背影，站在偏左）。
圖是用下面的 SVG 畫的，要改圖就改這個檔案再執行一次：

  python3 tools/icons/make.py

需要 Google Chrome（把 SVG 轉成 PNG）和 macOS 內建的 sips（縮小）。
"""

import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

BOARD = '''
<g id="board">
  <ellipse cx="512" cy="832" rx="320" ry="20" fill="#000" opacity="0.12"/>
  <rect x="236" y="350" width="60" height="476" rx="24" fill="#7A4826"/>
  <rect x="728" y="350" width="60" height="476" rx="24" fill="#7A4826"/>
  <rect x="214" y="794" width="104" height="44" rx="22" fill="#5E361C"/>
  <rect x="706" y="794" width="104" height="44" rx="22" fill="#5E361C"/>
  <rect x="258" y="402" width="508" height="332" rx="40" fill="#A0673A"/>
  <rect x="294" y="436" width="436" height="264" rx="20" fill="#FFF7E3"/>
  <rect x="628" y="464" width="48" height="208" rx="24" fill="#2A2A2A"/>
  <rect x="558" y="464" width="32" height="176" rx="16" fill="#444"/>
  <rect x="490" y="464" width="32" height="208" rx="16" fill="#444"/>
  <rect x="422" y="464" width="32" height="124" rx="16" fill="#444"/>
  <rect x="330" y="594" width="80" height="80" rx="20" fill="#D8433A"/>
  <path d="M300 266 L724 266 Q772 334 880 286 Q886 340 846 368 Q512 398 178 368 Q138 340 144 286 Q252 334 300 266 Z" fill="#3D4E5A" stroke="#3D4E5A" stroke-width="18" stroke-linejoin="round"/>
  <path d="M400 290 L384 352 M512 290 L512 360 M624 290 L640 352" stroke="#536774" stroke-width="14" stroke-linecap="round" fill="none"/>
  <path d="M176 376 Q512 406 848 376" stroke="#27343D" stroke-width="20" stroke-linecap="round" fill="none"/>
  <rect x="286" y="226" width="452" height="50" rx="25" fill="#27343D"/>
  <circle cx="286" cy="250" r="32" fill="#27343D"/>
  <circle cx="738" cy="250" r="32" fill="#27343D"/>
</g>'''

# Q 版的人：頭大身體小，背影，雙手背在後面。原點在腳下中間。
PERSON = '''
<g id="person">
  <ellipse cx="0" cy="4" rx="150" ry="18" fill="#000" opacity="0.14"/>
  <ellipse cx="-42" cy="-6" rx="36" ry="18" fill="#1E2226"/>
  <ellipse cx="42" cy="-6" rx="36" ry="18" fill="#1E2226"/>
  <path d="M-62 -160 Q0 -134 62 -160 C104 -134 126 -70 128 -14 Q0 10 -128 -14 C-126 -70 -104 -134 -62 -160 Z" fill="#3A6EA5"/>
  <path d="M-62 -160 Q0 -134 62 -160 L52 -176 Q0 -154 -52 -176 Z" fill="#F3ECD8"/>
  <ellipse cx="0" cy="-70" rx="30" ry="18" fill="#F0C29B"/>
  <circle cx="-112" cy="-238" r="20" fill="#F0C29B"/>
  <circle cx="112" cy="-238" r="20" fill="#F0C29B"/>
  <circle cx="0" cy="-250" r="112" fill="#23272C"/>
  <circle cx="0" cy="-372" r="44" fill="#23272C"/>
  <rect x="-74" y="-380" width="148" height="16" rx="8" fill="#D9A036"/>
</g>'''

BG = '<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F8EBCB"/><stop offset="1" stop-color="#E6CB92"/></linearGradient>'

client = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" width="1024" height="1024">
<defs>{BG}</defs>
<rect width="1024" height="1024" fill="url(#bg)"/>
<g transform="translate(512 500) scale(0.9) translate(-512 -532)">{BOARD}</g>
</svg>'''

host = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" width="1024" height="1024">
<defs>{BG}<clipPath id="tile"><rect x="100" y="100" width="824" height="824" rx="186"/></clipPath></defs>
<g clip-path="url(#tile)">
<rect x="100" y="100" width="824" height="824" fill="url(#bg)"/>
<g transform="translate(532 430) scale(0.8) translate(-512 -532)">{BOARD}</g>
<g transform="translate(352 872) scale(0.92)">{PERSON}</g>
</g>
</svg>'''


def svg(inner, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" width="1024" height="1024">'
            f'<defs>{BG}{defs}</defs>{inner}</svg>')


# 看板端在 Android 8 以上用「前景＋背景」兩層，系統會自己裁形狀；
# 前景要縮在中間，四周留給系統裁切。
client_foreground = svg(f'<g transform="translate(512 512) scale(0.66) translate(-512 -532)">{BOARD}</g>')
client_background = svg('<rect width="1024" height="1024" fill="url(#bg)"/>')


def render(name, source, folder):
    """把 SVG 存到這個資料夾，並轉成 1024x1024 的 PNG（背景透明），回傳 PNG 的路徑。"""
    path = os.path.join(HERE, f"{name}.svg")
    with open(path, "w") as file:
        file.write(source)
    page = os.path.join(folder, f"{name}.html")
    with open(page, "w") as file:
        file.write(f'<html><body style="margin:0;background:transparent"><img src="file://{path}" style="display:block"></body></html>')
    png = os.path.join(folder, f"{name}.png")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars", "--default-background-color=00000000",
                    "--window-size=1024,1024", f"--screenshot={png}", f"file://{page}"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return png


def resize(source, size, target):
    os.makedirs(os.path.dirname(target), exist_ok=True)
    subprocess.run(["sips", "-z", str(size), str(size), source, "--out", target], check=True, stdout=subprocess.DEVNULL)


def main():
    with tempfile.TemporaryDirectory() as folder:
        full = render("cam-board-client-icon", client, folder)
        foreground = render("cam-board-client-icon-foreground", client_foreground, folder)
        background = render("cam-board-client-icon-background", client_background, folder)
        host_png = render("cam-board-host-icon", host, folder)

        res = os.path.join(ROOT, "cam-board-client/android/app/src/main/res")
        # 舊式的單張圖示（Android 7 以下）是 48dp，兩層的是 108dp。
        for density, scale in (("mdpi", 1), ("hdpi", 1.5), ("xhdpi", 2), ("xxhdpi", 3), ("xxxhdpi", 4)):
            resize(full, int(48 * scale), f"{res}/mipmap-{density}/ic_launcher.png")
            resize(foreground, int(108 * scale), f"{res}/mipmap-{density}/ic_launcher_foreground.png")
            resize(background, int(108 * scale), f"{res}/mipmap-{density}/ic_launcher_background.png")
        os.makedirs(f"{res}/mipmap-anydpi-v26", exist_ok=True)
        with open(f"{res}/mipmap-anydpi-v26/ic_launcher.xml", "w") as file:
            file.write(
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
                '    <background android:drawable="@mipmap/ic_launcher_background" />\n'
                '    <foreground android:drawable="@mipmap/ic_launcher_foreground" />\n'
                "</adaptive-icon>\n"
            )

        icons = os.path.join(ROOT, "cam-board-host/macos/Runner/Assets.xcassets/AppIcon.appiconset")
        for size in (16, 32, 64, 128, 256, 512, 1024):
            resize(host_png, size, f"{icons}/app_icon_{size}.png")


if __name__ == "__main__":
    main()
