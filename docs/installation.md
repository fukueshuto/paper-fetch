# インストールガイド

このドキュメントでは、PaperFetchのインストール方法と初期設定について詳しく説明します。

## 前提条件

- **Python**: 3.12 以上
- **パッケージマネージャー**: [uv](https://github.com/astral-sh/uv) (推奨) または pip

> [!NOTE]
> 本プロジェクトは `uv` での管理を強く推奨しています。依存関係の解決や仮想環境の管理が高速かつ確実に行えます。

## インストール手順

### 1. `uv tool` を使用する場合 (推奨)

CLIツールとしてシステム全体で利用可能にする最も簡単な方法です。

```bash
# カレントディレクトリからインストール (開発版)
uv tool install .

# または GitHubから直接インストール
uv tool install git+https://github.com/fukueshuto/paper-fetch.git
```

### 2. リポジトリをクローンして使用する場合 (開発者向け)

```bash
git clone https://github.com/fukueshuto/paper-fetch.git
cd paper-fetch
uv sync
```

## 初期設定

### ブラウザ自動化ツールの準備 (NotebookLM連携用)

PaperFetchのNotebookLM連携機能（自動アップロードなど）を使用する場合は、ブラウザ操作用のツール `patchright` のセットアップが必要です。

PaperFetchインストール後、以下のコマンドを実行してブラウザバイナリをダウンロードしてください：

```bash
uv run patchright install chromium
```

> [!IMPORTANT]
> この手順をスキップすると、NotebookLMへのアップロード機能実行時にエラーが発生します。

### 設定ファイルの生成

PaperFetchの動作設定（デフォルトの検索先やダウンロード制限、APIキーなど）を管理する `config.toml` を作成することをお勧めします。

```bash
# 対話形式で設定ファイルを作成
paper-fetch --init-config
```

詳細は [設定ガイド](configuration.md) を参照してください。

## アップデート方法

`uv tool` でインストールした場合：

```bash
uv tool upgrade paper-fetch
```
