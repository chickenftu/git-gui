# git-gui

This repository provides a minimal Git GUI application written in Python.
The GUI uses **PyQt6** and the backend logic relies on **GitPython**.

## Requirements

- Python 3.10+
- PyQt6
- GitPython
- Git installed and available on the command line

## Running

Install the required Python dependencies and run the application with

```bash
python -m pip install PyQt6 GitPython
python -m git_gui.main /path/to/repository
```

If no path is provided, the current directory is used.

## Project Structure

- `git_gui/git_backend.py` – minimal wrapper around git commands
- `git_gui/app.py` – PyQt6 GUI
- `git_gui/main.py` – command line entry point
- `tests/` – unit tests for git backend logic

## Architectural Plan

The application is organized into several modules using the Qt Model/View
pattern:

- **`git_gui.git_backend`** – `Repository` wraps GitPython to expose actions
  like status, staging, committing, pulling, pushing and branch operations.
- **`git_gui.models`** – `FileStatusModel` implements a `QAbstractListModel`
  to present `FileStatus` entries from the repository.
- **`git_gui.diff_viewer`** – `DiffViewer` dialog displays diffs using simple
  HTML styling.
- **`git_gui.diff_highlighter`** – `DiffHighlighter` highlights diff output in
  text widgets.
- **`git_gui.app`** – `GitGuiApp` main window wiring together the model and
  backend, providing actions for staging, committing, pulling and pushing.
- **`git_gui.main`** – entry point launching the application.

## Development Notes

The project aims to demonstrate basic best practices for separating the
business logic (git operations) from the user interface. The GUI lists the
current status of repository files, allows staging and committing changes,
and exposes simple pull and push actions. Pull and push are available as
toolbar buttons, and a *Push Review* action shows commits that will be pushed.
The context menu for each file adapts based on its git status. Untracked files
offer an option to add the file to the repository or ignore it (which writes
the path to `.gitignore`). Tracked files show stage or unstage actions
depending on whether changes are staged.
Double-clicking a file or choosing **Show Diff** opens an HTML diff viewer
styled similarly to the web diff view.
