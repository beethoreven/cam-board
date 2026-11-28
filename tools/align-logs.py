#!/usr/bin/env python3
"""把兩端（或更多）各自的紀錄檔照時間排成一條時間線，每一行標明是哪一端的。

查「一端送了、另一端沒收到」這類問題時，要把兩邊同一秒發生的事放在一起看。
各端的紀錄格式不用一樣，只要每一行裡有時間就行。

用法：
  align-logs.py 手機=client.log 電腦=host.log
  align-logs.py 手機=client.log 電腦=host.log --from 12:06:30 --to 12:07:10
  align-logs.py 手機=client.log 電腦=host.log --grep '重建|接回|照片' --exclude '統計'
  align-logs.py 手機=logcat.txt 電腦=host.log --shift 手機=+0.35   # 手機的時鐘慢了 0.35 秒

認得的時間寫法（取每一行裡的第一個）：
  2026-11-27T12:06:42.123456   （ISO）
  11-27 12:06:42.123            （Android logcat）
  12:06:42 或 12:06:42.123      （只有時間）
沒有時間的行會接在上一行後面，當成同一筆的延續。

注意：兩台裝置的時鐘可能差幾十到幾百毫秒，順序差一點點不代表真的誰先誰後。
確定差多少時用 --shift 修正。跨過午夜的紀錄請用 --from/--to 分段看。
"""

import argparse
import re
import sys

TIME = re.compile(r"(?<!\d)(\d{2}):(\d{2}):(\d{2})(?:[.,](\d{1,6}))?(?!\d)")


def seconds(text):
    match = TIME.search(text)
    if not match:
        return None
    hour, minute, second, fraction = match.groups()
    value = int(hour) * 3600 + int(minute) * 60 + int(second)
    if fraction:
        value += int(fraction) / (10 ** len(fraction))
    return value


def clock(value):
    value = max(value, 0)
    whole = int(value)
    return f"{whole // 3600:02d}:{whole % 3600 // 60:02d}:{whole % 60:02d}.{int((value - whole) * 1000):03d}"


def strip_time(line):
    """拿掉行首的日期時間，留下內容；時間不在行首的就整行留著。"""
    return re.sub(r"^\s*(?:\d{4}-\d{2}-\d{2}[T ]|\d{2}-\d{2} )?\d{2}:\d{2}:\d{2}(?:[.,]\d+)?\s*", "", line, count=1)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sources", nargs="+", metavar="名稱=檔案", help="每一端的名稱和它的紀錄檔")
    parser.add_argument("--from", dest="start", metavar="HH:MM:SS", help="只看這個時間之後")
    parser.add_argument("--to", dest="end", metavar="HH:MM:SS", help="只看這個時間之前")
    parser.add_argument("--grep", metavar="規則", help="只留符合這個規則運算式的行")
    parser.add_argument("--exclude", metavar="規則", help="去掉符合這個規則運算式的行")
    parser.add_argument("--shift", action="append", default=[], metavar="名稱=±秒", help="把某一端的時間往後（+）或往前（-）調")
    parser.add_argument("--width", type=int, default=200, help="每一行最多顯示幾個字（預設 200）")
    args = parser.parse_args()

    shifts = {}
    for item in args.shift:
        name, _, amount = item.partition("=")
        shifts[name] = float(amount)
    start = seconds(args.start) if args.start else None
    end = seconds(args.end) if args.end else None
    keep = re.compile(args.grep) if args.grep else None
    drop = re.compile(args.exclude) if args.exclude else None

    rows = []
    for order, source in enumerate(args.sources):
        name, sep, path = source.partition("=")
        if not sep:
            parser.error(f"要寫成「名稱=檔案」：{source}")
        try:
            lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
        except OSError as error:
            sys.exit(f"讀不到 {path}：{error}")
        current = None
        for number, line in enumerate(lines):
            at = seconds(line[:48])
            if at is not None:
                current = at + shifts.get(name, 0.0)
                text = strip_time(line)
            else:
                text = "    " + line.strip()
            if current is None or not line.strip():
                continue
            if start is not None and current < start:
                continue
            if end is not None and current > end:
                continue
            if keep and not keep.search(line):
                continue
            if drop and drop.search(line):
                continue
            rows.append((current, order, number, name, text))

    rows.sort()
    label = max((len(row[3]) for row in rows), default=0)
    for at, _, _, name, text in rows:
        if len(text) > args.width:
            text = text[: args.width] + "…"
        print(f"{clock(at)} | {name:<{label}} | {text}")
    print(f"# 共 {len(rows)} 行", file=sys.stderr)


if __name__ == "__main__":
    main()
