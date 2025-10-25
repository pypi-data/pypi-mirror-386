# projectree/core.py
import os

def generate_project_tree(project_path: str, ignored_dirs=None, extensions=None):
    """
    Generate a text-based tree of a project, including only relevant files.

    Args:
        project_path (str): The root directory of the project.
        ignored_dirs (set, optional): Directories to ignore.
        extensions (tuple, optional): File extensions to include.
    Returns:
        str: A newline-separated list of file paths relative to the project root.
    """
    if ignored_dirs is None:
        ignored_dirs = {
            'node_modules', '.next', '.vercel', '.git', '.cache',
            '__pycache__', 'dist', 'build', '.DS_Store', '.vscode'
        }

    if extensions is None:
        extensions = ('.ts', '.tsx', '.js', '.jsx', '.json', '.css', '.py', '.html', '.md')

    project_path = os.path.abspath(project_path)
    tree_lines = []

    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.startswith('.')]
        rel_root = os.path.relpath(root, project_path)
        rel_root = '' if rel_root == '.' else rel_root

        for f in files:
            if f.endswith(tuple(extensions)):
                rel_path = os.path.join(rel_root, f) if rel_root else f
                tree_lines.append(rel_path)

    return "\n".join(tree_lines)
