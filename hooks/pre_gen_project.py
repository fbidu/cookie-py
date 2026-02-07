"""
This commands are executed by cookiecutter
before a project is generated
"""

import sys

UV_INSTALL_INSTRUCTIONS = """
*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
| uv is not installed!                                                        |
| Please refer to https://docs.astral.sh/uv/ for instructions.                |
| For most systems: `curl -LsSf https://astral.sh/uv/install.sh | sh`         |
*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
"""

PRE_COMMIT_INSTALL_INSTRUCTIONS = """
*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
| pre-commit is not installed!                                                |
| Please refer to https://pre-commit.com/ for instructions.                   |
| For most systems: `pip install pre-commit` or `uv tool install pre-commit`  |
*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
"""


def command_exists(command):
    """
    checks if `command` exists in the current shell
    """
    from shutil import which

    return which(command) is not None


if __name__ == "__main__":
    exit_messages = []

    if not command_exists("uv"):
        exit_messages.append(UV_INSTALL_INSTRUCTIONS)

    if not command_exists("pre-commit"):
        exit_messages.append(PRE_COMMIT_INSTALL_INSTRUCTIONS)

    if exit_messages:
        sys.exit("\n".join(exit_messages))
