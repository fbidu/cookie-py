"""
Commands that are executed by Cookiecutter
after a project is generated
"""

import json
import logging
import subprocess
import sys
from pathlib import Path


def init_git():
    """Initialize a git repo in the newly created folder"""
    subprocess.run(["git", "init"], check=True)


def install_dependencies():
    """Install all the dependencies using uv"""
    subprocess.run(["uv", "sync", "--dev"], check=True)


def install_pre_commit():
    """Install the git hooks through pre-commit"""
    try:
        subprocess.run(["pre-commit", "install", "--install-hooks"], check=True)
        subprocess.run(["pre-commit", "install", "-t", "pre-push"], check=True)
    except subprocess.CalledProcessError as e:
        logging.warning(
            f"Pre-commit installation failed: {e}. Continuing without pre-commit hooks."
        )
        return False
    return True


def set_vscode_python_path():
    """
    Sets VSCode's python.defaultInterpreterPath to the
    current interpreter managed by uv
    """
    try:
        result = subprocess.run(
            ["uv", "run", "which", "python"], stdout=subprocess.PIPE, check=True, text=True
        )
        python_path = result.stdout.strip()
    except subprocess.CalledProcessError:
        logging.warning("Could not determine Python path. Skipping VSCode setting.")
        return

    settings_path = Path(".vscode/settings.json")

    if not settings_path.parent.exists():
        settings_path.parent.mkdir(parents=True, exist_ok=True)

    if settings_path.is_file():
        with settings_path.open() as f:
            settings = json.load(f)
    else:
        settings = {}

    if "python.defaultInterpreterPath" in settings:
        logging.warning(
            "There already is a 'defaultInterpreterPath' entry. Skipping Python path setting."
        )
        return

    settings["python.defaultInterpreterPath"] = python_path

    with settings_path.open("w") as f:
        json.dump(settings, f, indent=4, sort_keys=True)


def setup_spec_kit():
    """Run specify init to set up spec-driven development scaffolding."""
    ai_agent = "{{ cookiecutter.spec_kit_ai_agent }}"
    try:
        subprocess.run(
            ["specify", "init", "--here", "--ai", ai_agent, "--no-git", "--force"],
            check=True,
        )
    except FileNotFoundError:
        logging.warning(
            "specify CLI not found. Skipping Spec Kit setup. "
            "Install with: uv tool install specify-cli "
            "--from git+https://github.com/github/spec-kit.git"
        )
        return False
    except subprocess.CalledProcessError as e:
        logging.warning(f"Spec Kit setup failed: {e}. Continuing without it.")
        return False
    return True


def run_pre_commit_hooks():
    """Run an initial pass of all pre-commit hooks"""
    try:
        subprocess.run(["git", "add", "."], check=True)
        result = subprocess.run(
            ["pre-commit", "run", "--all-files"],
            check=False,  # Don't fail if hooks make changes
            capture_output=True,
            text=True,
        )
        # Pre-commit returns 1 if it made changes, which is fine
        if result.returncode > 1:
            logging.warning(
                f"Pre-commit hooks had errors (exit code {result.returncode}): {result.stderr}"
            )
            return False
    except subprocess.CalledProcessError as e:
        logging.warning(f"Pre-commit hooks failed: {e}. Continuing without running hooks.")
        return False
    return True


def initial_commit():
    """Create initial commit and set main branch"""
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
    subprocess.run(["git", "branch", "-M", "main"], check=True)


def main():
    """Main execution function"""
    try:
        logging.basicConfig(level=logging.INFO)

        init_git()
        install_dependencies()
        precommit_success = install_pre_commit()
        set_vscode_python_path()

        if "{{ cookiecutter.enable_spec_kit }}" == "yes":
            setup_spec_kit()

        if precommit_success:
            run_pre_commit_hooks()
        else:
            logging.warning("Skipping pre-commit hooks due to installation failure.")

        initial_commit()

        print("✅ Project setup completed successfully!")

    except subprocess.CalledProcessError as e:
        logging.error(f"Setup failed: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
