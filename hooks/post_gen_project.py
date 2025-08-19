"""
Commands that are executed by Cookiecutter
after a project is generated
"""
import json
import logging
import pathlib
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
    subprocess.run(["uv", "run", "pre-commit", "install", "--install-hooks"], check=True)
    subprocess.run(["uv", "run", "pre-commit", "install", "-t", "pre-push"], check=True)


def set_vscode_python_path():
    """
    Sets VSCode's python.defaultInterpreterPath to the
    current interpreter managed by uv
    """
    try:
        result = subprocess.run(
            ["uv", "run", "which", "python"], 
            stdout=subprocess.PIPE, 
            check=True,
            text=True
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


def run_pre_commit_hooks():
    """Run an initial pass of all pre-commit hooks"""
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(
        ["uv", "run", "pre-commit", "run", "--all-files"], 
        check=False  # Don't fail if hooks make changes
    )


def initial_commit():
    """Create initial commit and set main branch"""
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"], 
        check=True
    )
    subprocess.run(["git", "branch", "-M", "main"], check=True)


def main():
    """Main execution function"""
    try:
        logging.basicConfig(level=logging.INFO)
        
        init_git()
        install_dependencies()
        install_pre_commit()
        set_vscode_python_path()
        run_pre_commit_hooks()
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
