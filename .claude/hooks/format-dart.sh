#!/bin/sh
# Claude 改完檔案後自動執行：如果改的是 .dart 檔，就用固定版本的 Dart 排版。

# 從標準輸入的 JSON 取出被修改的檔案路徑
f=$(jq -r '.tool_input.file_path')

# 只處理 .dart 檔，其他檔案什麼都不做
case "$f" in
  *.dart) "$HOME/.pub-cache/bin/fvm" dart format "$f" ;;
esac
