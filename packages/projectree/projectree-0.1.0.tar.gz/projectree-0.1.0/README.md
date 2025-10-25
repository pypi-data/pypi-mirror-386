# projecttree

A lightweight Python utility to generate a clean project tree, excluding build and cache directories.

## Installation

```bash
pip install projecttree
(or locally:)
pip install -e .
Usage
from projecttree import generate_project_tree

tree = generate_project_tree(".")
print(tree)
Command Line

✅ Default behavior
projectree .
✅ With custom extensions
projectree . --ext .py,.md
✅ Ignoring custom folders
projectree . --ignore venv,__pycache__
✅ Save output to file
projectree . --save tree.txt

---

## 📜 Step 7: Add a License

File: `LICENSE`  
(Use MIT License as an example.)

```text
MIT License

Copyright (c) 2025 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
...