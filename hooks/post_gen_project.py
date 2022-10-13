"""
Commands that are executed by Cookiecutter
after a project is generated
"""
import logging
import json
import pathlib
import subprocess
import os


def init_git():
    """
    Initializes a git repo in the newly created folder
    """
    os.system("git init")


def install_pre_commit():
    """
    Installs the git hooks through Pre-Commit
    """
    os.system("pre-commit install --install-hooks")
    os.system("pre-commit install -t pre-push")


def instal_poetry_dependencies():
    """
    Installs all the dependencies defined in poetry
    """
    os.system("poetry install")


def set_vscode_python_path():
    """
    Sets VSCode's `python.pythonPath` to the
    current interpreter managed by Poetry
    """
    result = subprocess.run(
        ["poetry", "run", "which", "python"], stdout=subprocess.PIPE, check=True
    )
    python_path = result.stdout.decode("utf-8")[:-1]

    settings_path = pathlib.Path(".vscode/settings.json")

    if not settings_path.is_file():
        logging.warning(".vscode/settings.json not found. Skipping pythonPath setting.")
        return

    settings = json.load(open(settings_path))

    if "python.pythonPath" in settings:
        logging.warning(
            "There already is a 'pythonPath' entry. Skipping pythonPath setting."
        )

    settings["python.pythonPath"] = python_path

    json.dump(settings, open(settings_path, "wt"), indent=4, sort_keys=True)


def run_pre_commit_hooks():
    """
    Does an initial run of all pre-commit hooks
    """
    os.system("git add . && pre-commit run --all-files > /dev/null")


def initial_commit():
    os.system("git add . && git commit -m 'Initial commit' && git branch -M main")


if __name__ == "__main__":
    init_git()
    instal_poetry_dependencies()
    install_pre_commit()
    set_vscode_python_path()
    run_pre_commit_hooks()
    initial_commit()
