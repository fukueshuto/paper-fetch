# PaperFetch

PaperFetchは、ArxivおよびIEEE Xploreから学術論文のPDFを検索・ダウンロードするためのツールです。コマンドラインインターフェース（CLI）とModel Context Protocol（MCP）サーバーの両方を提供しており、LLMワークフローへの統合が容易です。

## 機能

- **Arxiv連携**: 公式Arxiv APIを使用して論文を検索・ダウンロードします。
- **IEEE Xplore連携**: Rest APIとrequestsを使用して論文を検索・ダウンロードします（Open Accessフィルタリング対応）。
- **CLIツール**: 論文の検索と一括ダウンロードを行うための対話型コマンドラインツールです。
- **MCPサーバー**: LLMエージェント向けに `search_papers` および `download_paper` ツールを公開します。

## 前提条件

- Python 3.13以上
- [uv](https://github.com/astral-sh/uv) （依存関係管理に推奨）

## インストール

### 方法 1: pipx / uv tool (推奨)

システム環境を汚さずにインストールできます。

**一般ユーザー (pipx):**
```bash
pipx install .
# または GitHub から直接:
# pipx install git+https://github.com/yourusername/paper-fetch.git
```

**uv ユーザー:**
```bash
uv tool install .
# または GitHub から直接:
# uv tool install git+https://github.com/yourusername/paper-fetch.git
```

### 方法 2: Docker

Dockerイメージをビルドして利用することも可能です。

```bash
docker build -t paper-fetch .
```

### 方法 3: 開発者向け (uv)

リポジトリをクローンして開発を行う場合:

```bash
git clone <repository-url>
cd paper-fetch
uv sync
```

## 使い方

インストール後、以下のコマンドが利用可能です。

### CLI

ターミナルから直接論文を検索・ダウンロードできます。

```bash
# 対話モード
paper-fetch
```

### コマンドライン引数モード

**Arxivの検索:**
```bash
uv run paper-fetch --source arxiv --query "generative ai" --search-limit 5
```

**IEEE Xploreの検索:**
```bash
uv run paper-fetch --source ieee --query "machine learning" --search-limit 5 --open-access-only
```

**Docker の場合:**
```bash
docker run -v $(pwd)/downloads:/app/downloads paper-fetch --source arxiv --query "AI"
```

**オプション:**
- `--source`: `arxiv` または `ieee` （必須）
- `--query`: 検索クエリ文字列 （必須）
- `--search-limit`: 検索する最大結果数 （デフォルト: 10, `0`で無制限）
- `--download-limit`: ダウンロードする最大結果数 （デフォルト: 無制限）
- `--output`: PDF保存先ディレクトリ （デフォルト: `downloads`）
- `--downloadable-only`: ダウンロード可能な論文のみを表示
- `--open-access-only`: Open Access論文のみを検索（IEEEのみ）
- `--sort-by`: ソート基準 (`relevance` または `date`, デフォルト: `relevance`)
- `--sort-order`: ソート順 (`desc` または `asc`, デフォルト: `desc`)
- `--start-year`: 検索開始年 (例: 2020)
- `--end-year`: 検索終了年 (例: 2024)
- `--export`: 検索結果をJSONファイルにエクスポート (例: `results.json`)
- `--from-file`: JSONファイルから論文情報を読み込んでダウンロード (例: `results.json`)

### Web GUI

ブラウザベースのGUIを使用して、より直感的に検索とダウンロードを行えます。

```bash
paper-fetch-gui
```

**Docker の場合:**
```bash
docker run -p 8501:8501 -v $(pwd)/downloads:/app/downloads paper-fetch paper-fetch-gui
```
ブラウザで `http://localhost:8501` にアクセスしてください。

### MCPサーバー

LLMクライアント（Claude Desktop, VS Codeなど）でPaperFetchをMCPサーバーとして使用する場合。

**コマンド:** `paper-fetch-mcp`

#### Claude Desktop 設定例
`claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "paper-fetch": {
      "command": "paper-fetch-mcp",
      "args": []
    }
  }
}
```
※ `pipx` や `uv tool` でインストールしていれば、パスが通っているためフルパス指定は不要です。

**利用可能なツール:**
- `search_papers(source, query, limit, open_access_only)`: 論文を検索します。
- `download_paper(url, title, authors, year, save_dir)`: 特定の論文をダウンロードします。

## プロジェクト構成

- `src/paper_fetch/cli.py`: CLIのエントリーポイント
- `src/paper_fetch/server.py`: MCPサーバーのエントリーポイント
- `src/paper_fetch/fetchers/`: ArxivおよびIEEEの取得ロジック
- `downloads/`: ダウンロードされたPDFのデフォルト保存先

## 安全な利用とレート制限について

大量の論文を短時間にダウンロードすると、提供元（Arxiv, IEEE）からIPブロックなどの制限を受ける可能性があります。以下の点に注意してご利用ください。

- **検索リミットの活用**: デフォルトでは検索結果は10件に制限されています。無制限（`0` または `all`）に設定する場合は十分ご注意ください。
- **Hit Count機能**: CLIの対話モードでは、実際に検索・ダウンロードを行う前に「Check Hit Count」機能を使用して、対象件数を確認することをお勧めします。
- **ダウンロード間隔**: ツール内部で以下の待機時間を設けています。
    - **検索**: 3.0秒 + ランダム待機 (0.0〜2.0秒) = **約3.0〜5.0秒**
    - **ダウンロード**: 20.0秒 + ランダム待機 (10.0〜40.0秒) = **約30.0〜60.0秒**
    - GUIではリアルタイムの待機状況が表示されますが、大量のダウンロードには時間がかかることを予めご了承ください。
