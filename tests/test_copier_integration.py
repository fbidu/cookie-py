"""Integration tests for Copier template generation."""

import os
import subprocess
import tomllib
from collections.abc import Iterator
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
    "python_version": "3.14",
    "language": "EN",
    "enable_github_copilot": True,
    "ci_provider": "github",
    "dependency_updates": "renovate",
}
# A small document for the tests of the spec-first option: one operation, one
# enum, a described field and a nullable one.
OPENAPI_DOCUMENT = """\
openapi: 3.1.0
info:
  title: Example
  version: "1"
paths:
  /forecasts/{city}:
    get:
      operationId: getForecast
      tags: [forecasts]
      parameters:
        - name: city
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: The forecast of a city.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Forecast"
components:
  schemas:
    Sky:
      type: string
      enum: [clear, cloudy, rain]
    Forecast:
      type: object
      required: [city, sky, issued_at]
      properties:
        city:
          type: string
        sky:
          $ref: "#/components/schemas/Sky"
        issued_at:
          type: integer
          description: When the forecast was issued, as a Unix timestamp in seconds.
        high:
          type: [number, "null"]
          description: The highest temperature of the day, in degrees Celsius.
"""
# Variables git exports to its hooks to locate the repo being committed or pushed.
GIT_REPO_ENV = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_PREFIX")


@pytest.fixture(scope="session", autouse=True)
def ignore_inherited_git_repo() -> Iterator[None]:
    """Stop git from acting on this repo when the suite runs from a git hook.

    The pre-push hook runs the suite with git's repo variables pointing here.
    Copier and the tests run git in other directories: with those variables
    set, cloning the template fails and `git add` would stage into this repo.
    """
    with pytest.MonkeyPatch.context() as patch:
        for name in GIT_REPO_ENV:
            patch.delenv(name, raising=False)
        yield


def _build_data_args(data: dict[str, str | bool]) -> list[str]:
    """Build copier -d arguments from a dict."""
    args: list[str] = []
    for key, value in data.items():
        if isinstance(value, bool):
            args.extend(["-d", f"{key}={'true' if value else 'false'}"])
        else:
            args.extend(["-d", f"{key}={value}"])
    return args


def _run_copier(
    dest: Path,
    data: dict[str, str | bool] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run copier on the template (post-gen tasks skipped via env var)."""
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

    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def _generate_project(
    dest: Path,
    data: dict[str, str | bool] | None = None,
) -> Path:
    """Generate a project from the template, failing the test if copier fails."""
    result = _run_copier(dest, data)
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


@pytest.fixture(scope="session")
def generated_docs_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate a project_type=docs project once and reuse across tests."""
    temp_dir = tmp_path_factory.mktemp("copier-docs-test")
    project_dir = temp_dir / "my-awesome-project"

    _generate_project(project_dir, {"project_type": "docs"})

    result = subprocess.run(
        ["uv", "sync", "--dev"],
        capture_output=True,
        text=True,
        cwd=project_dir,
    )
    assert result.returncode == 0, f"uv sync failed: {result.stderr}"

    return project_dir


@pytest.fixture(scope="session")
def generated_api_client_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate a project_type=api-client project once and reuse across tests."""
    temp_dir = tmp_path_factory.mktemp("copier-api-client-test")
    project_dir = temp_dir / "my-awesome-project"

    _generate_project(project_dir, {"project_type": "api-client"})

    result = subprocess.run(
        ["uv", "sync", "--dev"],
        capture_output=True,
        text=True,
        cwd=project_dir,
    )
    assert result.returncode == 0, f"uv sync failed: {result.stderr}"

    return project_dir


@pytest.fixture(scope="session")
def generated_spec_first_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate a spec-first project_type=api-client project once and reuse across tests."""
    temp_dir = tmp_path_factory.mktemp("copier-spec-first-test")
    project_dir = temp_dir / "my-awesome-project"

    _generate_project(project_dir, {"project_type": "api-client", "spec_first": True})

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
            "AGENTS.md",
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
        assert (generated_project / ".python-version").read_text().strip() == "3.14"

    def test_claude_md_imports_agents_md(self, generated_project: Path) -> None:
        """Agent instructions live in AGENTS.md, so every agent tool reads one file.

        CLAUDE.md only imports it, for the tools that look for that name.
        """
        assert (generated_project / "CLAUDE.md").read_text().strip() == "@AGENTS.md"

    def test_free_text_answers_survive_in_generated_files(self, tmp_path: Path) -> None:
        """The description and the author are free text, so they may hold quotes.

        Written unescaped into a quoted string, a double quote makes
        pyproject.toml invalid and the project cannot be installed.
        """
        description = 'Say "hi" to João\'s API'
        author = 'Felipe "Bidu" Rodrigues <felipe@example.com>'

        project_dir = _generate_project(
            tmp_path / "quotes", {"description": description, "author": author}
        )

        project = tomllib.loads((project_dir / "pyproject.toml").read_text())["project"]
        assert project["description"] == description
        assert project["authors"] == [{"name": author}]
        main_module = (project_dir / "my_awesome_project/__main__.py").read_text()
        compile(main_module, "__main__.py", "exec")
        # Escaped only where the format needs it, so the files stay readable
        mkdocs_yml = (project_dir / "mkdocs.yml").read_text()
        assert 'site_description: "Say \\"hi\\" to João\'s API"' in mkdocs_yml

    def test_workflow_files_rendered_correctly(self, generated_project: Path) -> None:
        """Test that workflow files have rendered Copier vars and preserved GH Actions syntax."""
        ci_yml = (generated_project / ".github/workflows/ci.yml").read_text()
        # Copier variables should be rendered
        assert "uv python install 3.14" in ci_yml
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

    def test_installs_when_pkg_name_differs_from_directory_name(self, tmp_path: Path) -> None:
        """A package name unrelated to the project name must still install.

        Hatchling's default file selection looks for a directory named after the
        project, so a distribution like `simplelogin-sdk` shipping a `simplelogin`
        package only builds when the wheel packages are declared explicitly.
        """
        project_dir = _generate_project(
            tmp_path / "simplelogin-sdk",
            {"directory_name": "simplelogin-sdk", "pkg_name": "simplelogin"},
        )
        # Sanity check: the package dir does not match the normalized project name
        assert (project_dir / "simplelogin").is_dir()
        assert not (project_dir / "simplelogin_sdk").exists()

        result = subprocess.run(
            ["uv", "sync", "--dev"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )

        assert result.returncode == 0, f"uv sync failed: {result.stderr}"


class TestDocs:
    """Test that every generated project ships an MkDocs site that builds."""

    def test_docs_site_builds(self, generated_project: Path) -> None:
        """A fresh project must build its docs with no warnings.

        The strict build is the gate the pre-commit hook and CI apply, so a
        template that fails it would break the first commit of every project.
        """
        result = subprocess.run(
            ["uv", "run", "mkdocs", "build", "--strict"],
            capture_output=True,
            text=True,
            cwd=generated_project,
        )

        assert result.returncode == 0, f"mkdocs build failed: {result.stdout}\n{result.stderr}"
        assert "My Awesome Project" in (generated_project / "site/index.html").read_text()

    def test_api_reference_documents_the_package(self, generated_cli_project: Path) -> None:
        """The reference page is rendered from the code, so it needs no upkeep.

        Submodules must show up too, or the page stays empty while the package
        grows.
        """
        result = subprocess.run(
            ["uv", "run", "mkdocs", "build", "--strict"],
            capture_output=True,
            text=True,
            cwd=generated_cli_project,
        )

        assert result.returncode == 0, f"mkdocs build failed: {result.stdout}\n{result.stderr}"
        reference = (generated_cli_project / "site/reference/index.html").read_text()
        assert "my_awesome_project.cli" in reference

    def test_docs_hook_rejects_a_broken_link(self, tmp_path: Path) -> None:
        """A broken link must fail the commit, not a publish job nobody watches."""
        if not which("prek"):
            pytest.skip("prek not installed")
        project_dir = _generate_project(tmp_path / "docs-hook")
        subprocess.run(["uv", "sync", "--dev"], cwd=project_dir, check=True, capture_output=True)
        # prek needs a git repo to find files via --all-files
        subprocess.run(["git", "init", "-q"], cwd=project_dir, check=True)
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
        hook = ["prek", "run", "mkdocs-build", "--all-files"]
        # Sanity check: the hook passes on the untouched project
        clean = subprocess.run(hook, capture_output=True, text=True, cwd=project_dir)
        assert clean.returncode == 0, f"Hook failed on a fresh project: {clean.stdout}"
        with (project_dir / "docs/index.md").open("a") as index:
            index.write("\n[Missing page](missing.md)\n")

        result = subprocess.run(hook, capture_output=True, text=True, cwd=project_dir)

        assert result.returncode != 0, "Hook accepted a link to a page that does not exist"
        assert "missing.md" in result.stdout

    def test_existing_instructions_and_pages_are_kept(self, tmp_path: Path) -> None:
        """Adopting the docs flow must not overwrite what a project already wrote.

        Projects generated before it filled CLAUDE.md by hand, and some have
        their own docs/index.md. Both are project content, not template files.
        """
        project_dir = tmp_path / "existing"
        (project_dir / "docs").mkdir(parents=True)
        (project_dir / "CLAUDE.md").write_text("Project instructions\n")
        (project_dir / "docs/index.md").write_text("# Findings\n")

        _generate_project(project_dir)

        assert (project_dir / "CLAUDE.md").read_text() == "Project instructions\n"
        assert (project_dir / "docs/index.md").read_text() == "# Findings\n"
        # Sanity check: the rest of the docs flow still arrived
        assert (project_dir / "mkdocs.yml").exists()
        assert (project_dir / "AGENTS.md").exists()


class TestDocsPublishing:
    """Test the opt-in publishing of the docs to the homelab docs host."""

    def test_publishing_is_off_by_default(self, tmp_path: Path) -> None:
        """A Forgejo project must not publish unless asked to.

        Publishing pushes the docs to a shared host, so it is never a default.
        """
        project_dir = _generate_project(tmp_path / "no-publish", {"ci_provider": "forgejo"})

        assert not (project_dir / ".forgejo/workflows/docs.yml").exists()
        assert "site_url" not in (project_dir / "mkdocs.yml").read_text()

    def test_opting_in_generates_the_publish_workflow(self, tmp_path: Path) -> None:
        """Opting in must yield a workflow that publishes the chosen tenant.

        MkDocs also needs the tenant URL as site_url, or the 404 page, the
        sitemap and canonical links point at the host root.
        """
        project_dir = _generate_project(
            tmp_path / "publish",
            {"ci_provider": "forgejo", "publish_docs": True, "docs_tenant": "my-tenant"},
        )

        workflow = (project_dir / ".forgejo/workflows/docs.yml").read_text()
        assert "runs-on: homelab" in workflow
        assert "mkdocs build --strict" in workflow
        assert "docspub@192.168.71.1 publish my-tenant" in workflow
        # Forgejo Actions expressions ({% raw %}…{% endraw %}) should survive verbatim.
        assert "${{ secrets.DOCS_PUBLISH_KEY_B64 }}" in workflow
        assert "{% raw %}" not in workflow, "Unrendered jinja raw block found"
        mkdocs_yml = (project_dir / "mkdocs.yml").read_text()
        assert "site_url: https://docs.example.com/my-tenant/" in mkdocs_yml

    def test_tenant_defaults_to_the_directory_name(self, tmp_path: Path) -> None:
        """The tenant is the URL path, and the project's own name is the obvious one."""
        project_dir = _generate_project(
            tmp_path / "default-tenant", {"ci_provider": "forgejo", "publish_docs": True}
        )

        workflow = (project_dir / ".forgejo/workflows/docs.yml").read_text()
        assert "publish my-awesome-project" in workflow

    def test_invalid_tenant_is_rejected(self, tmp_path: Path) -> None:
        """The docs host refuses a tenant outside [a-z0-9][a-z0-9-]*.

        Rejecting it at generation time beats a publish job that fails later.
        """
        result = _run_copier(
            tmp_path / "bad-tenant",
            {"ci_provider": "forgejo", "publish_docs": True, "docs_tenant": "Bad_Tenant"},
        )

        assert result.returncode != 0, "Copier accepted an invalid tenant"
        assert "tenant" in result.stderr

    def test_tenant_rule_does_not_apply_without_publishing(self, tmp_path: Path) -> None:
        """A directory name that is not a valid tenant must not block a project that never publishes."""
        project_dir = _generate_project(
            tmp_path / "under_score",
            {"ci_provider": "forgejo", "directory_name": "under_score"},
        )

        assert (project_dir / "mkdocs.yml").exists()

    def test_other_providers_never_publish(self, tmp_path: Path) -> None:
        """The docs host is only reachable from the homelab runner.

        A publish workflow on another provider could never succeed, so the
        answer is ignored there.
        """
        project_dir = _generate_project(
            tmp_path / "github-publish", {"ci_provider": "github", "publish_docs": True}
        )

        assert not (project_dir / ".forgejo/workflows/docs.yml").exists()
        assert "site_url" not in (project_dir / "mkdocs.yml").read_text()


def _require_docker() -> None:
    """Skip the calling test when there is no usable Docker daemon."""
    if not which("docker") or subprocess.run(["docker", "info"], capture_output=True).returncode:
        pytest.skip("docker not available")


class TestDockerImage:
    """Test that the generated Dockerfile installs the project into its images."""

    def test_production_image_has_the_package_installed(self, generated_project: Path) -> None:
        """The package must be importable from anywhere in the production image.

        Installing the project before its source is in the build context leaves
        an empty install. `python -m <pkg>` run from /app hides that, but console
        scripts break, so the import runs from another directory.
        """
        _require_docker()
        build = subprocess.run(
            ["docker", "build", "--target", "production", "-t", "cookie-py-test-production", "."],
            capture_output=True,
            text=True,
            cwd=generated_project,
        )
        assert build.returncode == 0, f"docker build failed: {build.stderr}"

        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-w",
                "/",
                "cookie-py-test-production",
                "python",
                "-c",
                "import my_awesome_project",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Package not installed in the image: {result.stderr}"

    def test_development_image_uses_the_mounted_source(self, generated_project: Path) -> None:
        """The development image must import the source that is mounted at runtime.

        That image ships no source: it is meant to run with the project
        bind-mounted, so its environment has to point at the mount.
        """
        _require_docker()
        build = subprocess.run(
            ["docker", "build", "--target", "development", "-t", "cookie-py-test-development", "."],
            capture_output=True,
            text=True,
            cwd=generated_project,
        )
        assert build.returncode == 0, f"docker build failed: {build.stderr}"
        source = generated_project / "my_awesome_project"

        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-w",
                "/",
                "-v",
                f"{source}:/app/my_awesome_project:ro",
                "cookie-py-test-development",
                "python",
                "-c",
                "import my_awesome_project",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Mounted source not importable: {result.stderr}"


@pytest.mark.parametrize("python_version", ["3.13", "3.14"])
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


@pytest.mark.parametrize("python_version", ["3.11", "3.12"])
def test_dropped_python_versions_are_rejected(tmp_path: Path, python_version: str) -> None:
    """The template no longer supports 3.11 and 3.12, so it must refuse them.

    Accepting a dropped version would generate a project the template does
    not test against.
    """
    result = _run_copier(tmp_path / "dropped-python", {"python_version": python_version})

    assert result.returncode != 0, f"Copier accepted Python {python_version}"
    assert "python_version" in result.stderr


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
        assert "uv python install 3.14" in ci_yml
        # Forgejo Actions expressions ({% raw %}…{% endraw %}) should survive verbatim.
        assert "${{ hashFiles(" in ci_yml
        assert "{% raw %}" not in ci_yml, "Unrendered jinja raw block found"

    def test_forgejo_ci_names_the_memory_cap(self, tmp_path: Path) -> None:
        """A job over the runner's memory cap dies with nothing but exit 137.

        The workflow is where someone debugging that death looks first, so it
        has to name the cap and the symptom.
        """
        project_dir = _generate_project(tmp_path / "forgejo", {"ci_provider": "forgejo"})

        ci_yml = (project_dir / ".forgejo/workflows/ci.yml").read_text()

        assert "2 GiB" in ci_yml
        assert "137" in ci_yml

    def test_forgejo_ci_points_container_tests_to_dind(self, tmp_path: Path) -> None:
        """Tests that start their own services cannot reach them on the default runner.

        The job runs pytest, so the workflow says which runner fixes that. A
        docs-only project runs no tests, so the note would only mislead there.
        """
        # Setup
        with_tests = _generate_project(tmp_path / "library", {"ci_provider": "forgejo"})
        docs_only = _generate_project(
            tmp_path / "docs", {"ci_provider": "forgejo", "project_type": "docs"}
        )

        # Act
        ci_yml = (with_tests / ".forgejo/workflows/ci.yml").read_text()
        docs_ci_yml = (docs_only / ".forgejo/workflows/ci.yml").read_text()

        # Assert
        assert "hook-stage pre-push" in ci_yml, "Sanity check: the job runs pytest"
        assert "`runs-on: dind`" in ci_yml
        assert "runs-on: ubuntu-latest" in ci_yml, "dind is documented, not the default"
        assert "dind" not in docs_ci_yml

    def test_forgejo_ci_caches_uv_before_syncing(self, tmp_path: Path) -> None:
        """The uv cache only saves downloads when it is restored before the sync.

        The key must not use `runner.os`: on the homelab runners it evaluates
        to both `Linux` and `linux`, so the cache would miss half the time.
        """
        project_dir = _generate_project(tmp_path / "forgejo", {"ci_provider": "forgejo"})

        ci_yml = (project_dir / ".forgejo/workflows/ci.yml").read_text()

        assert "path: ~/.cache/uv" in ci_yml
        assert "key: uv-${{ hashFiles('uv.lock') }}" in ci_yml
        assert ci_yml.index("path: ~/.cache/uv") < ci_yml.index("uv sync")
        assert "runner.os" not in ci_yml

    def test_forgejo_ci_cancels_superseded_runs(self, tmp_path: Path) -> None:
        """The runner is shared, so a run made obsolete by a newer push must free its slot."""
        project_dir = _generate_project(tmp_path / "forgejo", {"ci_provider": "forgejo"})

        ci_yml = (project_dir / ".forgejo/workflows/ci.yml").read_text()

        assert (
            "concurrency:\n"
            "  group: ${{ github.workflow }}-${{ github.ref }}\n"
            "  cancel-in-progress: true\n"
        ) in ci_yml

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


class TestDocsOnlyProject:
    """Test the project_type=docs scaffold: an MkDocs site with no Python package."""

    def test_ships_the_site_and_no_code(self, generated_docs_project: Path) -> None:
        """A docs-only project is the site plus its tooling, with nothing to import or test."""
        expected = [
            "pyproject.toml",
            "mkdocs.yml",
            "docs/index.md",
            "README.md",
            "AGENTS.md",
            "CLAUDE.md",
            ".python-version",
            ".pre-commit-config.yaml",
            ".github/workflows/ci.yml",
        ]
        for file_path in expected:
            assert (generated_docs_project / file_path).exists(), f"Missing file: {file_path}"

        unexpected = [
            "my_awesome_project",
            "tests",
            "conftest.py",
            "Dockerfile",
            ".dockerignore",
            "docs/reference.md",
            ".github/workflows/build.yml",
        ]
        for file_path in unexpected:
            assert not (generated_docs_project / file_path).exists(), f"Unexpected: {file_path}"

    def test_has_no_python_tooling(self, generated_docs_project: Path) -> None:
        """Linters, type checkers and test runners have nothing to check here.

        Shipping them would add hooks and CI steps that run on no files.
        """
        pyproject = (generated_docs_project / "pyproject.toml").read_text()
        assert "package = false" in pyproject
        hooks = (generated_docs_project / ".pre-commit-config.yaml").read_text()
        for tool in ("ruff", "pyright", "pytest", "bandit", "hatchling", "mkdocstrings"):
            assert tool not in pyproject, f"{tool} found in pyproject.toml"
            assert tool not in hooks, f"{tool} found in .pre-commit-config.yaml"

    def test_docs_site_builds(self, generated_docs_project: Path) -> None:
        """The site is the whole product, so a fresh project must build it cleanly."""
        result = subprocess.run(
            ["uv", "run", "mkdocs", "build", "--strict"],
            capture_output=True,
            text=True,
            cwd=generated_docs_project,
        )

        assert result.returncode == 0, f"mkdocs build failed: {result.stdout}\n{result.stderr}"
        assert "My Awesome Project" in (generated_docs_project / "site/index.html").read_text()

    def test_passes_its_own_hooks(self, tmp_path: Path) -> None:
        """The hooks left after dropping the Python tooling must still run green.

        The first pass may rewrite files (end-of-file fixer), as the post-generate
        task allows, so the second pass is the one that must be clean.
        """
        if not which("prek"):
            pytest.skip("prek not installed")
        project_dir = _generate_project(tmp_path / "docs-hooks", {"project_type": "docs"})
        subprocess.run(["uv", "sync", "--dev"], cwd=project_dir, check=True, capture_output=True)
        # prek needs a git repo to find files via --all-files
        subprocess.run(["git", "init", "-q"], cwd=project_dir, check=True)
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
        subprocess.run(["prek", "run", "--all-files"], cwd=project_dir, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)

        result = subprocess.run(
            ["prek", "run", "--all-files"], capture_output=True, text=True, cwd=project_dir
        )

        assert result.returncode == 0, f"Hooks failed:\n{result.stdout}\n{result.stderr}"
        assert "mkdocs build" in result.stdout

    def test_pages_survive_in_a_directory_named_docs(self, tmp_path: Path) -> None:
        """A docs repo is often just called `docs`, which is also the pages folder.

        The package folder is skipped for this project type, and skipping it by
        name would take the pages with it.
        """
        project_dir = _generate_project(
            tmp_path / "docs",
            {"project_type": "docs", "directory_name": "docs", "pkg_name": "docs"},
        )

        assert (project_dir / "docs/index.md").exists()

    def test_publish_workflow_watches_no_package(self, tmp_path: Path) -> None:
        """The publish workflow must not trigger on a package folder that does not exist."""
        project_dir = _generate_project(
            tmp_path / "docs-publish",
            {"project_type": "docs", "ci_provider": "forgejo", "publish_docs": True},
        )

        workflow = (project_dir / ".forgejo/workflows/docs.yml").read_text()
        assert "docs/**" in workflow
        assert "my_awesome_project" not in workflow


class TestApiClientProject:
    """Test the project_type=api-client scaffold: an HTTP client, its errors and its settings."""

    def test_ships_the_client_scaffold(self, generated_api_client_project: Path) -> None:
        """Every API client starts from the same decisions, so the scaffold makes them once.

        The placeholder test goes away: the client ships with tests of its own.
        """
        expected = [
            "my_awesome_project/client.py",
            "my_awesome_project/errors.py",
            "my_awesome_project/settings.py",
            "tests/test_client.py",
            ".env.example",
        ]
        for file_path in expected:
            assert (generated_api_client_project / file_path).exists(), f"Missing file: {file_path}"
        assert not (generated_api_client_project / "tests/test_my_awesome_project.py").exists()

        pyproject = tomllib.loads((generated_api_client_project / "pyproject.toml").read_text())
        dependencies = [spec.split(">=")[0] for spec in pyproject["project"]["dependencies"]]
        assert sorted(dependencies) == ["httpx2", "pydantic", "pydantic-settings"]
        # An API client is a library: it installs no command on the caller's PATH.
        assert "scripts" not in pyproject["project"]

    def test_env_example_names_the_variables_the_settings_read(
        self, generated_api_client_project: Path
    ) -> None:
        """`.env.example` is what a user copies to `.env`.

        A variable there that the settings do not read is ignored without an
        error, and the user is left with a key that seems to be missing.
        """
        settings = (generated_api_client_project / "my_awesome_project/settings.py").read_text()
        env_example = (generated_api_client_project / ".env.example").read_text()

        assert 'ENV_PREFIX = "MY_AWESOME_PROJECT_"' in settings
        assert "\nMY_AWESOME_PROJECT_API_KEY=\n" in env_example

    def test_readme_points_to_the_env_example_in_each_language(self, tmp_path: Path) -> None:
        """The README is where a new user learns how to hand the key to the client."""
        project_dir = _generate_project(
            tmp_path / "client-readme", {"project_type": "api-client", "language": "Both"}
        )

        readme = (project_dir / "README.md").read_text()

        assert readme.count("`.env.example`") == 2, "Expected once per README language"
        assert readme.count("`Client.from_env()`") == 2
        assert readme.count("`uv run python -m my_awesome_project /some/path`") == 2

    def test_env_file_itself_is_ignored_by_git(self, generated_api_client_project: Path) -> None:
        """`.env` holds the real key, so only its example may be committed."""
        ignored = (generated_api_client_project / ".gitignore").read_text().splitlines()

        assert ".env" in ignored
        assert ".env.example" not in ignored

    def test_other_project_types_ship_no_client_scaffold(self, generated_project: Path) -> None:
        """A plain library must not gain an HTTP client or its dependencies."""
        for file_path in ("client.py", "errors.py", "settings.py"):
            assert not (generated_project / "my_awesome_project" / file_path).exists()
        assert not (generated_project / ".env.example").exists()
        assert not (generated_project / "tests/test_client.py").exists()
        assert not (generated_project / "tests/test_main.py").exists()
        assert (generated_project / "my_awesome_project/__init__.py").read_text() == ""
        assert "httpx2" not in (generated_project / "pyproject.toml").read_text()
        assert "API client" not in (generated_project / "AGENTS.md").read_text()

    def test_agents_md_states_the_client_rules(self, generated_api_client_project: Path) -> None:
        """The rules of the client outlive the scaffold only if the agents can read them.

        The errors are named after the package, so the rules must name the
        class that was generated.
        """
        agents_md = (generated_api_client_project / "AGENTS.md").read_text()

        assert "## API client" in agents_md
        assert "`MyAwesomeProjectError`" in agents_md
        assert "`httpx2.MockTransport`" in agents_md
        assert "{{" not in agents_md, "Unrendered template variable found"
        errors = (generated_api_client_project / "my_awesome_project/errors.py").read_text()
        assert "class MyAwesomeProjectError(Exception):" in errors

    def test_linting_passes(self, generated_api_client_project: Path) -> None:
        """A freshly generated API client must lint clean."""
        result = subprocess.run(
            ["uv", "run", "ruff", "check", "."],
            capture_output=True,
            text=True,
            cwd=generated_api_client_project,
        )
        assert result.returncode == 0, f"Ruff check failed: {result.stdout}\n{result.stderr}"

    def test_formatting_is_clean(self, generated_api_client_project: Path) -> None:
        """The first commit runs the formatter, so the scaffold must already be formatted.

        The package name is rendered into the code, which moves line breaks.
        """
        result = subprocess.run(
            ["uv", "run", "ruff", "format", "--check", "."],
            capture_output=True,
            text=True,
            cwd=generated_api_client_project,
        )
        assert result.returncode == 0, f"Ruff format failed: {result.stdout}\n{result.stderr}"

    @pytest.mark.parametrize("pkg_name", ["acme", "zebra"])
    def test_linting_and_formatting_hold_for_other_package_names(
        self, tmp_path: Path, pkg_name: str
    ) -> None:
        """The package name is rendered into sorted lists and into lines near the length limit.

        `AcmeError` sorts on either side of `APIError` depending on whether the
        order minds case, `ZebraError` sorts last, and a short name shortens
        lines that the default name wraps.
        """
        project_dir = _generate_project(
            tmp_path / pkg_name,
            {"project_type": "api-client", "directory_name": pkg_name, "pkg_name": pkg_name},
        )
        subprocess.run(["uv", "sync", "--dev"], cwd=project_dir, check=True, capture_output=True)

        check = subprocess.run(
            ["uv", "run", "ruff", "check", "."], capture_output=True, text=True, cwd=project_dir
        )
        formatting = subprocess.run(
            ["uv", "run", "ruff", "format", "--check", "."],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )

        assert check.returncode == 0, f"Ruff check failed: {check.stdout}\n{check.stderr}"
        assert formatting.returncode == 0, f"Ruff format failed: {formatting.stdout}"

    def test_type_checking_passes(self, generated_api_client_project: Path) -> None:
        """A freshly generated API client must pass pyright (strict)."""
        result = subprocess.run(
            ["uv", "run", "pyright"],
            capture_output=True,
            text=True,
            cwd=generated_api_client_project,
        )
        assert result.returncode == 0, f"Pyright failed: {result.stdout}\n{result.stderr}"

    def test_tests_pass(self, generated_api_client_project: Path) -> None:
        """The client's own test suite (MockTransport, no network) must pass."""
        result = subprocess.run(
            ["uv", "run", "pytest", "-v"],
            capture_output=True,
            text=True,
            cwd=generated_api_client_project,
        )
        assert result.returncode == 0, f"Tests failed: {result.stdout}\n{result.stderr}"
        assert "tests/test_client.py" in result.stdout

    def test_demo_runs_as_a_module(self, generated_api_client_project: Path) -> None:
        """The demo is how a new user checks the key and the base URL.

        It runs as `python -m <package>`, so the library still installs no
        command. Its behaviour is covered by the project's own tests.
        """
        assert (generated_api_client_project / "tests/test_main.py").exists()

        result = subprocess.run(
            ["uv", "run", "python", "-m", "my_awesome_project", "--help"],
            capture_output=True,
            text=True,
            cwd=generated_api_client_project,
        )

        assert result.returncode == 0, f"Demo failed: {result.stdout}\n{result.stderr}"
        assert "usage: python -m my_awesome_project" in result.stdout

    def test_api_reference_documents_the_client(self, generated_api_client_project: Path) -> None:
        """The docstrings of the client are its reference, and the strict build reads them."""
        result = subprocess.run(
            ["uv", "run", "mkdocs", "build", "--strict"],
            capture_output=True,
            text=True,
            cwd=generated_api_client_project,
        )

        assert result.returncode == 0, f"mkdocs build failed: {result.stdout}\n{result.stderr}"
        reference = (generated_api_client_project / "site/reference/index.html").read_text()
        assert "my_awesome_project.client" in reference
        assert "my_awesome_project.errors" in reference

    def test_passes_its_own_hooks(self, tmp_path: Path) -> None:
        """Bandit and the end-of-file fixer only run as hooks, so the suite runs them too.

        The first pass may rewrite files, as the post-generate task allows, so
        the second pass is the one that must be clean.
        """
        if not which("prek"):
            pytest.skip("prek not installed")
        project_dir = _generate_project(tmp_path / "client-hooks", {"project_type": "api-client"})
        subprocess.run(["uv", "sync", "--dev"], cwd=project_dir, check=True, capture_output=True)
        # prek needs a git repo to find files via --all-files
        subprocess.run(["git", "init", "-q"], cwd=project_dir, check=True)
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
        subprocess.run(["prek", "run", "--all-files"], cwd=project_dir, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)

        result = subprocess.run(
            ["prek", "run", "--all-files"], capture_output=True, text=True, cwd=project_dir
        )

        assert result.returncode == 0, f"Hooks failed:\n{result.stdout}\n{result.stderr}"
        assert "bandit" in result.stdout


class TestSpecFirstApiClient:
    """Test the spec_first option: agents that write `openapi.yaml`, and their init skill."""

    def test_ships_the_agents_and_the_init_skill(self, generated_spec_first_project: Path) -> None:
        """A spec-first client is derived from `openapi.yaml`, so the project needs what writes it.

        The agents are development tooling: their dependencies stay out of the
        package's own, and the wheel still holds the package alone.
        """
        expected = [
            "tools/__init__.py",
            "tools/openapi_agents/__init__.py",
            "tools/openapi_agents/__main__.py",
            "tools/openapi_agents/agents.py",
            "tools/openapi_agents/pipeline.py",
            "tools/openapi_agents/project.py",
            "tools/openapi_agents/settings.py",
            "tools/openapi_agents/upstream.py",
            "tools/openapi_agents/validation.py",
            "tests/tools/test_engine.py",
            "tests/tools/test_project.py",
            ".claude/skills/init-sdk/SKILL.md",
        ]
        for file_path in expected:
            assert (generated_spec_first_project / file_path).exists(), f"Missing file: {file_path}"

        pyproject = tomllib.loads((generated_spec_first_project / "pyproject.toml").read_text())
        dependencies = [spec.split(">=")[0] for spec in pyproject["project"]["dependencies"]]
        assert sorted(dependencies) == ["httpx2", "pydantic", "pydantic-settings"]
        tools = [spec.split(">=")[0] for spec in pyproject["dependency-groups"]["tools"]]
        assert tools == [
            "datamodel-code-generator",
            "openapi-spec-validator",
            "pydantic-ai-slim[openrouter]",
            "pyyaml",
        ]
        assert {"include-group": "tools"} in pyproject["dependency-groups"]["dev"]
        wheel = pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]
        assert wheel["packages"] == ["my_awesome_project"]
        assert pyproject["tool"]["pyright"]["include"] == ["my_awesome_project", "tests", "tools"]
        assert "--cov=tools" in pyproject["tool"]["pytest"]["ini_options"]["addopts"]

    def test_bare_api_client_ships_no_agents(self, generated_api_client_project: Path) -> None:
        """The option is opt-in: a client written by hand must not carry an LLM pipeline."""
        for path in ("tools", "tests/tools", ".claude"):
            assert not (generated_api_client_project / path).exists(), f"Unexpected: {path}"
        pyproject = (generated_api_client_project / "pyproject.toml").read_text()
        assert "pydantic-ai" not in pyproject
        assert "datamodel-codegen" not in pyproject
        assert "tools" not in tomllib.loads(pyproject)["dependency-groups"]
        hooks = (generated_api_client_project / ".pre-commit-config.yaml").read_text()
        assert "datamodel-codegen" not in hooks
        assert "openapi.yaml" not in (generated_api_client_project / "AGENTS.md").read_text()
        assert "OPENROUTER" not in (generated_api_client_project / ".env.example").read_text()

    def test_option_is_ignored_for_other_project_types(self, tmp_path: Path) -> None:
        """The agents write the document of an HTTP API, which only an API client has."""
        project_dir = _generate_project(
            tmp_path / "library", {"project_type": "library", "spec_first": True}
        )

        for path in ("tools", "tests/tools", ".claude"):
            assert not (project_dir / path).exists(), f"Unexpected: {path}"
        assert "pydantic-ai" not in (project_dir / "pyproject.toml").read_text()
        assert "spec_first" not in (project_dir / ".copier-answers.yml").read_text()

    def test_agents_md_gates_work_on_the_openapi_document(
        self, generated_spec_first_project: Path
    ) -> None:
        """No skill runs by itself, so the instructions every agent reads carry the gate.

        A project without `openapi.yaml` is not initialised, and the agent has
        to learn that, and where the procedure is, before it adds an endpoint.
        """
        agents_md = (generated_spec_first_project / "AGENTS.md").read_text()

        assert "### Spec-first" in agents_md
        assert "`openapi.yaml`" in agents_md
        assert "`.claude/skills/init-sdk/SKILL.md`" in agents_md
        assert "`uv run python -m tools.openapi_agents`" in agents_md
        assert "`uv run datamodel-codegen`" in agents_md
        assert "`my_awesome_project/models.py`" in agents_md
        assert "{{" not in agents_md, "Unrendered template variable found"

    def test_skill_names_the_generated_package(self, generated_spec_first_project: Path) -> None:
        """The skill sends the agent to the placeholders, so it must name the files that exist."""
        skill = (generated_spec_first_project / ".claude/skills/init-sdk/SKILL.md").read_text()

        assert skill.startswith("---\nname: init-sdk\n")
        assert "`my_awesome_project/settings.py`" in skill
        assert "`tools/openapi_agents/project.py`" in skill
        assert "`my_awesome_project/models.py`" in skill
        assert "{{" not in skill, "Unrendered template variable found"

    def test_env_example_names_the_key_of_the_agents(
        self, generated_spec_first_project: Path
    ) -> None:
        """The agents read their key from the same `.env` as the client, under another name."""
        env_example = (generated_spec_first_project / ".env.example").read_text()
        settings = (generated_spec_first_project / "tools/openapi_agents/settings.py").read_text()

        assert "\nMY_AWESOME_PROJECT_API_KEY=\n" in env_example
        assert "\nOPENROUTER_API_KEY=\n" in env_example
        assert "openrouter_api_key: SecretStr" in settings

    def test_readme_explains_the_run_in_each_language(self, tmp_path: Path) -> None:
        """A run spends money, so the README says how to start one and what it needs."""
        project_dir = _generate_project(
            tmp_path / "spec-first-readme",
            {"project_type": "api-client", "spec_first": True, "language": "Both"},
        )

        readme = (project_dir / "README.md").read_text()

        assert readme.count("uv run python -m tools.openapi_agents") == 2
        assert readme.count("`OPENROUTER_API_KEY`") == 2
        assert readme.count("uv run datamodel-codegen\n") == 2

    def test_project_module_is_kept_on_a_later_generation(self, tmp_path: Path) -> None:
        """The init skill rewrites `project.py` for one API, and an update must not undo that.

        The engine beside it stays a template file, so that fixes reach the project.
        """
        project_dir = tmp_path / "initialised"
        agents_dir = project_dir / "tools/openapi_agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "project.py").write_text("API_NAME = 'Weather'\n")

        _generate_project(project_dir, {"project_type": "api-client", "spec_first": True})

        assert (agents_dir / "project.py").read_text() == "API_NAME = 'Weather'\n"
        # Sanity check: the engine still arrived
        assert (agents_dir / "pipeline.py").exists()

    def test_linting_passes(self, generated_spec_first_project: Path) -> None:
        """The agents are linted with the rules of the project they are generated into."""
        result = subprocess.run(
            ["uv", "run", "ruff", "check", "."],
            capture_output=True,
            text=True,
            cwd=generated_spec_first_project,
        )
        assert result.returncode == 0, f"Ruff check failed: {result.stdout}\n{result.stderr}"

    def test_formatting_is_clean(self, generated_spec_first_project: Path) -> None:
        """The first commit runs the formatter, so the agents must already be formatted."""
        result = subprocess.run(
            ["uv", "run", "ruff", "format", "--check", "."],
            capture_output=True,
            text=True,
            cwd=generated_spec_first_project,
        )
        assert result.returncode == 0, f"Ruff format failed: {result.stdout}\n{result.stderr}"

    def test_type_checking_passes(self, generated_spec_first_project: Path) -> None:
        """Pyright (strict) covers `tools`, so the agents must pass it too."""
        result = subprocess.run(
            ["uv", "run", "pyright"],
            capture_output=True,
            text=True,
            cwd=generated_spec_first_project,
        )
        assert result.returncode == 0, f"Pyright failed: {result.stdout}\n{result.stderr}"

    def test_tests_pass(self, generated_spec_first_project: Path) -> None:
        """The agents ship with their tests, which replace the model and need no key.

        Each project locks its own pydantic-ai, so the tests travel with the code.
        """
        result = subprocess.run(
            ["uv", "run", "pytest", "-v"],
            capture_output=True,
            text=True,
            cwd=generated_spec_first_project,
        )
        assert result.returncode == 0, f"Tests failed: {result.stdout}\n{result.stderr}"
        assert "tests/tools/test_engine.py" in result.stdout
        assert "tests/test_client.py" in result.stdout

    def test_agents_refuse_to_run_before_the_project_is_initialised(
        self, generated_spec_first_project: Path
    ) -> None:
        """A run without sources would bill a model for a document about nothing.

        The run stops before it reads the key, and says where the procedure is.
        """
        # Sanity check: a new project vendors no source yet
        assert not (generated_spec_first_project / "upstream").exists()

        result = subprocess.run(
            ["uv", "run", "python", "-m", "tools.openapi_agents"],
            capture_output=True,
            text=True,
            cwd=generated_spec_first_project,
        )

        assert result.returncode == 2, f"Unexpected run: {result.stdout}\n{result.stderr}"
        assert ".claude/skills/init-sdk/SKILL.md" in result.stderr
        assert not (generated_spec_first_project / "openapi.yaml").exists()

    def test_passes_its_own_hooks(self, tmp_path: Path) -> None:
        """Bandit only runs as a hook, and the agents start a `git` subprocess.

        The first pass may rewrite files, as the post-generate task allows, so
        the second pass is the one that must be clean.
        """
        if not which("prek"):
            pytest.skip("prek not installed")
        project_dir = _generate_project(
            tmp_path / "spec-first-hooks", {"project_type": "api-client", "spec_first": True}
        )
        subprocess.run(["uv", "sync", "--dev"], cwd=project_dir, check=True, capture_output=True)
        # prek needs a git repo to find files via --all-files
        subprocess.run(["git", "init", "-q"], cwd=project_dir, check=True)
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
        subprocess.run(["prek", "run", "--all-files"], cwd=project_dir, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)

        result = subprocess.run(
            ["prek", "run", "--all-files"], capture_output=True, text=True, cwd=project_dir
        )

        assert result.returncode == 0, f"Hooks failed:\n{result.stdout}\n{result.stderr}"
        assert "bandit" in result.stdout

    @pytest.mark.parametrize("python_version", ["3.13", "3.14"])
    def test_models_are_generated_from_the_openapi_document(
        self, tmp_path: Path, python_version: str
    ) -> None:
        """`openapi.yaml` stays canonical only if nobody writes a model by hand.

        The generator targets the Python of the project, and its output is
        committed, so it has to pass the project's linter, formatter and type
        checker as it comes out, on each version the template supports.
        """
        project_dir = _generate_project(
            tmp_path / f"models-py{python_version.replace('.', '')}",
            {"project_type": "api-client", "spec_first": True, "python_version": python_version},
        )
        subprocess.run(["uv", "sync", "--dev"], cwd=project_dir, check=True, capture_output=True)
        (project_dir / "openapi.yaml").write_text(OPENAPI_DOCUMENT)

        generation = subprocess.run(
            ["uv", "run", "datamodel-codegen"], capture_output=True, text=True, cwd=project_dir
        )

        assert generation.returncode == 0, f"Generation failed: {generation.stderr}"
        models = (project_dir / "my_awesome_project/models.py").read_text()
        assert "class Forecast(BaseModel):" in models
        assert "class Sky(StrEnum):" in models
        # An API adds response fields without notice, and a model must not reject them.
        assert 'extra="ignore"' in models
        assert "as a Unix timestamp in seconds" in models
        for command in (
            ["ruff", "check", "."],
            ["ruff", "format", "--check", "."],
            ["pyright"],
            ["datamodel-codegen", "--check"],
        ):
            result = subprocess.run(
                ["uv", "run", *command], capture_output=True, text=True, cwd=project_dir
            )
            assert result.returncode == 0, f"{command} failed: {result.stdout}\n{result.stderr}"

    def test_hook_rejects_models_that_no_longer_match_the_document(self, tmp_path: Path) -> None:
        """A document changed without its models leaves the client describing another API.

        The hook is skipped while the project has no `openapi.yaml`, which the
        hooks test above covers. Here the document exists: the hooks must
        leave fresh models as the generator wrote them, and fail once the
        document moves on without them.
        """
        if not which("prek"):
            pytest.skip("prek not installed")
        project_dir = _generate_project(
            tmp_path / "models-hook", {"project_type": "api-client", "spec_first": True}
        )
        subprocess.run(["uv", "sync", "--dev"], cwd=project_dir, check=True, capture_output=True)
        (project_dir / "openapi.yaml").write_text(OPENAPI_DOCUMENT)
        subprocess.run(
            ["uv", "run", "datamodel-codegen"], cwd=project_dir, check=True, capture_output=True
        )
        # prek needs a git repo to find files via --all-files
        subprocess.run(["git", "init", "-q"], cwd=project_dir, check=True)
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
        subprocess.run(["prek", "run", "--all-files"], cwd=project_dir, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)

        matching = subprocess.run(
            ["prek", "run", "--all-files"], capture_output=True, text=True, cwd=project_dir
        )
        (project_dir / "openapi.yaml").write_text(OPENAPI_DOCUMENT.replace("high:", "highest:"))
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
        outdated = subprocess.run(
            ["prek", "run", "models-match-openapi", "--all-files"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )

        assert matching.returncode == 0, f"Hooks failed:\n{matching.stdout}\n{matching.stderr}"
        [hook_line] = [
            line for line in matching.stdout.splitlines() if "models match openapi.yaml" in line
        ]
        assert hook_line.endswith("Passed"), f"Hook did not run: {hook_line}"
        assert outdated.returncode != 0, "Hook accepted models that the document no longer matches"


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

    def test_forgejo_readme_names_the_secret_the_workflow_reads(self, tmp_path: Path) -> None:
        """The README says which secret to create, so it must match the workflow.

        Forgejo refuses secret names that start with GITHUB_, so a README that
        names one leaves the user unable to follow it.
        """
        project_dir = _generate_project(
            tmp_path / "fj-secret",
            {"ci_provider": "forgejo", "dependency_updates": "renovate", "language": "Both"},
        )
        # Sanity check: this is the secret the workflow reads
        workflow = (project_dir / ".forgejo/workflows/renovate.yml").read_text()
        assert "secrets.GH_COM_TOKEN" in workflow

        readme = (project_dir / "README.md").read_text()
        assert readme.count("`GH_COM_TOKEN`") == 2, "Expected once per README language"
        assert "GITHUB_COM_TOKEN" not in readme

    def test_none_ships_nothing(self, tmp_path: Path) -> None:
        """dependency_updates=none ships no Renovate config or runner."""
        project_dir = _generate_project(
            tmp_path / "no-renovate",
            {"ci_provider": "github", "dependency_updates": "none"},
        )
        assert not (project_dir / "renovate.json").exists()
        assert not (project_dir / ".github/workflows/renovate.yml").exists()
