"""
This commands are executed by cookiecutter
before a project is generated
"""
import sys


def command_exists(command):
    """
    checks if `command` exists in the current shell
    """

    # Usually, I check for existence using `which`
    # Apparently, this is not a good practice
    # see: https://stackoverflow.com/a/677212/2713733

    if sys.version_info < (3,):
        # If we're running Python 2
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
    if not command_exists("poetry"):
        sys.exit("Please install Poetry!")
