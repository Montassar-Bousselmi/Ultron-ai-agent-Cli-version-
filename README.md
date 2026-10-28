<div align="center">

# 🤖 Ultron AI Agent (CLI Version)

**A modular, fully local, terminal-native autonomous agent powered by Ollama.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20Inference-black?logo=ollama&logoColor=white)](https://ollama.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)]()

*Execute safe code, search local document archives, manage local files, and scrape real-time web results — 100% locally and privately.*

---

</div>

## 📑 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Key Capabilities & Tools](#-key-capabilities--tools)
- [Project Layout](#-project-layout)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Document Knowledge Base (RAG-Lite)](#-document-knowledge-base-rag-lite)
- [Terminal Walkthrough](#-terminal-walkthrough)
- [Configuration](#-configuration)
- [Context & History Management](#-context--history-management)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## 🌟 Overview

**Ultron AI Agent** is an autonomous terminal-based AI assistant built for local-first workflows. It connects directly to your local **Ollama** runtime and uses function-calling to autonomously plan, execute multi-step tasks, reflect on tool outputs, and provide grounded answers.

Unlike heavy agent frameworks, Ultron is lightweight, zero-bloat, and transparent: every tool execution is visible directly in the terminal stream.

---

## 🧠 Architecture

Ultron uses an iterative **ReAct (Reason + Act)** loop with a maximum limit of 15 execution steps per prompt:

```
                  ┌───────────────────────────────┐
                  │          User Prompt          │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                     ┌────────────────────────┐
          ┌─────────►│  Ollama Chat / LLM     │◄────────┐
          │          │  (gemma4, qwen2.5...)  │         │
          │          └────────────┬───────────┘         │
          │                       │                     │
          │             Tool Call Requested?            │
          │                       │                     │
      Tool Output          Yes ───┴─── No               │
          │                 │          │                │
          │                 ▼          ▼                │
          │          Execute Tool  Final Output         │
          │                 │          │                │
          └─────────────────┴──────────┴────────────────┘
```

---

## 🛠️ Key Capabilities & Tools

Ultron provides 8 specialized tools across 4 core modules:

| Module | Tool | Description | Safety & Key Features |
| :--- | :--- | :--- | :--- |
| **Filesystem** | `read_file(file_path)` | Read entire contents of a file | Safe path reading with error handling |
| | `make_file(file_path, content)` | Create or overwrite a file | **Auto-backup**: creates `.bak` before overwrite |
| | `append_to_file(file_path, content)` | Append text to end of file | Auto-backup copy created before append |
| | `edit_file(file_path, search, replace)` | Precise text search-and-replace | Strict single-occurrence check avoids accidental edits |
| | `list_dir(path=".")` | List files and directories | Lists directory entries for navigation |
| **Knowledge Base** | `search_documents(query)` | Fast keyword search over indexed files | Ingests `.pdf`, `.docx`, `.txt`, `.md` with chunking & source tracking |
| **Code Runner** | `execute_python_code(code)` | Execute Python code in isolated scope | Standard library only; captures stdout output safely |
| **Web Search** | `web_search(query)` | Live DuckDuckGo, Wikipedia & YouTube | Returns summaries, direct URLs, and embedded widgets |

---

## 📂 Project Layout

```text
Ultron-ai-agent-Cli-version-/
├── start.sh                      # Shell launch script with Ollama service check
├── requirements.txt              # Minimal project dependencies
├── README.md                     # Documentation
├── data/
│   ├── documents/                # Place source documents here (.pdf, .docx, .txt, .md)
│   │   └── sample_innovation.txt # Sample knowledge base document
│   └── index/                    # Generated document index (documents.json)
└── agent/
    ├── app.py                    # Terminal agent entrypoint & ReAct orchestrator
    ├── code_running.py           # Python code runner with stdout capture
    ├── files.py                  # File management with automatic backup system
    ├── web_tools.py              # Web search, Wikipedia lookup & YouTube extractors
    └── knowledge/
        ├── config.py             # Ingestion parameters (chunk size, overlap, paths)
        ├── ingest.py             # Document parser and search index builder
        ├── search.py             # Normalized keyword ranking engine
        └── test_search.py        # Standalone search CLI tester
```

---

## 📋 Prerequisites

1. **Python 3.10+**
2. **Ollama**: Installed and running ([Download Ollama](https://ollama.com/download))
3. **Model**: An Ollama model with tool-calling support. Recommended:
   ```bash
   ollama pull gemma4:latest
   # Or alternatives:
   ollama pull qwen2.5:7b
   ollama pull llama3.1:8b
   ```

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Montassar-Bousselmi/Ultron-ai-agent-Cli-version-.git
cd Ultron-ai-agent-Cli-version-
```

### 2. Setup Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the Agent

**Option A — Automated Launcher (Recommended):**
The `start.sh` script verifies Ollama is running, starts it in the background if necessary, activates the virtual environment, and starts Ultron:
```bash
chmod +x start.sh
./start.sh
```

**Option B — Direct Python Execution:**
```bash
python3 agent/app.py
```

---

## 📚 Document Knowledge Base (RAG-Lite)

Ultron includes a lightweight, local document indexing and search engine that does not require complex vector databases or remote embedding APIs.

### How it Works:
1. **Extraction**: Parses `.pdf` (via `pypdf`), `.docx` (via `python-docx`), `.txt`, and `.md` files.
2. **Sliding-Window Chunking**:
   - `CHUNK_SIZE`: 1200 characters
   - `CHUNK_OVERLAP`: 150 characters
3. **Normalized Keyword Ranking**: Computes relevancy scores by filtering out stopwords, normalizing accents/diacritics, and weighting title matches.
4. **Source Attribution**: Retains source document name and exact page or chunk number in every answer.

### Ingesting Documents:
Add your documents into `data/documents/`, then run:
```bash
python3 -m agent.knowledge.ingest
```

You can test searches independently without launching the full agent:
```bash
python3 agent/knowledge/test_search.py
```

---

## 💻 Terminal Walkthrough

Here is an example session showing Ultron resolving a complex, multi-step prompt:

```text
Innovation AI Assistant. Type 'exit' to stop.
Tip: put documents in data/documents/ and run the ingestion command first.

You: Check data/documents/ for the Innovation team goals and save a 2-sentence summary to summary.txt.

--- [Step 1/15] Agent is working... ---
-> Executing: search_documents | {'query': 'Innovation team goals initiatives'}

--- [Step 2/15] Agent is working... ---
-> Executing: make_file | {'file_path': 'summary.txt', 'content': 'The Innovation team prioritizes UX research automation, CX knowledge management, and partner tracking.\nThese initiatives focus on reducing manual preparation time and centralizing internal notes.'}

--- [Step 3/15] Agent is working... ---
Agent: I have reviewed the internal document on Innovation initiatives and saved a two-sentence summary into `summary.txt`.

Sources:
- [SOURCE 1] sample_innovation.txt (chunk 0)

You: exit
```

---

## ⚙️ Configuration

### Switching the Ollama Model
In `agent/app.py` (around line 72), change the `model` argument:
```python
response = ollama.chat(
    model="qwen2.5:7b",  # Change to your preferred local model
    messages=messages,
    tools=[...],
)
```

### Ingestion & Search Parameters
In `agent/knowledge/config.py`:
```python
CHUNK_SIZE = 1200         # Maximum character size per chunk
CHUNK_OVERLAP = 150       # Overlapping characters between adjacent chunks
TOP_K = 5                 # Maximum number of source excerpts returned
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
```

### Customizing Instructions & Persona
Modify the `system` message in `agent/app.py` (lines 25–49) to add or alter rules, persona, and output style.

---

## 🧹 Context & History Management

To keep interactions within local LLM context limits and avoid token bloat during long sessions:
- File write tool inputs (`make_file`, `append_to_file`, `edit_file`) exceeding 500 characters are compacted in message history after execution.
- Tool responses longer than 2,000 characters are trimmed to 1,500 characters in conversation history.
- The agent loop has a safety threshold of **15 maximum steps per prompt** to prevent infinite execution loops.

---

## ❓ Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `Connection refused` | Ollama service is not running | Run `ollama serve` in a separate terminal or use `./start.sh` |
| `model not found` | The requested model is not downloaded | Run `ollama pull gemma4:latest` (or model specified in `app.py`) |
| `ModuleNotFoundError` | Virtual environment not active | Run `source .venv/bin/activate` before starting |
| Agent doesn't call tools | Model may lack function calling support | Use a model with tool-calling capabilities like `gemma4`, `qwen2.5`, or `llama3.1` |
| `No readable documents found` | Index has not been created | Run `python3 -m agent.knowledge.ingest` after adding documents |

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
