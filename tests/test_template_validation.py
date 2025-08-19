"""Test cookiecutter template structure and files."""

import json
from pathlib import Path

import pytest
import yaml


def test_cookiecutter_json_valid():
    """Test that cookiecutter.json is valid JSON."""
    cookiecutter_file = Path(__file__).parent.parent / "cookiecutter.json"
    assert cookiecutter_file.exists()
    
    with cookiecutter_file.open() as f:
        config = json.load(f)
    
    # Check required fields
    required_fields = [
        "project_name", "directory_name", "pkg_name", 
        "description", "author", "version", "license", "python_version"
    ]
    
    for field in required_fields:
        assert field in config, f"Missing required field: {field}"
    
    # Check that directory_name and pkg_name use templates
    assert "{{" in config["directory_name"]
    assert "{{" in config["pkg_name"]


def test_template_files_exist():
    """Test that essential template files exist."""
    template_dir = Path(__file__).parent.parent / "{{cookiecutter.directory_name}}"
    assert template_dir.exists()
    
    essential_files = [
        "pyproject.toml",
        "README.md",
        ".pre-commit-config.yaml",
        "conftest.py",
        "{{cookiecutter.pkg_name}}/__main__.py",
        "tests/__init__.py",
        "tests/test_{{cookiecutter.pkg_name}}.py",
    ]
    
    for file_path in essential_files:
        full_path = template_dir / file_path
        assert full_path.exists(), f"Template file missing: {file_path}"


def test_template_pyproject_toml():
    """Test that template pyproject.toml is valid."""
    pyproject_file = Path(__file__).parent.parent / "{{cookiecutter.directory_name}}" / "pyproject.toml"
    content = pyproject_file.read_text()
    
    # Check for cookiecutter variables
    assert "{{cookiecutter.directory_name}}" in content
    assert "{{cookiecutter.description}}" in content
    assert "{{cookiecutter.author}}" in content
    assert "{{cookiecutter.pkg_name}}" in content
    assert "{{cookiecutter.python_version}}" in content
    
    # Check for modern project structure
    assert "[project]" in content
    assert "[build-system]" in content
    assert "[tool.ruff" in content
    assert "[tool.pyright]" in content
    assert "[tool.pytest" in content
    
    # Check for uv-compatible structure
    assert "[project.optional-dependencies]" in content
    assert "dev = [" in content


def test_template_pre_commit_config():
    """Test that template .pre-commit-config.yaml is valid."""
    pre_commit_file = Path(__file__).parent.parent / "{{cookiecutter.directory_name}}" / ".pre-commit-config.yaml"
    assert pre_commit_file.exists()
    
    with pre_commit_file.open() as f:
        config = yaml.safe_load(f)
    
    # Check structure
    assert "repos" in config
    assert isinstance(config["repos"], list)
    
    # Check for ruff repository
    ruff_repos = [repo for repo in config["repos"] if "ruff-pre-commit" in repo.get("repo", "")]
    assert len(ruff_repos) > 0, "Missing ruff pre-commit repository"
    
    # Check for bandit
    bandit_repos = [repo for repo in config["repos"] if "bandit" in repo.get("repo", "")]
    assert len(bandit_repos) > 0, "Missing bandit repository"


def test_hooks_directory():
    """Test that hooks directory and files exist."""
    hooks_dir = Path(__file__).parent.parent / "hooks"
    assert hooks_dir.exists()
    assert hooks_dir.is_dir()
    
    # Check hook files
    post_gen_hook = hooks_dir / "post_gen_project.py"
    assert post_gen_hook.exists()
    
    # Check that hook uses uv instead of poetry
    content = post_gen_hook.read_text()
    assert "uv sync" in content
    assert "uv run" in content
    # Should not contain poetry commands
    assert "poetry install" not in content
    assert "poetry run" not in content


def test_dockerfile_uses_uv():
    """Test that Dockerfile uses uv instead of poetry."""
    dockerfile = Path(__file__).parent.parent / "Dockerfile"
    assert dockerfile.exists()
    
    content = dockerfile.read_text()
    assert "uv" in content
    assert "cookiecutter" in content
    # Should not contain poetry
    assert "poetry" not in content.lower()


def test_readme_mentions_uv():
    """Test that README mentions uv instead of poetry."""
    readme = Path(__file__).parent.parent / "README.md"
    assert readme.exists()
    
    content = readme.read_text()
    assert "uv" in content
    assert "ruff" in content
    assert "pyright" in content
    # Should not prominently feature old tools
    assert content.count("poetry") < content.count("uv")
    assert content.count("black") < content.count("ruff")


def test_github_workflows_exist():
    """Test that GitHub workflows exist and use modern actions."""
    workflows_dir = Path(__file__).parent.parent / ".github" / "workflows"
    assert workflows_dir.exists()
    
    test_workflow = workflows_dir / "test-template.yml"
    assert test_workflow.exists()
    
    content = test_workflow.read_text()
    # Should use modern action versions
    assert "actions/checkout@v4" in content
    assert "actions/setup-python@v5" in content
    assert "astral-sh/setup-uv@v3" in content
    assert "uv sync" in content