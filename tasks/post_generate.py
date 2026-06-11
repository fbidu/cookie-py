"""
Post-generation tasks for Copier template.
Sets up git, installs dependencies, configures prek, and creates initial commit.
"""

import json
import logging
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from shutil import which

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

# Per-license placeholders to substitute. SPDX texts ship with these as
# example markers; we replace them with the user's values.
_LICENSE_PLACEHOLDERS: dict[str, tuple[tuple[str, str], ...]] = {
    "MIT": (("<year>", "{year}"), ("<copyright holders>", "{author}")),
    "BSD-3-Clause": (("<year>", "{year}"), ("<copyright holders>", "{author}")),
    "Apache-2.0": (("[yyyy]", "{year}"), ("[name of copyright owner]", "{author}")),
    "GPL-3.0": (("<year>  <name of author>", "{year}  {author}"),),
}


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
    if not which("prek"):
        missing.append(
            "prek is not installed! See https://github.com/j178/prek for instructions.\n"
            "  Install with: pip install prek  or  uv tool install prek"
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
    """Install git hooks through prek (both pre-commit and pre-push via default_install_hook_types)."""
    try:
        subprocess.run(["prek", "install", "--install-hooks"], check=True)
    except subprocess.CalledProcessError:
        log.warning("Prek installation failed. Continuing without git hooks.")
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
    """Run an initial pass of all prek hooks."""
    try:
        subprocess.run(["git", "add", "."], check=True)
        result = subprocess.run(
            ["prek", "run", "--all-files"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode > 1:
            log.warning("Prek hooks had errors (exit code %d)", result.returncode)
            return False
    except subprocess.CalledProcessError:
        log.warning("Prek hooks failed. Continuing.")
        return False
    return True


def initial_commit() -> None:
    """Create initial commit and set main branch."""
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
    subprocess.run(["git", "branch", "-M", "main"], check=True)


def write_license(template_src: Path, license_id: str, author: str) -> None:
    """Write a LICENSE file with year/author substituted into the SPDX text.

    Skips silently when license_id is Proprietary or unrecognized — the user
    can drop in their own LICENSE.
    """
    if license_id == "Proprietary":
        return
    src = template_src / "licenses" / f"{license_id}.txt"
    if not src.exists():
        log.warning("Unknown license %r; skipping LICENSE generation.", license_id)
        return
    text = src.read_text()
    year = str(datetime.now(tz=UTC).year)
    for placeholder, replacement in _LICENSE_PLACEHOLDERS.get(license_id, ()):
        text = text.replace(placeholder, replacement.format(year=year, author=author))
    Path("LICENSE").write_text(text)


def setup_forge_repo() -> None:
    """Create a Forgejo repo via tea, add it as the origin remote, and push.

    tea (the Gitea/Forgejo CLI) only creates the remote repo — unlike glab it
    does not wire up a git remote — so we scrape the clone URL from its output
    and add ``origin`` ourselves. That URL carries the instance's real SSH port,
    which hardcoding would get wrong. (``tea repos create`` ignores ``-o json``
    and always prints a human-readable summary, so we match the URL rather than
    parse JSON. fj, the Forgejo-native CLI, is a future alternative.)
    """
    if not which("tea"):
        log.warning("tea not found on PATH; skipping Forgejo repo creation.")
        return
    try:
        result = subprocess.run(
            ["tea", "repos", "create", "--name", Path.cwd().name, "--private"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        log.warning("tea repos create failed (%s); skipping remote setup.", e)
        return
    # tea's summary has a "Clone:" line; pull the SSH (preferred) or HTTPS URL.
    match = re.search(r"ssh://\S+?\.git", result.stdout) or re.search(
        r"https?://\S+?\.git", result.stdout
    )
    if not match:
        log.warning("No clone URL found in tea output; skipping remote setup.")
        return
    subprocess.run(["git", "remote", "add", "origin", match.group()], check=False)
    push = subprocess.run(
        ["git", "push", "-u", "origin", "main"],
        check=False,
        capture_output=True,
        text=True,
    )
    if push.returncode != 0:
        log.warning(
            "git push failed; push manually with 'git push -u origin main'.\n%s",
            push.stderr.strip(),
        )


def setup_github_repo(visibility: str) -> None:
    """Create a GitHub repo via gh, wire up origin, and push — in one shot.

    Unlike tea, ``gh repo create --source=. --remote=origin --push`` creates the
    remote repo, adds the origin remote, and pushes the initial commit on its
    own, so there is no clone URL to scrape. ``visibility`` is ``private`` or
    ``public``; gh takes it as the ``--private``/``--public`` flag.
    """
    if not which("gh"):
        log.warning("gh not found on PATH; skipping GitHub repo creation.")
        return
    subprocess.run(
        [
            "gh",
            "repo",
            "create",
            Path.cwd().name,
            f"--{visibility}",
            "--source=.",
            "--remote=origin",
            "--push",
        ],
        check=False,
    )


def main() -> None:
    """Main execution function."""
    import os

    if os.environ.get("SKIP_POST_GENERATE"):
        return

    disable_copilot = "--disable-copilot" in sys.argv
    ci_provider = _arg_value("--ci-provider")
    license_id = _arg_value("--license")
    author = _arg_value("--author")
    template_src = _arg_value("--template-src")
    repo_visibility = _arg_value("--repo-visibility") or "private"

    try:
        check_prerequisites()
        init_git()
        install_dependencies()

        precommit_ok = install_pre_commit()
        setup_vscode_settings(disable_copilot=disable_copilot)

        if license_id and author and template_src:
            write_license(Path(template_src), license_id, author)

        if precommit_ok:
            run_pre_commit_hooks()

        initial_commit()

        if ci_provider == "forgejo":
            setup_forge_repo()
        elif ci_provider == "github":
            setup_github_repo(repo_visibility)

        print("Project setup completed successfully!")

    except subprocess.CalledProcessError as e:
        log.error("Setup failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
