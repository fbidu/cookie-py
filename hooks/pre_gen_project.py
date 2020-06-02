"""
This commands are executed by cookiecutter
before a project is generated
"""
import sys

POETRY_INSTALL_INSTRUCTIONS = """
*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
| Poetry is not installed!                                                    |
| Please refer to https://python-poetry.org/ for instructions.                |
| In most systems, a `pip install poetry` is enough.                          |
*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
"""

PRE_COMMIT_INSTALL_INSTRUCTIONS = """
*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
| pre-commit is not installed!                                                |
| Please refer to https://pre-commit.com/ for instructions.                   |
| In most systems, a `pip install pre-commit` is enough.                      |
*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
"""


def command_exists(command):
    """
    checks if `command` exists in the current shell
    """

    # Usually, I check for existence using `which`
    # Apparently, this is not a good practice
    # see: https://stackoverflow.com/a/677212/2713733

    # If we're running Python 2
    if sys.version_info < (3,):

        from subprocess import Popen
        import os

        devnull = open(os.devnull)
        try:
            Popen([command, "-v"], stdout=devnull, stderr=devnull).communicate()
        except OSError as e:
            # pylint: disable=no-member
            if e.errno != os.errno.ENOENT:
                raise
            return False
        return True

    # If we're running Python 3
    from shutil import which

    return which(command) is not None


if __name__ == "__main__":
    exit_messages = []

    if not command_exists("poetry"):
        exit_messages.append(POETRY_INSTALL_INSTRUCTIONS)

    if not command_exists("pre-commit"):
        exit_messages.append(PRE_COMMIT_INSTALL_INSTRUCTIONS)

    if exit_messages:
        sys.exit("\n".join(exit_messages))
