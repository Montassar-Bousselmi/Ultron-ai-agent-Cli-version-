
import sys
from pathlib import Path

import ollama

agent_dir = Path(__file__).resolve().parent
project_root = agent_dir.parent

if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from files import read_file, make_file, append_to_file, edit_file, list_dir
from knowledge.search import search_documents
from code_running import execute_python_code
from web_tools import web_search

available_tools = {
    "read_file": read_file,
    "make_file": make_file,
    "append_to_file": append_to_file,
    "edit_file": edit_file,
    "list_dir": list_dir,
    "search_documents": search_documents,
    "execute_python_code": execute_python_code,
    "web_search": web_search
}

messages = [
    {
        "role": "system",
        "content": """You are an internal Innovation team AI assistant.

RULES:
1. Use search_documents whenever the user asks about information that may exist in internal documents.
2. The document search is a simple keyword search. Do not claim it is semantic search or RAG.
3. Do not invent facts. If the document search does not provide enough evidence, say so.
4. When answering from document search, preserve source labels exactly, e.g. [SOURCE 1].
5. At the end of a document-based answer, add a short 'Sources' section listing the source labels and locations used.
6. Use file tools only when the user explicitly asks to create, edit, read, append, or list files.
7. Keep answers concise but useful.
8. If the user asks you to write code, you may use execute_python_code to run it and return the output or error message
9. In the execute_python_code tool , only execute 100 percent safe code.
10. In the execute_python_code tool, dont pass variables except the code to execute and allways print the result.
11. In the execute_python_code tool, only use modules that are a part of the standard library and dont need external dependencies or installations.
12. if the user asks a math equation or a calculation, you may use execute_python_code to calculate it and return the output or error message
13. work with what you have , if the user asks you to do something that is safe and possible then do it.
14. If the user asks you to search the web, use the web_search tool to search the web and embed the interactive web page window in the conversation.
15. If the user asks for a song or music, use the web_search tool to find the song on YouTube and embed the music player window in the conversation.
16. If the user asks for a specific website or URL, search for it using the web_search tool to embed the web page window in the conversation.
"""
    }
]


def cleanup_history(chat_history: list):
    for msg in chat_history:
        if "tool_calls" in msg and msg["tool_calls"]:
            for tc in msg["tool_calls"]:
                args = tc.function.arguments
                if tc.function.name in ["make_file", "append_to_file", "edit_file"] and "content" in args:
                    if len(str(args["content"])) > 500:
                        args["content"] = "[CONTENT SAVED - OMITTED FOR FUTURE TURNS]"
        if msg.get("role") == "tool" and isinstance(msg.get("content"), str):
            if len(msg["content"]) > 2000:
                msg["content"] = msg["content"][:1500] + "\n...[TOOL OUTPUT OMITTED]..."


def agent_chat(user_input: str) -> str:
    messages.append({"role": "user", "content": user_input})
    max_steps = 15

    for step in range(max_steps):
        print(f"\n--- [Step {step + 1}/{max_steps}] Agent is working... ---")
        response = ollama.chat(
            model="gemma4:cloud",
            messages=messages,
            tools=[
                read_file,
                make_file,
                append_to_file,
                edit_file,
                list_dir,
                search_documents,
                execute_python_code,
                web_search
            ],
        )

        message = response.message

        if not message.tool_calls:
            messages.append(message)
            cleanup_history(messages)
            return message.content

        messages.append(message)

        for tool_call in message.tool_calls:
            func_name = tool_call.function.name
            args = tool_call.function.arguments
            print(f"-> Executing: {func_name} | {args}")

            if func_name not in available_tools:
                result = f"Error: Tool {func_name} not found."
            else:
                try:
                    result = available_tools[func_name](**args)
                except TypeError as e:
                    result = f"Action Failed: {e}. Retry with correct arguments."
                except Exception as e:
                    result = f"Action Failed: {e}"

            if result is None:
                result = "Action executed successfully."

            messages.append({
                "role": "tool",
                "name": func_name,
                "content": str(result),
            })

    cleanup_history(messages)
    return "Error: Agent reached maximum steps without resolving the task."


def main() -> None:
    print("Innovation AI Assistant. Type 'exit' to stop.")
    print("Tip: put documents in data/documents/ and run the ingestion command first.")
    while True:
        try:
            prompt = input("\nYou: ").strip()
            if prompt.lower() in {"exit", "quit"}:
                break
            if not prompt:
                continue
            print(f"\nAgent: {agent_chat(prompt)}\n")
        except (EOFError, KeyboardInterrupt):
            break


if __name__ == "__main__":
    main()
