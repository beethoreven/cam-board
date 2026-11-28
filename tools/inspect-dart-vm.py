#!/usr/bin/env python3
"""讀一個「執行中」的 Dart／Flutter 程式（開發版）裡，某些類別的物件現在長什麼樣子。

只讀不改：不會暫停程式，也不會改任何值。用來回答「它現在到底卡在什麼狀態」，
不用重現問題，也不用請使用者貼終端機的內容。

用法：
  inspect-dart-vm.py 類別名稱 [類別名稱 ...]
  inspect-dart-vm.py --url http://127.0.0.1:50275/abc=/ ViewerController
  inspect-dart-vm.py --depth 2 WebRtcBoardLink      # 連同它欄位裡的物件再往下看一層
  inspect-dart-vm.py --list 'Controller|Link'        # 不知道類別名稱時，用關鍵字找

程式要是用 `flutter run`（或 `dart run --observe`）啟動的開發版才有這個服務。
沒給 --url 時，會從這台電腦正在執行的程式裡找；找到不只一個就列出來請你選。
"""

import argparse
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request


def find_services():
    """找出這台電腦上所有開著的 Dart VM 服務位址。"""
    out = subprocess.run(["ps", "-axww", "-o", "pid=,args="], capture_output=True, text=True).stdout
    found = []
    for line in out.splitlines():
        match = re.search(r"--vm-service-uri=(\S+)", line)
        if match:
            name = re.search(r"--app-name=(.*)$", line)
            found.append((match.group(1).rstrip("/"), name.group(1).strip() if name else ""))
    return found


class Vm:
    def __init__(self, base):
        self.base = base.rstrip("/")
        vm = self.call("getVM")
        isolates = vm.get("isolates", [])
        if not isolates:
            sys.exit("這個程式裡沒有正在執行的 isolate")
        self.isolate = isolates[0]["id"]
        self.pid = vm.get("pid")

    def call(self, method, **params):
        query = urllib.parse.urlencode(params)
        try:
            with urllib.request.urlopen(f"{self.base}/{method}?{query}", timeout=20) as reply:
                data = json.load(reply)
        except OSError as error:
            sys.exit(f"連不上 {self.base}：{error}")
        if "error" in data:
            raise RuntimeError(data["error"].get("message", str(data["error"])))
        return data["result"]

    def classes(self):
        return self.call("getClassList", isolateId=self.isolate)["classes"]

    def instances(self, class_id, limit):
        return self.call("getInstances", isolateId=self.isolate, objectId=class_id, limit=limit)

    def fields(self, object_id):
        obj = self.call("getObject", isolateId=self.isolate, objectId=object_id)
        result = []
        for field in obj.get("fields", []):
            decl = field.get("decl")
            name = decl["name"] if isinstance(decl, dict) else field.get("name")
            result.append((name, field["value"]))
        for index, element in enumerate(obj.get("elements", [])[:20]):
            if isinstance(element, dict):
                result.append((f"[{index}]", element))
        return result


def describe(value):
    """把一個欄位的值變成一行看得懂的字。"""
    kind = value.get("kind", value.get("type", ""))
    cls = value.get("class", {}).get("name", "")
    if "valueAsString" in value:
        text = value["valueAsString"]
        if value.get("valueAsStringIsTruncated"):
            text += "…"
        return f"{text}" if kind in ("Null", "Bool", "Int", "Double") else f"{text!r}"
    if "length" in value:
        return f"<{cls}，{value['length']} 個>"
    return f"<{cls or kind}>"


def is_plain(value):
    return "valueAsString" in value or value.get("kind") in ("Null", "Closure")


def show(vm, object_id, depth, indent):
    try:
        fields = vm.fields(object_id)
    except RuntimeError as error:
        print(f"{indent}（讀不到：{error}）")
        return
    for name, value in fields:
        print(f"{indent}{name}: {describe(value)}")
        if depth > 1 and not is_plain(value) and value.get("id"):
            show(vm, value["id"], depth - 1, indent + "    ")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("classes", nargs="*", help="要看的類別名稱（要完全一樣）")
    parser.add_argument("--url", help="VM 服務的位址；不給就自己找")
    parser.add_argument("--depth", type=int, default=1, help="往下看幾層（預設 1）")
    parser.add_argument("--limit", type=int, default=5, help="每個類別最多列幾個物件（預設 5）")
    parser.add_argument("--list", metavar="關鍵字", help="列出名稱符合這個規則運算式的類別，不看內容")
    args = parser.parse_args()

    url = args.url
    if not url:
        services = find_services()
        if not services:
            sys.exit("找不到正在執行的開發版程式（要用 flutter run 之類的方式啟動才有）")
        if len(services) > 1:
            print("找到不只一個，請用 --url 指定：", file=sys.stderr)
            for found, name in services:
                print(f"  {found}/   {name}", file=sys.stderr)
            sys.exit(2)
        url = services[0][0]

    vm = Vm(url)
    print(f"# 程式 pid {vm.pid}，{url}")
    all_classes = vm.classes()

    if args.list:
        pattern = re.compile(args.list)
        for name in sorted({c["name"] for c in all_classes if pattern.search(c["name"])}):
            print(name)
        return
    if not args.classes:
        parser.error("要給類別名稱，或用 --list 找")

    for wanted in args.classes:
        matches = [c for c in all_classes if c["name"] == wanted]
        if not matches:
            print(f"== {wanted}：沒有這個類別（用 --list 找找看）")
            continue
        for cls in matches:
            found = vm.instances(cls["id"], args.limit)
            print(f"== {wanted}：{found['totalCount']} 個物件")
            for number, instance in enumerate(found.get("instances", []), 1):
                print(f"-- 第 {number} 個")
                show(vm, instance["id"], args.depth, "  ")


if __name__ == "__main__":
    main()
