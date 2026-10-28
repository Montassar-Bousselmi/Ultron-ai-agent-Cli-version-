import os
import shutil


def create_backup(file_path: str):
    if os.path.exists(file_path):
        shutil.copy(file_path, file_path + ".bak")


def read_file(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return f"Error: The file '{file_path}' was not found."
    except Exception as e:
        return f"Error: Could not read file. {e}"


def make_file(file_path: str, content: str) -> str:
    try:
        create_backup(file_path)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        return f"Success: File '{file_path}' created (backup saved if it existed)."
    except Exception as e:
        return f"Error: Could not create the file '{file_path}'. {e}"


def append_to_file(file_path: str, content: str) -> str:
    try:
        create_backup(file_path)
        with open(file_path, "a", encoding="utf-8") as file:
            file.write(content)
        return f"Success: Content appended to '{file_path}'."
    except Exception as e:
        return f"Error: Could not append to the file '{file_path}'. {e}"


def edit_file(file_path: str, search_string: str, replace_string: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        occurrences = content.count(search_string)
        if occurrences == 0:
            return f"Error: The exact search_string was not found in '{file_path}'."
        if occurrences > 1:
            return f"Error: The search_string was found {occurrences} times. Make it more specific."
        create_backup(file_path)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content.replace(search_string, replace_string))
        return f"Success: Modified '{file_path}'."
    except FileNotFoundError:
        return f"Error: The file '{file_path}' was not found."
    except Exception as e:
        return f"Error: Could not edit file. {e}"


def list_dir(path: str = ".") -> str:
    try:
        return f"Files in directory '{path}': " + ", ".join(os.listdir(path))
    except Exception as e:
        return f"Error reading directory: {e}"
