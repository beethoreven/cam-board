#!/bin/bash
# 用無線 adb 把看板端裝到手機上。
#
# 為什麼不直接 adb install：這支開發用的手機走無線 adb 時，傳超過大約 10 MB 的檔案
# 會卡住不動（2026-11-25 實測，1 MB 和 10 MB 正常，40 MB 卡住）。所以把安裝檔切成
# 小塊分次傳，在手機上接回去再安裝。用 USB 線時直接 adb install 就好，不需要這個。
#
# 用法（在 meta repo 的根目錄）：
#   cd cam-board-client && fvm flutter build apk --debug --target-platform android-arm64
#   tools/install-client-wireless.sh
# 手機不只一支時，用 ADB_SERIAL 指定：ADB_SERIAL=192.168.1.115:39731 tools/install-client-wireless.sh
set -u
# macOS 內建的 bash 3.2 在 UTF-8 的終端機下，變數後面直接接中文（例如「$remote，」）
# 會把中文的一部分當成變數名稱，報出「unbound variable」。固定用 C 就不會；
# 中文訊息照樣顯示得出來，因為畫出文字的是終端機，不是 bash。
export LC_ALL=C
APK=${1:-"$(dirname "$0")/../cam-board-client/build/app/outputs/flutter-apk/app-debug.apk"}
DEVICE=${ADB_SERIAL:-$(adb devices | awk 'NR>1 && $2=="device"{print $1; exit}')}
[ -n "$DEVICE" ] || { echo "adb 找不到手機"; exit 1; }
[ -f "$APK" ] || { echo "找不到安裝檔：$APK"; exit 1; }

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
split -b 6m "$APK" "$WORK/part."
adb -s "$DEVICE" shell "rm -rf /data/local/tmp/parts; mkdir -p /data/local/tmp/parts" || exit 1
for part in "$WORK"/part.*; do
  sent=0
  for attempt in 1 2 3; do
    adb -s "$DEVICE" push "$part" /data/local/tmp/parts/ >/dev/null 2>&1 &
    pid=$!
    for _ in $(seq 1 25); do kill -0 $pid 2>/dev/null || break; sleep 1; done
    if kill -0 $pid 2>/dev/null; then
      # 卡住了。卡住之後連小指令都不會有回應，要重啟 adb 才恢復。
      kill $pid
      adb kill-server
      adb start-server >/dev/null 2>&1
      sleep 6
    elif wait $pid; then
      sent=1
      break
    else
      sleep 2
    fi
  done
  [ $sent = 1 ] || { echo "傳 $(basename "$part") 失敗"; exit 1; }
done
remote=$(adb -s "$DEVICE" shell "cat /data/local/tmp/parts/part.* > /data/local/tmp/cam-board-client.apk && rm -rf /data/local/tmp/parts && stat -c %s /data/local/tmp/cam-board-client.apk" | tr -d '\r')
local_size=$(stat -f %z "$APK" 2>/dev/null || stat -c %s "$APK")
[ "$remote" = "$local_size" ] || { echo "手機上的檔案大小不對（$remote，應該是 $local_size）"; exit 1; }
adb -s "$DEVICE" shell pm install -r /data/local/tmp/cam-board-client.apk
