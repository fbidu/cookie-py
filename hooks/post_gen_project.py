"""
Commands that are executed by Cookiecutter
after a project is generated
"""
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
    os.system("poetry run pre-commit install --install-hooks ")
    os.system("poetry run pre-commit install -t pre-push ")

def instal_poetry_dependencies():
    """
    Installs all the dependencies defined in poetry
    """
    os.system("poetry install")

if __name__ == "__main__":
    init_git()
    instal_poetry_dependencies()
    install_pre_commit()
