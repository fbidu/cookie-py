"""
Post-generation tasks for Copier template.
Sets up git, installs dependencies, configures pre-commit, and creates initial commit.
"""

import json
import logging
import subprocess
import sys
from pathlib import Path
from shutil import which

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def _arg_value(flag: str) -> str | None:
    """Return the value following ``flag`` in ``sys.argv``, or ``None`` if absent."""
    if flag in sys.argv:
        idx = sys.argv.index(flag)
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    return None


def check_prerequisites() -> None:
    """Verify required tools are installed."""
    missing: list[str] = []
    if not which("uv"):
        missing.append(
            "uv is not installed! See https://docs.astral.sh/uv/ for instructions.\n"
            "  For most systems: curl -LsSf https://astral.sh/uv/install.sh | sh"
        )
    if not which("pre-commit"):
        missing.append(
            "pre-commit is not installed! See https://pre-commit.com/ for instructions.\n"
            "  Install with: pip install pre-commit  or  uv tool install pre-commit"
        )
    if missing:
        for msg in missing:
            log.error(msg)
        sys.exit(1)


def init_git() -> None:
    """Initialize a git repo."""
    subprocess.run(["git", "init"], check=True)


def install_dependencies() -> None:
    """Install all dependencies using uv."""
    subprocess.run(["uv", "sync", "--dev"], check=True)


def install_pre_commit() -> bool:
    """Install git hooks through pre-commit."""
    try:
        subprocess.run(["pre-commit", "install", "--install-hooks"], check=True)
        subprocess.run(["pre-commit", "install", "-t", "pre-push"], check=True)
    except subprocess.CalledProcessError:
        log.warning("Pre-commit installation failed. Continuing without pre-commit hooks.")
        return False
    return True


def setup_vscode_settings(*, disable_copilot: bool = False) -> None:
    """Configure VS Code settings: editor preferences, Python path, and optionally disable Copilot."""
    settings: dict[str, object] = {
        "[python]": {
            "editor.codeActionsOnSave": {
                "source.organizeImports": "always",
                "source.fixAll": "always",
            },
            "editor.defaultFormatter": "charliermarsh.ruff",
            "editor.formatOnSave": True,
        },
        "ruff.lint.enable": True,
        "ruff.nativeServer": "on",
        "ruff.organizeImports": True,
        "python.testing.nosetestsEnabled": False,
        "python.testing.pytestArgs": ["tests", "--doctest-modules"],
        "python.testing.pytestEnabled": True,
        "python.testing.unittestEnabled": False,
    }

    if disable_copilot:
        settings["github.copilot.enable"] = {
            "*": False,
            "plaintext": False,
            "markdown": False,
            "scminput": False,
        }

    # Add Python interpreter path
    try:
        result = subprocess.run(
            ["uv", "run", "python", "-c", "import sys; print(sys.executable)"],
            capture_output=True,
            check=True,
            text=True,
        )
        settings["python.defaultInterpreterPath"] = result.stdout.strip()
    except subprocess.CalledProcessError:
        log.warning("Could not determine Python path.")

    settings_path = Path(".vscode/settings.json")
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    with settings_path.open("w") as f:
        json.dump(settings, f, indent=4, sort_keys=True)


def run_pre_commit_hooks() -> bool:
    """Run an initial pass of all pre-commit hooks."""
    try:
        subprocess.run(["git", "add", "."], check=True)
        result = subprocess.run(
            ["pre-commit", "run", "--all-files"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode > 1:
            log.warning("Pre-commit hooks had errors (exit code %d)", result.returncode)
            return False
    except subprocess.CalledProcessError:
        log.warning("Pre-commit hooks failed. Continuing.")
        return False
    return True


def initial_commit() -> None:
    """Create initial commit and set main branch."""
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
    subprocess.run(["git", "branch", "-M", "main"], check=True)


def setup_gitlab_repo() -> None:
    """Create a GitLab project via glab and add it as the origin remote."""
    if not which("glab"):
        log.warning("glab not found on PATH; skipping GitLab repo creation.")
        return
    try:
        subprocess.run(
            ["glab", "repo", "create", "--defaultBranch", "main"],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        log.warning("glab repo create failed (%s); skipping remote setup.", e)


def main() -> None:
    """Main execution function."""
    import os

    if os.environ.get("SKIP_POST_GENERATE"):
        return

    disable_copilot = "--disable-copilot" in sys.argv
    cd_pipeline = _arg_value("--cd-pipeline")

    try:
        check_prerequisites()
        init_git()
        install_dependencies()

        precommit_ok = install_pre_commit()
        setup_vscode_settings(disable_copilot=disable_copilot)

        if precommit_ok:
            run_pre_commit_hooks()

        initial_commit()

        if cd_pipeline == "homelab-gitlab":
            setup_gitlab_repo()

        print("Project setup completed successfully!")

    except subprocess.CalledProcessError as e:
        log.error("Setup failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
