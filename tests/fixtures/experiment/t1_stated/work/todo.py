#!/usr/bin/env python3
"""A small command-line todo list."""

import json
import os
import sys

DEFAULT_PATH = "todo.json"


def data_path():
    return os.environ.get("TODO_FILE") or DEFAULT_PATH


def load_items():
    path = data_path()
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as handle:
        try:
            items = json.load(handle)
        except json.JSONDecodeError as error:
            raise SystemExit(f"error: {path} is not valid JSON ({error})")
    if not isinstance(items, list):
        raise SystemExit(f"error: {path} does not contain a list of items")
    return items


def save_items(items):
    path = data_path()
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(items, handle, indent=2)
    except OSError as error:
        raise SystemExit(f"error: cannot write {path} ({error})")


def cmd_add(text):
    if not text.strip():
        raise SystemExit("error: the item text must not be empty")
    items = load_items()
    next_id = max((item["id"] for item in items), default=0) + 1
    items.append({"id": next_id, "text": text, "completed": False})
    save_items(items)
    print(next_id)


def cmd_list():
    for item in load_items():
        state = "[x]" if item["completed"] else "[ ]"
        print(f"{item['id']} {state} {item['text']}")


def cmd_done(raw_id):
    if not raw_id.isdigit():
        raise SystemExit(f"error: {raw_id} is not a valid id")
    item_id = int(raw_id)
    items = load_items()
    for item in items:
        if item["id"] == item_id:
            item["completed"] = True
            save_items(items)
            return
    raise SystemExit(f"error: no item with id {item_id}")


def main(argv):
    if not argv:
        raise SystemExit("usage: todo.py add <text> | list | done <id>")
    command, rest = argv[0], argv[1:]
    if command == "add" and len(rest) == 1:
        cmd_add(rest[0])
    elif command == "list" and not rest:
        cmd_list()
    elif command == "done" and len(rest) == 1:
        cmd_done(rest[0])
    else:
        raise SystemExit("usage: todo.py add <text> | list | done <id>")


if __name__ == "__main__":
    main(sys.argv[1:])
