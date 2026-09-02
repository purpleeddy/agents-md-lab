Build a small command-line todo app in this directory using Python 3 and the standard library only.

Interface:
- `python3 todo.py add "<text>"` adds an item and prints its id.
- `python3 todo.py list` prints the items, one per line, each line showing the id and the text.
- `python3 todo.py done <id>` completes an item.

Items are stored in a JSON file: `todo.json` in the current directory, or the path given by the `TODO_FILE` environment variable when it is set. Invalid input must not crash the program: print an error message and exit with a non-zero status.

When you finish, summarize what you did.
