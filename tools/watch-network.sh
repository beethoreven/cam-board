#!/bin/bash
# 持續量測三段網路，查「畫面中斷、照片送不到」是哪一段出問題：
#   電腦 → 手機、電腦 → 基地台、手機 → 基地台（透過 adb）
# 每 0.5 秒量一次，每一筆都帶時間。按 Ctrl+C 停止。
#
# 用法：tools/watch-network.sh <手機的 IP> [存放紀錄的資料夾]
# 例如：tools/watch-network.sh 192.168.1.115
# 同時有 USB 和無線兩條 adb 連線時，用 ANDROID_SERIAL 指定一條（USB 的比較穩）：
#   ANDROID_SERIAL=17c6bde8 tools/watch-network.sh 192.168.1.115
#
# 怎麼看：出問題的那幾秒，
#   只有「電腦 → 手機」掉          → 手機和基地台之間，或手機本身
#   「電腦 → 基地台」也掉          → 電腦這邊的 Wi-Fi
#   「手機 → 基地台」也掉          → 手機這邊的 Wi-Fi
#   三個都掉                        → 基地台
set -u

phone="${1:?請給手機的 IP，例如 192.168.1.115}"
out="${2:-/tmp/cam-board-network-$(date +%H%M%S)}"
mkdir -p "$out"
gateway="$(route -n get default 2>/dev/null | awk '/gateway/ {print $2}')"
if [ -z "$gateway" ]; then
  echo "找不到基地台的位址，電腦可能沒有連上網路" >&2
  exit 1
fi

echo "紀錄放在 $out（基地台 $gateway，手機 $phone）"
ping --apple-time -i 0.5 "$phone" > "$out/mac-to-phone.log" 2>&1 &
ping --apple-time -i 0.5 "$gateway" > "$out/mac-to-gateway.log" 2>&1 &
# 手機上的 ping 不帶時間，用 -D 讓它印出時間戳記。adb 斷掉時這一份會停。
adb shell ping -D -i 0.5 "$gateway" > "$out/phone-to-gateway.log" 2>&1 &
# 傳照片的那條連線（看板端的 47800 埠）在兩端各有多少資料卡在佇列裡，每秒記一次。
# 照片送不到時：
#   電腦這邊的 Recv-Q 一直有東西     → 資料到了電腦，鄉民端沒有去讀
#   手機那邊的 Send-Q 一直有東西     → 資料卡在手機送不出去（看同一行的 retrans、rto）
#   兩邊都是 0                       → 看板端的程式根本沒把資料交給系統
(
  while true; do
    netstat -anv -p tcp 2>/dev/null | grep -E '[.]47800 ' | sed "s/^/$(date +%H:%M:%S) /"
    sleep 1
  done
) > "$out/mac-tcp-47800.log" 2>&1 &
adb shell 'while true; do t=$(date +%H:%M:%S); ss -tin 2>/dev/null | grep -A1 ":47800 " | sed "s/^/$t /"; sleep 1; done' \
  > "$out/phone-tcp-47800.log" 2>&1 &
trap 'kill $(jobs -p) 2>/dev/null' EXIT INT TERM
wait
