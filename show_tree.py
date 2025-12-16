from pathlib import Path

EXCLUDE_DIRS = {".venv", "__pycache__", ".git", ".mypy_cache", ".ruff_cache"}


def print_tree(path: Path, prefix: str = ""):
    entries = [
        e for e in sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        if e.name not in EXCLUDE_DIRS
    ]

    for index, entry in enumerate(entries):
        connector = "└── " if index == len(entries) - 1 else "├── "
        print(prefix + connector + entry.name)

        if entry.is_dir():
            extension = "    " if index == len(entries) - 1 else "│   "
            print_tree(entry, prefix + extension)


if __name__ == "__main__":
    root = Path(".").resolve()
    print(root.name)
    print_tree(root)
