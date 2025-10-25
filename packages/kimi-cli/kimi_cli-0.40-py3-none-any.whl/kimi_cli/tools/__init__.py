import json
from pathlib import Path

import streamingjson
from kosong.utils.typing import JsonType

from kimi_cli.utils.string import shorten_middle


def extract_subtitle(lexer: streamingjson.Lexer, tool_name: str) -> str | None:
    try:
        curr_args: JsonType = json.loads(lexer.complete_json())
    except json.JSONDecodeError:
        return None
    if not curr_args:
        return None
    subtitle: str = ""
    match tool_name:
        case "Task":
            if not isinstance(curr_args, dict) or not curr_args.get("description"):
                return None
            subtitle = str(curr_args["description"])
        case "SendDMail":
            return "El Psy Kongroo"
        case "Think":
            if not isinstance(curr_args, dict) or not curr_args.get("thought"):
                return None
            subtitle = str(curr_args["thought"])
        case "SetTodoList":
            if not isinstance(curr_args, dict) or not curr_args.get("todos"):
                return None
            if not isinstance(curr_args["todos"], list):
                return None
            for todo in curr_args["todos"]:
                if not isinstance(todo, dict) or not todo.get("title"):
                    continue
                subtitle += f"• {todo['title']}"
                if todo.get("status"):
                    subtitle += f" [{todo['status']}]"
                subtitle += "\n"
            return "\n" + subtitle.strip()
        case "Bash":
            if not isinstance(curr_args, dict) or not curr_args.get("command"):
                return None
            subtitle = str(curr_args["command"])
        case "ReadFile":
            if not isinstance(curr_args, dict) or not curr_args.get("path"):
                return None
            subtitle = _normalize_path(str(curr_args["path"]))
        case "Glob":
            if not isinstance(curr_args, dict) or not curr_args.get("pattern"):
                return None
            subtitle = str(curr_args["pattern"])
        case "Grep":
            if not isinstance(curr_args, dict) or not curr_args.get("pattern"):
                return None
            subtitle = str(curr_args["pattern"])
        case "WriteFile":
            if not isinstance(curr_args, dict) or not curr_args.get("path"):
                return None
            subtitle = _normalize_path(str(curr_args["path"]))
        case "StrReplaceFile":
            if not isinstance(curr_args, dict) or not curr_args.get("path"):
                return None
            subtitle = _normalize_path(str(curr_args["path"]))
        case "SearchWeb":
            if not isinstance(curr_args, dict) or not curr_args.get("query"):
                return None
            subtitle = str(curr_args["query"])
        case "FetchURL":
            if not isinstance(curr_args, dict) or not curr_args.get("url"):
                return None
            subtitle = str(curr_args["url"])
        case _:
            subtitle = "".join(lexer.json_content)
    if tool_name not in ["SetTodoList"]:
        subtitle = shorten_middle(subtitle, width=50)
    return subtitle


def _normalize_path(path: str) -> str:
    cwd = str(Path.cwd().absolute())
    if path.startswith(cwd):
        path = path[len(cwd) :].lstrip("/\\")
    return path
