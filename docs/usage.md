# 使い方ガイド

PaperFetchは、**Web GUI**、**コマンドライン (CLI)**、および **MCPサーバー** として利用できます。

## 1. Web GUI (推奨)

直感的な操作で論文の検索、選択、ダウンロード、そしてNotebookLMへのエクスポートが可能です。

### 起動方法

```bash
uv run paper-fetch-gui
```

コマンド実行後、ブラウザが自動的に開き、以下の画面が表示されます。

### 基本的なワークフロー

1.  **Search Settings**: サイドバーで検索対象（Arxiv, IEEE, 3GPPなど）とキーワード、取得件数を指定します。
2.  **Search**: 「Search」ボタンをクリックして検索を実行します。
3.  **Select**: 検索結果リストからダウンロードしたい論文にチェックを入れます。
4.  **Action**:
    - **Download**: 選択した論文をローカルにダウンロードします。
    - **Download & Convert**: ダウンロードに加え、Markdownへのテキスト変換を行います。
    - **NotebookLM**: ノートブックへアップロードします（[詳細はこちら](notebooklm.md)）。

---

## 2. CLI (コマンドライン)

スクリプト連携や手早い検索に便利です。

### 基本コマンド

```bash
# ヘルプの表示
paper-fetch --help

# 対話モード（ウィザード形式で検索条件を指定）
paper-fetch

# ワンライナー検索 (Arxivから "generative ai" を5件検索)
paper-fetch --source arxiv --query "generative ai" --limit 5
```

### 主なオプション

- `--source`: 検索ソース (`arxiv`, `ieee`, `threegpp`, `google_patents`*)
- `--query`: 検索キーワード
- `--limit`: 検索・ダウンロード件数の上限
- `--dry-run`: ダウンロードを行わず、検索結果の確認のみ行う

(* `google_patents` は現在 Experimental です)

---

## 3. MCP サーバー (AI Agent連携)

Claude DesktopやCursorなどのAIアシスタントからPaperFetchの機能を利用するためのサーバーです。

### 設定 (Claude Desktopの場合)

`claude_desktop_config.json` に以下を追加します：

```json
{
  "mcpServers": {
    "paper-fetch": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/paper-fetch",
        "run",
        "paper-fetch-mcp"
      ]
    }
  }
}
```

これにより、Claudeとの会話の中で「最新のLLMに関する論文を探して」といった指示が可能になります。
