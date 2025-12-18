# PaperFetch

[Japanese](README.md) | [Feature Details](docs/features.md) | [Developer Guide](docs/design.md) | [Troubleshooting](docs/troubleshooting.md)

PaperFetch is a powerful tool to search and download academic papers and technical specifications from **Arxiv**, **IEEE Xplore**, and **3GPP**.

## Key Features

- **Multi-Source Search**: Arxiv, IEEE Xplore, and 3GPP support.
- **Patents (USPTO)**:
  - **Status**: ⚠️ **Experimental / Unverified**
  - Implementation is pending API key access for debugging. Currently considered unstable.
- **NotebookLM Integration (Enhanced)**:
  - Auto-upload PDFs to Google NotebookLM.
  - **Direct Open**: Specify a Notebook ID to append directly to an existing notebook.
  - **Session Resume**: Saves session info (`notebooklm_session.json`) for easy workflow resumption.
- **Advanced Config**: `config.toml` support and setup wizard.
- **Document Conversion**: PDF-to-Markdown conversion.

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (Recommended)
- **For NotebookLM**:
    - `patchright` (Stealth browser automation)

## Installation

### Recommended: uv tool

```bash
uv tool install .
```

### Setup for NotebookLM (Patchright)

If you plan to use the NotebookLM feature, install the necessary browser binaries:

```bash
uv run patchright install chromium
```

## Usage

### Web GUI

```bash
paper-fetch-gui
```

In the "Export Actions" tab:
- **NotebookLM**: Choose to create a new notebook or add to an existing one. You can now input a **Notebook ID** for direct access.

### CLI

```bash
paper-fetch --source arxiv --query "AI Agents"
```

For more details, see [Feature Details](docs/features.md).
