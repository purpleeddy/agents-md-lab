#!/usr/bin/env python3
import json
import os
import sys

PATH = os.environ.get("TODO_FILE", "todo.json")


def load():
    if not os.path.exists(PATH):
        return []
    with open(PATH, encoding="utf-8") as handle:
        return json.load(handle)


def save(items):
    with open(PATH, "w", encoding="utf-8") as handle:
        json.dump(items, handle)


def main(argv):
    if not argv:
        print("usage: todo.py add|list|done|remove", file=sys.stderr)
        return 1
    command = argv[0]
    items = load()
    if command == "add":
        if len(argv) != 2 or not argv[1].strip():
            print("error: add needs a non-empty text", file=sys.stderr)
            return 1
        item_id = len(items) + 1
        items.append({"id": item_id, "text": argv[1], "completed": False})
        save(items)
        print(item_id)
        return 0
    if command == "list":
        for item in items:
            flag = "x" if item["completed"] else " "
            print(f"{item['id']} [{flag}] {item['text']}")
        return 0
    if command == "done":
        if len(argv) != 2 or not argv[1].isdigit():
            print("error: done needs a numeric id", file=sys.stderr)
            return 1
        for item in items:
            if item["id"] == int(argv[1]):
                item["completed"] = True
                save(items)
                return 0
        print("error: unknown id", file=sys.stderr)
        return 1
    if command == "remove":
        if len(argv) != 2 or not argv[1].isdigit():
            print("error: remove needs a numeric id", file=sys.stderr)
            return 1
        kept = [item for item in items if item["id"] != int(argv[1])]
        save(kept)
        return 0
    print("error: unknown command", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
