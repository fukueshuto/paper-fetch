# トラブルシューティング

## NotebookLM 連携

### ブラウザが起動しない / エラーが出る
- **Patchrightの確認**: 本バージョンから `playwright` ではなく `patchright` を使用しています。
  ```bash
  uv run patchright install chromium
  ```
  を実行して、必要なバイナリがインストールされているか確認してください。
- **ゾンビプロセス**: ブラウザが正しく終了しなかった場合、バックグラウンドのChromeプロセスがロックファイル (`SingletonLock`) を掴んだままになることがあります。
  - PaperFetchは起動時にこれらを自動的にクリーンアップしようとしますが、解決しない場合は手動でChromeプロセスを終了してください (`pkill -f chrome` など)。

### ログインが維持されない
- ブラウザプロファイルは `~/.paper_fetch/browser_data` に保存されます。
- 初回起動時に手動でGoogleにログインしてください。2回目以降はCookieが再利用されます。

### アップロードボタンが見つからない
- NotebookLMのUI変更によりセレクタが一致しなくなる可能性があります。
- スクリプト実行中もブラウザ操作は可能です。手動で「ソースを追加」ボタンを押してファイル選択画面を出すことで、スクリプトのアップロード処理を続行させることができます（Human-in-the-loop）。

## API制限 (429 Error)
- Arxiv/IEEEへのアクセス頻度が高すぎると発生します。`config.toml` の `wait_time` を増やしてください。

## インストール
- **pdftotext**: `poppler` がシステムにインストールされている必要があります。
  - Mac: `brew install poppler`
  - Linux: `sudo apt install poppler-utils`
