# Ultron AI Agent (CLI Version)

A lightweight, local, terminal-based autonomous AI agent powered by **Ollama**. Equipped with function-calling tools for local file management, document indexing and search, safe Python code execution, and web/multimedia queries.

---

## ⚡ Features

- **Autonomous Tool-Calling Loop**: Uses Ollama's native tool calling capabilities to perform multi-step tasks (up to 15 execution steps per prompt).
- **📁 File Management**:
  - `read_file`: Inspect file contents.
  - `make_file`: Create new files (automatically creates `.bak` backups if overwritten).
  - `append_to_file`: Append data to existing files.
  - `edit_file`: Find and replace exact substrings within files safely.
  - `list_dir`: Explore directory contents.
- **📚 Local Document Search (Knowledge Base)**:
  - Simple, fast keyword search over indexed documents without heavyweight vector databases.
  - Supports `.pdf`, `.docx`, `.txt`, and `.md` formats.
  - Preserves exact source references (`[SOURCE X] file | chunk/page`).
- **🐍 Python Code Execution**:
  - `execute_python_code`: Runs standard library Python code directly in a captured stdout environment, ideal for mathematical calculations and algorithmic tasks.
- **🌐 Web & YouTube Search**:
  - `web_search`: Live search using DuckDuckGo, Wikipedia API fallbacks, and direct YouTube metadata scraping for music/video lookups.
- **🔒 Privacy First**: Runs entirely on your local machine with local LLMs (via Ollama).

---

## 📂 Project Structure

```text
.
├── start.sh                      # One-step launcher (Ollama check + venv activation + agent run)
├── requirements.txt              # Python dependencies
├── README.md                     # Project documentation
├── data/
│   ├── documents/                # Place your PDF, DOCX, TXT, or MD documents here
│   │   └── sample_innovation.txt # Sample document
│   └── index/                    # Generated document index (documents.json)
└── agent/
    ├── app.py                    # Main terminal agent loop and CLI entrypoint
    ├── code_running.py           # Safe Python code execution tool
    ├── files.py                  # File reading, writing, editing, and listing tools
    ├── web_tools.py              # Web and YouTube search tools
    └── knowledge/
        ├── config.py             # Knowledge chunking and directory settings
        ├── ingest.py             # Document parser and index generator
        ├── search.py             # Keyword search implementation
        └── test_search.py        # Standalone search CLI tester
```

---

## 📋 Prerequisites

1. **Python 3.10+**
2. **Ollama**: Installed and running on your system ([ollama.com](https://ollama.com)).
3. **Model**: A tool-capable model pulled in Ollama (default is `gemma4:latest`, or any model like `qwen2.5:latest`, `llama3.1:latest`, etc.):
   ```bash
   ollama pull gemma4:latest
   ```

---

## 🚀 Quick Start

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/your-username/Ultron-ai-agent-Cli-version-.git
cd Ultron-ai-agent-Cli-version-

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. (Optional) Ingest Internal Documents

Drop any documents (`.pdf`, `.docx`, `.txt`, `.md`) into `data/documents/` and build the index:

```bash
python3 -m agent.knowledge.ingest
```

### 3. Run the Agent

You can launch using the included startup script (which checks if the Ollama service is active and starts it if needed):

```bash
chmod +x start.sh
./start.sh
```

Or run directly with Python:

```bash
python3 agent/app.py
```

---

## 💬 Usage Examples

Once the agent is running in your terminal, simply enter your prompt:

- **Document Search**:
  ```text
  You: What are the three priority initiatives of the Innovation team?
  ```
- **File Creation & Modification**:
  ```text
  You: Create a python script named test_calc.py that computes prime numbers under 50.
  ```
- **Code Execution**:
  ```text
  You: Calculate the 45th Fibonacci number using Python code.
  ```
- **Web Search**:
  ```text
  You: Search the web for latest space discoveries this week.
  ```
- **Exit**:
  ```text
  You: exit
  ```

---

## ⚙️ Configuration

- **Change Ollama Model**: Edit `model="gemma4:latest"` in `agent/app.py` (line 78) to your preferred model name (e.g. `qwen2.5:7b`, `mistral`, `llama3.1`).
- **Knowledge Base Settings**: Configure chunk size, overlap, and top-k results in `agent/knowledge/config.py`:
  ```python
  CHUNK_SIZE = 1200
  CHUNK_OVERLAP = 150
  TOP_K = 5
  ```

---

## 🛠️ Requirements

- `ollama` — Ollama Python client
- `pypdf` — PDF document parsing
- `python-docx` — DOCX document parsing
- `ddgs` & `duckduckgo_search` — DuckDuckGo search integration
- `httpx` — HTTP client for web lookups
