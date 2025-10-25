# projectree/cli.py
import argparse
from .core import generate_project_tree

def main():
    parser = argparse.ArgumentParser(
        description="Generate a simple project tree excluding ignored directories."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the project directory (default: current directory)."
    )
    parser.add_argument(
        "--ext",
        type=str,
        help="Comma-separated list of file extensions to include (e.g. .py,.js,.md)."
    )
    parser.add_argument(
        "--ignore",
        type=str,
        help="Comma-separated list of directories to ignore (e.g. node_modules,venv,build)."
    )
    parser.add_argument(
        "--save",
        type=str,
        help="Save the output tree to a file (e.g. tree.txt)."
    )

    args = parser.parse_args()

    extensions = tuple(e.strip() for e in args.ext.split(",")) if args.ext else None
    ignored_dirs = set(d.strip() for d in args.ignore.split(",")) if args.ignore else None

    tree = generate_project_tree(args.path, ignored_dirs, extensions)

    if args.save:
        with open(args.save, "w") as f:
            f.write(tree)
        print(f"✅ Tree saved to {args.save}")
    else:
        print(tree)
