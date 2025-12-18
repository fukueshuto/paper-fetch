# 機能詳細ドキュメント

## 1. 対応データソース
- **Arxiv**: `arxiv` ライブラリ使用。
- **IEEE Xplore**: Open Access対応。
- **3GPP**: Google検索ベースのドキュメント検索およびURL指定ダウンロード。
- **USPTO (特許)**:
  - ⚠️ **現在未検証 (Experimental)**
  - PatentsView APIを使用した検索機能をコードベースに含んでいますが、開発者がAPIキーを取得できていないため、**動作確認が完了していません**。利用する場合は自己責任でお願いします（または修正PRを歓迎します）。

## 2. NotebookLM 連携機能 (Enhanced)

PaperFetchは、Google NotebookLMへのPDFアップロードを自動化します。v0.2.0以降、より安定性と隠匿性の高い `patchright` を採用しています。

### 主な機能強化
- **Patchright採用**: 従来のPlaywrightに比べ、Bot検知を回避しやすい `patchright` に移行しました。
- **セッションレジューム**: アップロード完了後、`notebooklm_session.json` をダウンロードフォルダに保存します。ここには作成されたノートブックのIDやURLが記録されます。
- **ID指定オープン**: GUIで「Existing Notebook」モードを選択した際、ノートブックIDを指定することで、ダッシュボードを経ずに直接対象のノートブックを開くことができます。
- **プロセス管理**: 競合するChromeプロセスや残留したロックファイルを自動的にクリーンアップし、安定した起動を実現しています。

### 使用フロー
1. GUIで論文を検索・ダウンロード。
2. Checkboxで必要な論文を選択。
3. "Export Actions" -> "NotebookLM" を選択。
4. **新規作成**: "Create New Notebook" を選択。
5. **既存追加**: "Add to Existing Notebook" を選択し、必要ならばNotebook IDを入力。
6. ブラウザが起動し、自動操作が実行されます（ログインが必要な場合は手動で介入可能）。

## 3. ドキュメント変換
- **PDF -> Markdown**: `marker` (高精度) または `pdftotext` (高速) を利用可能。
- **3GPP変換**: `.doc`/`.docx` をLibreOfficeでPDFに自動変換。

## 4. 設定とレート制限
`config.toml` により、検索・ダウンロード時の待機時間（Jitter）を詳細に設定可能です。IPブロック回避のため、デフォルトでは数十秒の待機時間が設定されています。
