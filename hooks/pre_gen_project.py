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


def command_exists(command):
    """
    checks if `command` exists in the current shell
    """
    from shutil import which

    return which(command) is not None


if __name__ == "__main__":
    # Only check for uv since it's required for project generation
    # pre-commit is optional and handled gracefully in post_gen_project.py
    if not command_exists("uv"):
        sys.exit(UV_INSTALL_INSTRUCTIONS)
