# cam-board

把手機當成白板的鏡頭：手機（**看板端**）架起來拍手寫紙，電腦（**鄉民端**）取得畫面後接投影機投出來。

兩端只需要在同一個區域網路內（包含手機熱點，熱點不需要有網路），不用架伺服器，也不用登入。

## 組成

這是 meta repo，下面三個資料夾各自是獨立的 repo：

| 資料夾 | 內容 | 平台 |
| --- | --- | --- |
| `cam-board-core` | 兩端共用的純 Dart 邏輯：通訊協定、狀態規則、視窗大小計算 | 不限 |
| `cam-board-client` | 看板端 | Android（之後 iOS） |
| `cam-board-host` | 鄉民端 | macOS（之後 Windows） |

兩個 app 用相對路徑（`../cam-board-core`）引用共用邏輯，所以要在這個 meta repo 裡建置，單獨 clone 一個 app 的 repo 建不起來。

## Flutter 版本：暫時固定在 3.47.9

版本由 [FVM](https://fvm.app) 鎖定，設定在根目錄的 `.fvmrc`，三個資料夾共用。

**升版前一定要先查新版是否還支援 Intel Mac。** 目前的開發機是 Intel 晶片的 Mac，Flutter 從 3.47 起預告未來的版本會停止支援在 Intel Mac 上建置，官方還沒有公布是哪一版。升上不支援的版本，這台機器就建不出任何東西。

連帶被卡住的套件：

| 套件 | 目前版本 | 為什麼不是最新版 |
| --- | --- | --- |
| `window_manager` | 0.6.0 | 0.7 以上要求 Flutter 3.50 |
| `nativeapi` | 0.5.10 | `window_manager` 0.6.0 的底層，版本要跟它一致。直接引用是為了取得螢幕可用範圍；原本該用的 `screen_retriever` 最新版要求 Flutter 3.50 |

升 Flutter 時，把這張表裡的套件一起升到最新版。

## 開發環境

需要：FVM、Xcode（建鄉民端）、Android Studio（建看板端，Java 用它內附的，不用另外安裝）。

第一次設定：

```bash
dart pub global activate fvm
```

```bash
fvm install
```

之後所有 `flutter`、`dart` 指令前面都加 `fvm`，確保用的是固定的版本。

## 測試

共用邏輯（最快，改完就跑）：

```bash
cd cam-board-core && fvm dart test
```

兩個 app：

```bash
cd cam-board-client && fvm flutter analyze && fvm flutter test
```

```bash
cd cam-board-host && fvm flutter analyze && fvm flutter test
```

鄉民端在真的 macOS 程式裡、用真的區域網路跑的測試。先在另一個終端機廣播一個假看板：

```bash
dns-sd -R "整合測試看板" _cam-board._tcp local 47999
```

```bash
cd cam-board-host && fvm flutter test integration_test/discovery_test.dart -d macos
```

連到真的手機、確認收得到畫面的測試。手機要先在看板端按「註冊」，位址換成看板端畫面上顯示的。它會印出每一次從開始連線到出現畫面花了幾毫秒，以及途中每一步的時間；鄉民端等待畫面的上限（core 的 `connectTimeout`，目前 5 秒）就是照這個結果定的。2026-11-25 在一般 Wi-Fi 上量到 0.9～2.2 秒，換了網路環境或手機後覺得太緊可以重量：

```bash
cd cam-board-host && fvm flutter test integration_test/watch_real_board_test.dart -d macos --dart-define=BOARD=192.168.1.115:47800
```

視窗控制的測試會實際移動視窗，不需要假看板：

```bash
cd cam-board-host && fvm flutter test integration_test/window_control_test.dart -d macos
```

## 執行

鄉民端（在這台 Mac 上）：

```bash
cd cam-board-host && fvm flutter run -d macos
```

看板端（Android 實機接上 USB、開啟 USB 偵錯）：

```bash
cd cam-board-client && fvm flutter run
```

## 目前進度

- [x] 專案骨架、共用邏輯與單元測試
- [x] 找到看板：看板端註冊／撤銷註冊，鄉民端的看板清單（自動搜尋與手動輸入位址）。2026-11-24 以 Android 實機與 Mac 驗收通過，一般 Wi-Fi 與手機熱點都能自動搜尋到看板，不需要手動輸入位址
- [x] 看到畫面：視訊串流，多個鄉民端同時觀看。2026-11-25 用實機連續連線五次，每次都收到 1920×1080 的畫面；多個鄉民端同時觀看尚未實測。等超過 5 秒畫面還沒出來時，鄉民端會回到清單並說明卡在哪一步；這部分只有自動測試，還沒在真的連不上的網路上驗證
- [x] 鄉民端的視窗：跟著畫面比例、旋轉、左右反轉、放到最大（視窗控制已在真的 macOS 視窗上測過，實機尚未驗收）
- [x] 看板端的鏡頭控制：縮放、對焦、切換前後鏡頭。點擊對焦與切換鏡頭已在實機確認可以執行；縮放尚未實測
- [ ] 使用者體驗的調整（全部功能驗收後再做）
