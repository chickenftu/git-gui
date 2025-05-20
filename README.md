# git-gui

This repository provides a minimal Git GUI application written in Python.
The GUI uses **PyQt6** and the backend logic relies on standard git commands.

## Requirements

- Python 3.10+
- PyQt6
- Git installed and available on the command line

## Running

Install the required Python dependencies and run the application with

```bash
python -m pip install PyQt6
python -m git_gui.main /path/to/repository
```

If no path is provided, the current directory is used.

## Project Structure

- `git_gui/git_backend.py` – minimal wrapper around git commands
- `git_gui/app.py` – PyQt6 GUI
- `git_gui/main.py` – command line entry point
- `tests/` – unit tests for git backend logic

## Development Notes

The project aims to demonstrate basic best practices for separating the
business logic (git operations) from the user interface. The GUI lists the
current status of repository files, allows staging and committing changes,
and exposes simple pull and push actions. Pull and push are available as
toolbar buttons, and a *Push Review* action shows commits that will be pushed.
