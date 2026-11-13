# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 這個專案是什麼

cam-board 把手機當成白板的鏡頭：手機（**看板端**）拍手寫紙，電腦（**鄉民端**）取得畫面後接投影機投出來。兩端只在同一個區域網路內連線（包含沒有網路的手機熱點），沒有伺服器、沒有登入、不傳聲音。

## Repo 結構

這是 meta repo，三個資料夾各自是獨立的 GitHub repo，以 submodule 掛進來：

- `cam-board-core`：兩端共用的純 Dart 邏輯，Dart 套件名 `cam_board_core`
- `cam-board-client`：看板端，Android（之後 iOS），識別碼 `tw.com.tutorarthur.camboard.client`
- `cam-board-host`：鄉民端，macOS（之後 Windows），識別碼 `tw.com.tutorarthur.camboard.host`

英文的 client 一律指看板端，host 一律指鄉民端。

改動 submodule 裡的檔案時，要先在該 submodule 裡 commit，再回 meta repo commit 更新後的 submodule 指向。兩個 app 用相對路徑 `../cam-board-core` 引用共用邏輯，所以只能在 meta repo 裡建置。

## 指令

所有 `flutter`、`dart` 指令前面都要加 `fvm`，否則會用到系統上沒有鎖版本的 Flutter。這台機器的 `fvm` 在 `~/.pub-cache/bin`，不在 PATH 裡時用完整路徑。

共用邏輯（在 `cam-board-core` 裡執行）：

```bash
fvm dart test                                   # 全部測試
fvm dart test test/session_test.dart            # 單一檔案
fvm dart test --name "不給看了"                  # 名稱包含這段文字的測試
fvm dart analyze
fvm dart format .
```

兩個 app（在 `cam-board-client` 或 `cam-board-host` 裡執行）：

```bash
fvm flutter analyze
fvm flutter test
fvm flutter test test/widget_test.dart          # 單一檔案
```

執行與建置：

```bash
cd cam-board-host && fvm flutter run -d macos           # 鄉民端
cd cam-board-host && fvm flutter build macos --debug
cd cam-board-client && fvm flutter run                  # 看板端，需要接上 Android 實機
cd cam-board-client && fvm flutter build apk --debug
```

## 架構

**規則放在 core，app 只負責接上真實世界。** `cam-board-core` 不依賴 Flutter，也不碰網路、鏡頭、視窗；它定義的是可以單獨測試的規則。app 那一層在做任何事之前先問 core 的狀態物件（`BoardSession`、`ViewerSession`）這個動作合不合法，再去操作網路或畫面。新增行為時先在 core 加規則和測試，再到 app 接上。

**連線流程**（app 端尚未實作，訊息格式已在 core 的 `signal_message.dart` 定案）：

1. 看板端註冊時用 mDNS 廣播 `_cam-board._tcp`，鄉民端搜尋得到看板清單。部分手機熱點會擋 mDNS，所以鄉民端另外支援手動輸入看板端顯示的位址。
2. 看板端在手機上開 WebSocket 伺服器（預設埠 47800）。鄉民端連上後送 `join`，看板端回 `offer`，鄉民端回 `answer`，雙方互送 `candidate`。
3. 之後畫面走 WebRTC 在兩台裝置之間直接傳。
4. 任一方送 `bye` 並附上原因就結束。

每個鄉民端各一條連線，一個看板可以同時給多個鄉民端看；一個鄉民端一次只看一個看板。`join` 帶有通訊協定版本，兩端版本不同時在這一步就拒絕。改動訊息格式時要遞增 `protocolVersion`。

**「不用留黑」**：鄉民端的視窗永遠等於畫面的大小和比例，不留黑邊。「放到最大」是在螢幕內維持比例放大並置中，不使用 macOS 原生全螢幕（原生全螢幕會把空白處塗黑）。計算在 core 的 `view_geometry.dart`。

## 已定案的規格

畫面上的用詞是固定的，不要改寫：

- 看板端：「註冊」「撤銷註冊」，觀看中退出叫「**不給看了**」
- 鄉民端：退出叫「**不看了**」
- App 顯示名稱：「看板端」「鄉民端」

行為：

- 註冊本身就代表同意被看，鄉民端點了看板就直接連，不再詢問看板端。
- 「不給看了」結束所有鄉民端的觀看，但看板仍留在清單上；要從清單消失得按「撤銷註冊」。
- 旋轉（90／180／270 度）和左右反轉只影響鄉民端自己的顯示。
- 畫質優先：網路變差時降低每秒張數，不降解析度。
- 看板端的鏡頭控制：縮放、點擊對焦、切換前後鏡頭。

尚未實作、之後可能加入：看板端單獨踢出其中一個鄉民端。

## 版本

Flutter 固定在 3.47.9，由根目錄的 `.fvmrc` 鎖定。開發機是 Intel Mac，Flutter 已預告未來停止支援在 Intel Mac 上建置，所以升版前必須先確認新版仍然支援。因為這個限制而不能用最新版的套件，連同原因列在 `README.md`，新增這類套件時要更新那張表。
