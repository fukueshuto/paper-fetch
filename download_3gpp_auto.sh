#!/bin/zsh

# --- ユーザー設定項目 ---
# 3GPPのドキュメントが置かれているFTPサイトのURL
DOCS_URL="https://www.3gpp.org/ftp/tsg_ran/WG1_RL1/TSGR1_122b/Docs/"
# --- ユーザー設定項目ここまで ---


# --- スクリプト本体 ---
# ログファイル設定
ERROR_LOG_FILE="error_log.txt"
rm -f "$ERROR_LOG_FILE"
exec 2> "$ERROR_LOG_FILE"

# --- OSを自動判別 ---
OS_TYPE=$(uname -s)
if [[ "$OS_TYPE" == "Darwin" ]]; then
  SED_FLAG="-E"
elif [[ "$OS_TYPE" == "Linux" ]]; then
  SED_FLAG="-r"
else
  echo "❌ サポートされていないOSです: $OS_TYPE"
  exit 1
fi

# --- ヘルパー関数 ---
format_seconds() { local s=$1; printf "%dm %ds" $((s/60)) $((s%60)); }
format_bytes() { numfmt --to=iec-i --suffix=B --format="%.2f" "$1"; }
fetch_list_html() { if [[ "$OS_TYPE" == "Darwin" ]]; then curl -s "$1"; else wget -q -O - "$1"; fi; }

# --- 事前準備チェック ---
check_dependencies() {
  echo "🔎 必要なツールがインストールされているか確認します..."
  local missing_count=0
  local required_cmds=("unzip" "pandoc" "numfmt")
  [[ "$OS_TYPE" == "Linux" ]] && required_cmds+=("wget")

  for cmd in "${required_cmds[@]}"; do
    if ! command -v "$cmd" &> /dev/null; then
      echo "❗️ エラー: '$cmd' が見つかりません。"
      missing_count=$((missing_count + 1))
    fi
  done

  if (( missing_count > 0 )); then
    echo "\n必要なツールが不足しています。インストールしてください。"
    exit 1
  fi

  # --- 画像変換(WMF/EMF -> PNG)ツールの確認 ---
  if ! command -v inkscape &> /dev/null; then
      echo "   -> ⚠️ 'inkscape' が見つかりません。WMF/EMF等の古い画像形式は変換されません。(推奨: brew install --cask inkscape)"
      CAN_CONVERT_IMAGES=false
  else
      echo "   -> ✅ 画像変換ツール 'inkscape' を検出しました。"
      CAN_CONVERT_IMAGES=true
  fi

  # --- PDF変換エンジン(LibreOffice)の確認 ---
  SOFFICE_CMD=""
  if [[ "$OS_TYPE" == "Darwin" ]] && [ -x "/Applications/LibreOffice.app/Contents/MacOS/soffice" ]; then
      SOFFICE_CMD="/Applications/LibreOffice.app/Contents/MacOS/soffice"
      echo "   -> ✅ PDF変換エンジン 'LibreOffice' を検出しました。"
      CAN_CONVERT_PDF=true
  elif command -v soffice &> /dev/null; then
      SOFFICE_CMD=$(command -v soffice)
      echo "   -> ✅ PDF変換エンジン 'LibreOffice' (soffice) を検出しました。"
      CAN_CONVERT_PDF=true
  else
      echo "   -> ⚠️ 'LibreOffice' が見つかりません。PDF変換はスキップされます。(推奨: brew install --cask libreoffice)"
      CAN_CONVERT_PDF=false
  fi

  # --- unzipツールのエンコーディング対応確認 ---
  USE_ENCODING_FLAG=false
  if [[ "$OS_TYPE" == "Darwin" ]]; then
      if unzip -h 2>&1 | grep -- "-O" > /dev/null; then
          echo "   -> ✅ 高機能版 'unzip' を検出しました。"
          USE_ENCODING_FLAG=true
      else
          echo "   -> ⚠️ 標準 'unzip' を検出しました。(推奨: brew install unzip)"
      fi
  else
      USE_ENCODING_FLAG=true
  fi

  echo "✅ 必要なツールは揃っています。"
}

# --- ファイル処理関数 ---
# --- ファイル処理関数 ---
process_file() {
  local filepath="$1"
  local filename
  filename=$(basename "$filepath")

  if [[ "$filename" == *.zip ]]; then
      local zip_basename="${filename%.zip}"
      echo "   -> 🤐 Processing ZIP file: $filename"

      local temp_dir
      temp_dir=$(mktemp -d)
      local local_unzip_dir="$UNZIPPED_DIR/$zip_basename"
      mkdir -p "$local_unzip_dir"

      # -o フラグで常にファイルを上書きし、プロンプトで停止するのを防ぐ
      if [[ "$USE_ENCODING_FLAG" == true ]]; then
          unzip -q -o -O cp932 "$filepath" -d "$local_unzip_dir"
      else
          unzip -q -o "$filepath" -d "$local_unzip_dir"
      fi
      if [ $? -ne 0 ]; then
          echo "      -> ❗️ ERROR: 'unzip' command failed for $filename."; mv "$filepath" "$ZIP_ARCHIVE_DIR/"; return
      fi

      # 解凍したファイルの中からOffice文書を探して処理
      find "$local_unzip_dir" \( -iname "*.docx" -o -iname "*.pptx" -o -iname "*.xlsx" -o -iname "*.doc" -o -iname "*.ppt" -o -iname "*.xls" \) ! -path "*/__MACOSX/*" ! -name "._*" -print0 | while IFS= read -r -d '' office_path; do
          local office_filename=$(basename "$office_path")
          local base_name="${office_filename%.*}"
          local prefixed_basename="${zip_basename}_${base_name}"
          local prefixed_source_name="${zip_basename}_${office_filename}"

          cp "$office_path" "$OFFICE_SOURCE_DIR/$prefixed_source_name"
          echo "      -> ✅ Found & Copied: $office_filename"

          case "$office_filename" in
            *.docx)
              # --- 1. PandocでMarkdownに変換 ---
              echo "         -> 📝 Converting to Markdown (Pandoc)..."
              local media_temp_dir="$temp_dir/media"
              pandoc -f docx -t markdown "$OFFICE_SOURCE_DIR/$prefixed_source_name" --extract-media="$temp_dir" -o "$MD_DIR/$prefixed_basename.md"
              if [ $? -ne 0 ]; then
                  echo "         -> ❗️ WARNING: Pandoc failed to convert '$office_filename' to Markdown."
              elif [ "$CAN_CONVERT_IMAGES" = true ]; then
                  # WMF/EMF画像をPNGに変換
                  find "$media_temp_dir" \( -iname "*.wmf" -o -iname "*.emf" \) -exec sh -c 'inkscape "$1" --export-type="png" --export-filename="${1%.*}.png" >/dev/null 2>&1' sh {} \;
              fi

              # --- 2. LibreOfficeでPDFに変換 ---
              if [ "$CAN_CONVERT_PDF" = true ]; then
                  echo "         -> 📄 Converting to PDF (LibreOffice)..."
                  local temp_profile_dir
                  temp_profile_dir=$(mktemp -d)

                  # タイムアウトと一時プロファイルを指定して実行
                  gtimeout 60s "$SOFFICE_CMD" \
                    -env:UserInstallation="file://$temp_profile_dir" \
                    --headless \
                    --convert-to pdf "$OFFICE_SOURCE_DIR/$prefixed_source_name" \
                    --outdir "$PDF_DIR" >/dev/null 2>&1

                  # タイムアウトした場合、$? は 124 になる
                  if [ $? -ne 0 ]; then
                      echo "         -> ❗️ WARNING: LibreOffice failed to convert (or timed out) for '$office_filename'."
                  else
                      # LibreOfficeが出力したファイル名をスクリプトの命名規則に合わせてリネーム
                      mv "$PDF_DIR/${office_filename%.*}.pdf" "$PDF_DIR/$prefixed_basename.pdf" 2>/dev/null
                  fi
                  # 一時プロファイルを削除
                  rm -rf "$temp_profile_dir"
              fi
              converted_count=$((converted_count + 1))
              ;;
            *)
              echo "      -> ℹ️ Skipping conversion for legacy format file: $office_filename"
              ;;
          esac
      done

      rm -rf "$temp_dir"
      mv "$filepath" "$ZIP_ARCHIVE_DIR/"
  else
      echo "   -> 📚 Moving non-zip file to _OTHERS/"
      mv "$filepath" "$OTHERS_DIR/"
  fi
}

# --- メイン処理開始 ---
check_dependencies
echo "---"

# --- 出力ディレクトリ作成 ---
MEETING_NAME=$(echo "$DOCS_URL" | rev | cut -d'/' -f3 | rev)
OUTPUT_DIR="${MEETING_NAME}_Docs"
UNZIPPED_DIR="_UNZIPPED"; OFFICE_SOURCE_DIR="_ALL_OFFICE_SOURCE"; PDF_DIR="_ALL_PDF"; MD_DIR="_ALL_MD"; OTHERS_DIR="_OTHERS"; ZIP_ARCHIVE_DIR="_ARCHIVE_ZIP"

mkdir -p "$OUTPUT_DIR"; cd "$OUTPUT_DIR" || exit
mkdir -p "$UNZIPPED_DIR" "$OFFICE_SOURCE_DIR" "$PDF_DIR" "$MD_DIR" "$OTHERS_DIR" "$ZIP_ARCHIVE_DIR"

echo "📂 保存先ディレクトリ: $(pwd)"
echo "---"
echo "📡 サーバーからファイルリストを取得しています..."

URL_LIST=$(fetch_list_html "$DOCS_URL" | grep '<a class="file"' | sed $SED_FLAG 's/.*href="([^"]+)".*/\1/' | tr -d '\r' | grep '.')
url_array=("${(@f)URL_LIST}")
total_files=${#url_array[@]}

echo "✅ $total_files 個のファイルが見つかりました。"
echo "---"

# --- カウンタ ---
start_time=$(date +%s); success_count=0; skip_count=0; fail_count=0; total_bytes=0; converted_count=0; failed_urls=()

# --- メインループ ---
for (( i=1; i<=${total_files}; i++ )); do
  url=${url_array[i]}
  current_count=$i
  file_encoded=$(basename "$url")
  file_decoded=$(printf '%b' "${file_encoded//%/\\x}")

  # --- レジューム機能 ---
  # 処理が完了し、アーカイブ済みのファイルは完全にスキップする
  if [ -f "$ZIP_ARCHIVE_DIR/$file_decoded" ]; then
    echo "✅ [ $current_count / $total_files ] Skipping already processed: $file_decoded"
    skip_count=$((skip_count + 1))
    continue # continueコマンドでこのファイルの処理を飛ばし、次のループに進む
  fi

  local target_file_to_process=""

  # --- ダウンロード済みか確認 ---
  # 中断した場合など、ファイルがローカルに存在すればダウンロードは省略
  if [ -f "$file_decoded" ]; then
    echo "🔄 [ $current_count / $total_files ] Processing existing file: $file_decoded"
    target_file_to_process="$file_decoded"
  else
    # --- 未ダウンロードならダウンロード ---
    echo "📥 [ $current_count / $total_files ] Downloading: $file_decoded"
    if [[ "$OS_TYPE" == "Darwin" ]]; then curl -# -L -O "$url"; else wget --show-progress -P . "$url"; fi
    exit_code=$?

    if [ "$exit_code" -ne 0 ]; then
      fail_count=$((fail_count + 1)); failed_urls+=("$url"); echo "❗️ ダウンロード失敗。"; continue
    else
      success_count=$((success_count + 1))
      file_size=$(stat -f%z "$file_encoded" 2>/dev/null || stat -c%s "$file_encoded" 2>/dev/null)
      total_bytes=$((total_bytes + file_size))
      [ "$file_encoded" != "$file_decoded" ] && mv "$file_encoded" "$file_decoded"
      target_file_to_process="$file_decoded"
    fi
  fi

  # --- ファイル処理の実行 ---
  if [ -n "$target_file_to_process" ]; then
      process_file "$target_file_to_process"
  fi
done
# --- 最終レポート ---
final_elapsed_time=$(( $(date +%s) - start_time ))
echo "\n🎉 すべての処理が完了しました。"
echo "\n--- [ 最終レポート ] --------------------------------------------------"
echo "ダウンロード成功: $success_count ファイル"
echo "処理済み(スキップ含む): $skip_count ファイル"
echo "失敗: $fail_count ファイル"
echo "変換されたOfficeファイル数: $converted_count"
echo ""
echo "合計ダウンロードサイズ: $(format_bytes $total_bytes)"
echo "合計所要時間: $(format_seconds $final_elapsed_time)"
echo "----------------------------------------------------------------------"

if (( fail_count > 0 )); then
  echo "\n--- [ 失敗したファイルリスト ] --------------------------------------"
  for failed_url in "${failed_urls[@]}"; do echo "$failed_url"; done
  echo "----------------------------------------------------------------------"
fi