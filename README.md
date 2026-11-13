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
| `window_manager` | 0.6.0（尚未加入，鄉民端做視窗功能時才會用到） | 0.7.0 要求 Flutter 3.50 |

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
- [ ] 找到看板：看板端註冊／撤銷註冊，鄉民端的看板清單
- [ ] 看到畫面：視訊串流，多個鄉民端同時觀看
- [ ] 鄉民端的視窗：跟著畫面比例、旋轉、左右反轉、放到最大
- [ ] 看板端的鏡頭控制：縮放、對焦、切換前後鏡頭
