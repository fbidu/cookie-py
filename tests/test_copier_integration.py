"""Integration tests for Copier template generation."""

import os
import subprocess
from pathlib import Path
from shutil import which

import pytest

TEMPLATE_DIR = str(Path(__file__).parent.parent)
DEFAULT_DATA: dict[str, str | bool] = {
    "project_name": "My Awesome Project",
    "directory_name": "my-awesome-project",
    "pkg_name": "my_awesome_project",
    "description": "My Awesome Project is awesome",
    "author": "Test Author <test@example.com>",
    "version": "0.1.0",
    "license": "MIT",
    "python_version": "3.12",
    "language": "EN",
    "enable_github_copilot": True,
    "ci_provider": "github",
    "dependency_updates": "renovate",
}


def _build_data_args(data: dict[str, str | bool]) -> list[str]:
    """Build copier -d arguments from a dict."""
    args: list[str] = []
    for key, value in data.items():
        if isinstance(value, bool):
            args.extend(["-d", f"{key}={'true' if value else 'false'}"])
        else:
            args.extend(["-d", f"{key}={value}"])
    return args


def _generate_project(
    dest: Path,
    data: dict[str, str | bool] | None = None,
) -> Path:
    """Generate a project from the template (post-gen tasks skipped via env var)."""
    effective_data = {**DEFAULT_DATA, **(data or {})}
    data_args = _build_data_args(effective_data)

    # Pin the source ref to the current commit. Copier defaults vcs_ref to the
    # latest git tag, so without this the suite would test the last *release*
    # (e.g. v0.2.6) instead of the working tree — masking unreleased template
    # changes locally while a tagless CI checkout silently falls back to HEAD.
    cmd = [
        "copier",
        "copy",
        "--vcs-ref",
        "HEAD",
        "--defaults",
        "--trust",
        *data_args,
        TEMPLATE_DIR,
        str(dest),
    ]
    env = {**os.environ, "SKIP_POST_GENERATE": "1"}

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert result.returncode == 0, f"Copier failed: {result.stderr}\n{result.stdout}"
    return dest


@pytest.fixture(scope="session")
def generated_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate a project once and reuse across tests (no post-gen tasks)."""
    temp_dir = tmp_path_factory.mktemp("copier-test")
    project_dir = temp_dir / "my-awesome-project"

    _generate_project(project_dir)

    # Install dependencies manually (task is skipped)
    result = subprocess.run(
        ["uv", "sync", "--dev"],
        capture_output=True,
        text=True,
        cwd=project_dir,
    )
    assert result.returncode == 0, f"uv sync failed: {result.stderr}"

    return project_dir


@pytest.fixture(scope="session")
def generated_cli_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate a project_type=cli project once and reuse across tests."""
    temp_dir = tmp_path_factory.mktemp("copier-cli-test")
    project_dir = temp_dir / "my-awesome-project"

    _generate_project(project_dir, {"project_type": "cli"})

    result = subprocess.run(
        ["uv", "sync", "--dev"],
        capture_output=True,
        text=True,
        cwd=project_dir,
    )
    assert result.returncode == 0, f"uv sync failed: {result.stderr}"

    return project_dir


class TestCopierGeneration:
    """Test that the Copier template generates valid projects."""

    def test_project_structure(self, generated_project: Path) -> None:
        """Test that the generated project has the correct structure."""
        essential_files = [
            "pyproject.toml",
            "README.md",
            ".gitignore",
            ".python-version",
            ".pre-commit-config.yaml",
            "Dockerfile",
            "CLAUDE.md",
            "conftest.py",
            "my_awesome_project/__init__.py",
            "my_awesome_project/__main__.py",
            "tests/__init__.py",
            "tests/test_my_awesome_project.py",
            ".github/workflows/ci.yml",
            ".github/workflows/build.yml",
        ]
        for file_path in essential_files:
            assert (generated_project / file_path).exists(), f"Missing file: {file_path}"

        # Forgejo workflows must not exist when ci_provider=github
        assert not (generated_project / ".forgejo/workflows/ci.yml").exists()

    def test_template_variables_rendered(self, generated_project: Path) -> None:
        """Test that template variables are properly rendered in output files."""
        pyproject = (generated_project / "pyproject.toml").read_text()
        assert 'name = "my-awesome-project"' in pyproject
        assert "requires-python" in pyproject
        assert "{{" not in pyproject, "Unrendered template variable found"

        readme = (generated_project / "README.md").read_text()
        assert "My Awesome Project" in readme
        assert "{{" not in readme, "Unrendered template variable found"

        # .python-version pins the exact chosen interpreter so uv sync doesn't
        # drift up to a newer minor that merely satisfies requires-python's floor.
        assert (generated_project / ".python-version").read_text().strip() == "3.12"

    def test_workflow_files_rendered_correctly(self, generated_project: Path) -> None:
        """Test that workflow files have rendered Copier vars and preserved GH Actions syntax."""
        ci_yml = (generated_project / ".github/workflows/ci.yml").read_text()
        # Copier variables should be rendered
        assert "uv python install 3.12" in ci_yml
        assert "cookiecutter" not in ci_yml
        # GitHub Actions expressions ({% raw %}…{% endraw %}) should be preserved verbatim
        assert "${{ runner.os }}" in ci_yml
        assert "${{ hashFiles(" in ci_yml

    def test_build_system_present(self, generated_project: Path) -> None:
        """Test that pyproject.toml has an explicit build-system."""
        pyproject = (generated_project / "pyproject.toml").read_text()
        assert "[build-system]" in pyproject
        assert "hatchling" in pyproject

    def test_linting_passes(self, generated_project: Path) -> None:
        """Test that ruff check passes on the generated project."""
        result = subprocess.run(
            ["uv", "run", "ruff", "check", "."],
            capture_output=True,
            text=True,
            cwd=generated_project,
        )
        assert result.returncode == 0, f"Ruff check failed: {result.stdout}\n{result.stderr}"

    def test_type_checking_passes(self, generated_project: Path) -> None:
        """Test that pyright passes on the generated project."""
        result = subprocess.run(
            ["uv", "run", "pyright"],
            capture_output=True,
            text=True,
            cwd=generated_project,
        )
        assert result.returncode == 0, f"Pyright failed: {result.stdout}\n{result.stderr}"

    def test_tests_pass(self, generated_project: Path) -> None:
        """Test that pytest passes on the generated project."""
        result = subprocess.run(
            ["uv", "run", "pytest", "-v"],
            capture_output=True,
            text=True,
            cwd=generated_project,
        )
        assert result.returncode == 0, f"Tests failed: {result.stdout}\n{result.stderr}"

    def test_build_works(self, generated_project: Path) -> None:
        """Test that uv build succeeds."""
        result = subprocess.run(
            ["uv", "build"],
            capture_output=True,
            text=True,
            cwd=generated_project,
        )
        assert result.returncode == 0, f"Build failed: {result.stderr}"
        assert (generated_project / "dist").exists()
        wheel_files = list((generated_project / "dist").glob("*.whl"))
        assert len(wheel_files) > 0, "No wheel file created"


@pytest.mark.parametrize("python_version", ["3.12", "3.13", "3.14"])
class TestPythonVersions:
    """Test that generated projects work with each supported Python version.

    This catches pin drift between template choices and tool versions
    (e.g., prek hooks pinned to an old ruff that doesn't recognize a newer target-version).
    """

    def test_ruff_check_accepts_target_version(self, tmp_path: Path, python_version: str) -> None:
        """Prek's pinned ruff must understand the chosen python_version target."""
        if not which("prek"):
            pytest.skip("prek not installed")

        project_dir = _generate_project(
            tmp_path / f"py{python_version.replace('.', '')}",
            {"python_version": python_version},
        )

        # prek needs a git repo to find files via --all-files
        subprocess.run(["git", "init", "-q"], cwd=project_dir, check=True)
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)

        # Run ONLY the ruff hook so the test stays fast.
        # This uses the ruff version pinned in .pre-commit-config.yaml,
        # not the dev-dep ruff, so it catches pin drift between template
        # choices and prek hook versions.
        result = subprocess.run(
            ["prek", "run", "ruff", "--all-files"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        # A freshly generated project should lint clean, so exit code must be 0.
        # prek collapses both "hook failed" and "files modified" into exit 1,
        # so we also check the output for the "Failed" status marker.
        assert result.returncode == 0 and "Failed" not in result.stdout, (
            f"Prek ruff hook failed on py{python_version}:\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


class TestCIProviderGeneration:
    """Test conditional CI file generation based on ci_provider."""

    def test_github_files_generated(self, tmp_path: Path) -> None:
        """ci_provider=github generates the GitHub workflows and nothing Forgejo."""
        project_dir = _generate_project(tmp_path / "github", {"ci_provider": "github"})
        assert (project_dir / ".github/workflows/ci.yml").exists()
        assert (project_dir / ".github/workflows/build.yml").exists()
        assert not (project_dir / ".forgejo/workflows/ci.yml").exists()

    def test_forgejo_files_generated(self, tmp_path: Path) -> None:
        """ci_provider=forgejo generates .forgejo/workflows and no GitHub workflows."""
        project_dir = _generate_project(tmp_path / "forgejo", {"ci_provider": "forgejo"})
        assert (project_dir / ".forgejo/workflows/ci.yml").exists()
        assert (project_dir / ".forgejo/workflows/copier-update.yml").exists()
        assert not (project_dir / ".github/workflows/ci.yml").exists()
        assert not (project_dir / ".github/workflows/build.yml").exists()
        # No image-build / CI registry job — the Forgejo runner can't build images.
        assert not (project_dir / ".forgejo/workflows/build.yml").exists()

        ci_yml = (project_dir / ".forgejo/workflows/ci.yml").read_text()
        assert "runs-on: ubuntu-latest" in ci_yml
        assert "uv python install 3.12" in ci_yml
        # Forgejo Actions expressions ({% raw %}…{% endraw %}) should survive verbatim.
        assert "${{ hashFiles(" in ci_yml
        assert "{% raw %}" not in ci_yml, "Unrendered jinja raw block found"

    def test_no_ci_generates_nothing(self, tmp_path: Path) -> None:
        """ci_provider=none produces no CI files for any provider."""
        project_dir = _generate_project(tmp_path / "none", {"ci_provider": "none"})
        assert not (project_dir / ".github/workflows/ci.yml").exists()
        assert not (project_dir / ".github/workflows/build.yml").exists()
        assert not (project_dir / ".forgejo/workflows/ci.yml").exists()


class TestProjectType:
    """Test conditional CLI scaffolding based on project_type."""

    def test_library_has_no_cli_scaffolding(self, tmp_path: Path) -> None:
        """project_type=library (default) ships no click dep, cli module, or script."""
        project_dir = _generate_project(tmp_path / "lib", {"project_type": "library"})
        assert not (project_dir / "my_awesome_project/cli.py").exists()
        pyproject = (project_dir / "pyproject.toml").read_text()
        assert "click" not in pyproject
        assert "[project.scripts]" not in pyproject
        assert "dependencies = []" in pyproject
        # The library __main__ keeps its placeholder, not a CLI entry point.
        assert "import" not in (project_dir / "my_awesome_project/__main__.py").read_text()

    def test_cli_scaffolds_click(self, tmp_path: Path) -> None:
        """project_type=cli ships the click dep, a cli module, and a console script."""
        project_dir = _generate_project(tmp_path / "cli", {"project_type": "cli"})
        assert (project_dir / "my_awesome_project/cli.py").exists()

        pyproject = (project_dir / "pyproject.toml").read_text()
        assert "click>=8.1.0" in pyproject
        assert "[project.scripts]" in pyproject
        assert 'my-awesome-project = "my_awesome_project.cli:main"' in pyproject

        # `python -m pkg` should delegate to the click command.
        main_mod = (project_dir / "my_awesome_project/__main__.py").read_text()
        assert "from my_awesome_project.cli import main" in main_mod

    def test_cli_linting_passes(self, generated_cli_project: Path) -> None:
        """A freshly generated CLI project must lint clean."""
        result = subprocess.run(
            ["uv", "run", "ruff", "check", "."],
            capture_output=True,
            text=True,
            cwd=generated_cli_project,
        )
        assert result.returncode == 0, f"Ruff check failed: {result.stdout}\n{result.stderr}"

    def test_cli_type_checking_passes(self, generated_cli_project: Path) -> None:
        """A freshly generated CLI project must pass pyright (strict)."""
        result = subprocess.run(
            ["uv", "run", "pyright"],
            capture_output=True,
            text=True,
            cwd=generated_cli_project,
        )
        assert result.returncode == 0, f"Pyright failed: {result.stdout}\n{result.stderr}"

    def test_cli_tests_pass(self, generated_cli_project: Path) -> None:
        """The generated CLI's own test suite (CliRunner) must pass."""
        result = subprocess.run(
            ["uv", "run", "pytest", "-v"],
            capture_output=True,
            text=True,
            cwd=generated_cli_project,
        )
        assert result.returncode == 0, f"Tests failed: {result.stdout}\n{result.stderr}"

    def test_cli_is_invokable(self, generated_cli_project: Path) -> None:
        """The installed console script runs end to end."""
        result = subprocess.run(
            ["uv", "run", "my-awesome-project", "--name", "World"],
            capture_output=True,
            text=True,
            cwd=generated_cli_project,
        )
        assert result.returncode == 0, f"CLI run failed: {result.stdout}\n{result.stderr}"
        assert "Hello, World!" in result.stdout


class TestDependencyUpdates:
    """Test conditional Renovate setup based on dependency_updates and ci_provider."""

    def test_github_ships_config_and_self_hosted_runner(self, tmp_path: Path) -> None:
        """github + renovate ships renovate.json and the self-hosted workflow."""
        project_dir = _generate_project(
            tmp_path / "gh-renovate",
            {"ci_provider": "github", "dependency_updates": "renovate"},
        )
        assert (project_dir / "renovate.json").exists()
        renovate_wf = project_dir / ".github/workflows/renovate.yml"
        assert renovate_wf.exists()
        # GitHub Actions expressions ({% raw %}…{% endraw %}) must survive verbatim.
        wf = renovate_wf.read_text()
        assert "${{ secrets.RENOVATE_TOKEN }}" in wf
        assert "${{ github.repository }}" in wf
        assert "{% raw %}" not in wf, "Unrendered jinja raw block found"

    def test_forgejo_ships_config_and_workflow(self, tmp_path: Path) -> None:
        """forgejo + renovate ships renovate.json and a scheduled Renovate workflow (no GH workflow)."""
        project_dir = _generate_project(
            tmp_path / "fj-renovate",
            {"ci_provider": "forgejo", "dependency_updates": "renovate"},
        )
        assert (project_dir / "renovate.json").exists()
        assert not (project_dir / ".github/workflows/renovate.yml").exists()
        renovate_wf = (project_dir / ".forgejo/workflows/renovate.yml").read_text()
        assert "RENOVATE_PLATFORM: forgejo" in renovate_wf
        assert "runs-on: ubuntu-latest" in renovate_wf
        assert "schedule:" in renovate_wf

    def test_none_ships_nothing(self, tmp_path: Path) -> None:
        """dependency_updates=none ships no Renovate config or runner."""
        project_dir = _generate_project(
            tmp_path / "no-renovate",
            {"ci_provider": "github", "dependency_updates": "none"},
        )
        assert not (project_dir / "renovate.json").exists()
        assert not (project_dir / ".github/workflows/renovate.yml").exists()
