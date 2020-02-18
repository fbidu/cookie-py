"""
Commands that are executed by Cookiecutter
after a project is generated
"""
import os

def init_git():
    os.system("git init")

def install_pre_commit():
    os.system("pre-commit install --install-hooks ")


if __name__ == "__main__":
    init_git()
    install_pre_commit()
