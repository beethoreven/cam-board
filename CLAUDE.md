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

鄉民端另有一組在真的 macOS 程式裡、用真的區域網路跑的測試。要先在另一個終端機廣播一個假看板，測試才搜尋得到：

```bash
dns-sd -R "整合測試看板" _cam-board._tcp local 47999      # 保持執行，測完再按 Ctrl+C
cd cam-board-host && fvm flutter test integration_test/discovery_test.dart -d macos
cd cam-board-host && fvm flutter test integration_test/window_control_test.dart -d macos   # 會實際移動視窗，不需要 dns-sd
```

整合測試要一個檔案一個檔案跑，一起跑會互相搶同一個視窗。

手機接著、而且已經在看板端按了「註冊」時，可以讓真的鄉民端連過去確認收得到畫面（位址用看板端畫面上顯示的）。改動連線或視訊相關的程式後要跑這個，因為其他測試裡的鏡頭和視訊都是假的：

```bash
cd cam-board-host && fvm flutter test integration_test/watch_real_board_test.dart -d macos --dart-define=BOARD=192.168.1.115:47800
cd cam-board-host && fvm flutter test integration_test/record_real_board_test.dart -d macos --dart-define=BOARD=192.168.1.115:47800   # 抄錄；印出「請在看板端按拍照」後 60 秒內要在手機上按一次「拍照」
```

這些 `-d macos` 的測試，測試的視窗要在最前面才會動。使用者自己也開著一個鄉民端時，測試會卡住不動：不要關掉使用者的鄉民端，改用 `osascript -e 'tell application "System Events" to set frontmost of (first process whose unix id is <測試程式的 pid>) to true'` 把測試的視窗叫到最前面。

手機用無線 adb 連著時，傳大檔會卡住，直接 `adb install` 或 `flutter run` 都裝不上去。用 `tools/install-client-wireless.sh`（先 `fvm flutter build apk --debug --target-platform android-arm64`）。

執行與建置：

```bash
cd cam-board-host && fvm flutter run -d macos           # 鄉民端
cd cam-board-host && fvm flutter build macos --debug
cd cam-board-client && fvm flutter run                  # 看板端，需要接上 Android 實機
cd cam-board-client && fvm flutter build apk --debug
```

## 架構

**規則放在 core，app 只負責接上真實世界。** `cam-board-core` 不依賴 Flutter，也不碰網路、鏡頭、視窗；它定義的是可以單獨測試的規則。app 那一層在做任何事之前先問 core 的狀態物件（`BoardSession`、`ViewerSession`）這個動作合不合法，再去操作網路或畫面。新增行為時先在 core 加規則和測試，再到 app 接上。

**app 的分層**：每個 app 的 controller 把 core 的規則接上 `lib/services/` 裡的服務。看板端是 `BoardController`；鄉民端是 `BoardListController`（看板清單）和 `ViewerController`（觀看）。服務（區域網路廣播與搜尋、連線、鏡頭、WebRTC、視窗、螢幕恆亮）都先定義介面再實作，測試時換成 `test/fakes.dart` 裡的假服務。真的實作另外測：WebSocket 用真的連線、視窗用真的 macOS 視窗；WebRTC 和鏡頭只能靠實機驗收。

**連線流程**（訊息格式在 core 的 `signal_message.dart`）：

1. 看板端註冊時用 mDNS 廣播 `_cam-board._tcp`，鄉民端搜尋得到看板清單。部分手機熱點會擋 mDNS，所以鄉民端另外支援手動輸入看板端顯示的位址。
2. 看板端在手機上開 WebSocket 伺服器（預設埠 47800）。鄉民端一連上，看板端先送 `hello` 報上名稱和通訊協定版本；鄉民端手動輸入位址時就是靠它確認對方是看板。鄉民端要看畫面時送 `join`，看板端回 `offer`，鄉民端回 `answer`，雙方互送 `candidate`；看板端的網路路徑全部找完時再送一則 `candidates_done`。
3. 之後畫面走 WebRTC 在兩台裝置之間直接傳，只送畫面、不送聲音。兩端都不設定任何 ICE 伺服器，因為只在區域網路內連線，這也是沒有網路的熱點能用的原因。
4. 任一方送 `bye` 並附上原因就結束。

看板端的伺服器開在區域網路上，誰都連得到，所以 `signal_server.dart` 在進門前先擋：帶 `Origin` 的連線（網頁發出的）、不是從區域網路來的對方（規則在 core 的 `isLanPeer`）、超過連線數上限的；連上之後 10 秒沒送過一則看得懂的訊息、或送來超大訊息或二進位資料的會被關掉。鄉民端送了 `join` 之後超過 core 的 `answerTimeout`（10 秒）沒回 `answer`，看板端就結束它，鏡頭不會為了它一直開著。這些只擋掉不照規矩的連線，不是驗證身分：同一個區域網路上任何人都還是看得到畫面，連線資訊和照片也沒有加密（要改得先決定要不要做配對碼）。

看板端處理鄉民端的訊息、斷線、「不給看了」、撤銷註冊，是排隊一件做完才做下一件（`BoardController._serial`）。處理 `join` 要開鏡頭、建連線，中間會等好幾次；不排隊的話，空檔裡另一個鄉民端加入會讓鏡頭開兩次，同一個鄉民端這時斷線則會留下一條沒人的連線、鏡頭關不掉。新增會動到這些狀態的流程時要走同一個排隊。

網路路徑（`candidate`）常常比連線資訊還早到，兩端都用 core 的 `CandidateGate` 先留著，等連線資訊處理完再交給 WebRTC；鄉民端另外把收到的訊息排隊，一則處理完才處理下一則。少了這兩件事，連線會時好時壞。

鄉民端從點了看板起算，超過 core 的 `connectTimeout`（5 秒）畫面還沒出來就放棄並回到清單。原因由 core 的 `ConnectProgress` 依連線進行到哪一步判斷：連不到看板端、看板端沒回應、交換到一半中斷、或看板端的路徑都送完了（收到 `candidates_done`）卻沒有一條連得通。最後一種代表兩台裝置之間的網路不通，重試沒有用。`candidates_done` 只用來判斷原因，不交給 WebRTC。計時在 `ViewerController`。

**抄錄**：鄉民端連上後可以按「我要抄錄」，選一個位置，在裡面建立 `{看板名稱}抄錄紀錄_26-11-25-14-30-05` 這種名稱的資料夾，並送 `record_start` 告訴看板端。看板端按「拍照」時，擷取鏡頭現在的畫面（還沒經過視訊壓縮，也不轉成圖檔，格式見 core 的 `raw_frame.dart`），只對抄錄中的鄉民端送 `shot`（帶寬、高、要轉幾度才是正的），後面緊接著一筆 WebSocket 的二進位訊息就是那張畫面；沒有人在抄錄時什麼都不做。鄉民端確認收完整就回 `shot_received`，看板端這時就顯示『{鄉民的名稱}抄錄了這個內容』；之後鄉民端才把畫面換成紅綠藍、轉正、套用自己當下的旋轉與左右反轉，壓成 PNG 存成 `001.png`、`002.png`……。轉成 PNG 不要搬回手機做，也不要讓看板端等存檔：手機轉一張要 1.2～1.7 秒（2026-11-25 實測），所以才改成這樣；代價是存不進去時只有鄉民端自己知道。鄉民的名稱在 `join` 裡帶過去，沒填時用電腦的名稱。看板端只在「真的傳過這一張給這個鄉民端、而且它還沒回報過」時才顯示提示（core 的 `BoardRecorders.shotConfirmed`）。同一秒內抄錄第二次時，資料夾名稱用下一秒，不跟上一次共用。按「抄錄完了」送 `record_stop`；觀看結束時抄錄也跟著結束。規則在 core 的 `recording.dart`。

**看板端的鏡頭控制**：縮放、對焦、擷取畫面走自己寫的 Android 程式（`cam-board-client/android/.../CameraControl.kt`），不用 flutter_webrtc 的 `Helper`。原因是套件設定縮放或對焦時會把鏡頭的設定整個換掉、互相蓋掉，也沒有真的觸發對焦，擷取功能存的又是 JPEG。所以 `CameraSource.apply` 每次都同時帶縮放和對焦，不要拆開。這段 Kotlin 用反射取得 flutter_webrtc 1.6.3 沒有公開的欄位，升級套件前要照 README 版本那一節的說明檢查。「自動對焦」開關的規則（開著時點擊對焦維持 5 秒、關著時一直鎖住、鏡頭重開時套回去）在 core 的 `focus_control.dart`。鎖住對焦一律是「對好焦之後把鏡頭固定在回報的距離」（對焦模式關閉＋指定距離），不能只靠「不觸發就不對焦」的模式：實機（OPPO Reno5 5G）在那個模式下，畫面內容一變相機還是會自己重新對焦。鏡頭實際的對焦狀態與位置一有變化會寫進 logcat（標籤 `CamBoardCamera`，`lens` 開頭），查對焦問題時看這個；不要用 `adb shell dumpsys media.camera`，它在這支手機上會讓相機服務當掉。

看板端第一個鄉民端加入時才開鏡頭，最後一個離開時關掉。每個鄉民端各一條連線（`ViewerLink`），共用同一個鏡頭畫面，所以一個看板可以同時給多個鄉民端看；一個鄉民端一次只看一個看板。`hello` 和 `join` 都帶有通訊協定版本，兩端版本不同時在這一步就拒絕。改動訊息格式時要遞增 `protocolVersion`（目前是 4）。

**「不用留黑」**：鄉民端的視窗永遠等於畫面的大小和比例，不留黑邊。「放到最大」是在螢幕內維持比例放大並置中，不使用 macOS 原生全螢幕（原生全螢幕會把空白處塗黑）。計算在 core 的 `view_geometry.dart`，`ViewerController` 每次畫面大小、旋轉角度或放大狀態改變時重算並套用到視窗。視窗控制用 `window_manager` 0.6.0 底層的 `nativeapi`（見 `window_control.dart` 開頭的說明）。

## 已定案的規格

畫面上的用詞是固定的，不要改寫：

- 看板端：「註冊」「撤銷註冊」，觀看中退出叫「**不給看了**」，「自動對焦」（開關）、「拍照」
- 鄉民端：退出叫「**不看了**」，「我要抄錄」「抄錄完了」，名稱欄位叫「名稱」
- 看板端的提示：『{鄉民的名稱}抄錄了這個內容』
- 抄錄的資料夾：`{看板名稱}抄錄紀錄_26-11-25-14-30-05`（年月日時分秒各兩位，用 `-` 連接）
- App 顯示名稱：「看板端」「鄉民端」

行為：

- 註冊本身就代表同意被看，鄉民端點了看板就直接連，不再詢問看板端。
- 「不給看了」結束所有鄉民端的觀看，但看板仍留在清單上；要從清單消失得按「撤銷註冊」。
- 旋轉（90／180／270 度）和左右反轉只影響鄉民端自己的顯示。
- 畫質優先：網路變差時降低每秒張數，不降解析度。視訊速率另有 1 Mbps 的下限（`viewer_link.dart` 的 `_minBitrate`），不要拿掉：沒有下限時，WebRTC 估計的頻寬掉到最低就爬不回來，畫面會停住到重新連線為止（2026-11-25 實機上鏡頭被遮住再放開後發生）。
- 看板端的鏡頭控制：縮放、點擊對焦、切換前後鏡頭。

目前的限制：看板端要留在前景，退到背景後可能從看板清單消失、畫面也會停。註冊期間螢幕會保持恆亮，所以手機架著不動時不受影響。背景執行需要 Android 的前景服務，尚未實作。


使用者體驗的調整（提示文字、過渡畫面、按鈕樣式等）刻意留到全部功能完成之後再一起處理，開發途中不要做。

尚未實作、之後可能加入：看板端單獨踢出其中一個鄉民端。

**正式版還沒打包過（2026-11-25）。** 到目前為止兩個 app 都只用開發版執行。做打包時要先處理這幾件事，而且要實機驗證過才算數：

- 看板端的 `android/app/src/main/AndroidManifest.xml` 沒有 `android.permission.INTERNET`（開發版是 Flutter 自動加的），正式版很可能開不了伺服器。
- 鄉民端的 `macos/Runner/Release.entitlements` 比 `DebugProfile.entitlements` 少了 `com.apple.security.network.server`，視訊連線很可能需要。
- 看板端正式版目前用開發用的金鑰簽章（`build.gradle.kts`），自己用可以，要發給別人前要換。
- 兩個 app 的版本號都還是 `0.1.0+1`。
- 看板端和相機服務出錯時不會發現、也不會重開鏡頭（畫面停住但仍顯示有鄉民端在看）。

## 版本

Flutter 固定在 3.47.9，由根目錄的 `.fvmrc` 鎖定。開發機是 Intel Mac，Flutter 已預告未來停止支援在 Intel Mac 上建置，所以升版前必須先確認新版仍然支援。因為這個限制而不能用最新版的套件，連同原因列在 `README.md`，新增這類套件時要更新那張表。

## 權限與 hook

權限規則在 `.claude/settings.json`。測試、靜態檢查、格式化不用詢問；`git push` 一律被擋，推送由專案擁有者自己在終端機做，不要嘗試繞過。

Claude 每次用 Edit 或 Write 改完 `.dart` 檔，hook 會自動執行 `.claude/hooks/format-dart.sh`，用固定版本的 Dart 排版該檔案，所以不需要另外手動跑 `dart format`。用 Bash 指令改的檔案不會觸發這個 hook。

deny 擋的是 `git push ...` 和 `git -C <資料夾> push ...` 兩種寫法（後者是 2026-11-25 補上的，原本是練習權限時刻意留下的缺口）。已知還擋不到的：用 `gh api` 直接呼叫 GitHub 也能改遠端的內容，目前只會跳出詢問，同樣不要用它繞過。
