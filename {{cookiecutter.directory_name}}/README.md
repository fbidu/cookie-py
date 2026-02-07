<h1 align="center">{{cookiecutter.project_name}}</h1>

---

[![](https://img.shields.io/badge/fbidu's%20cookiecutter-gray?style=for-the-badge&logo=cookiecutter)](https://github.com/fbidu/cookie-py)
<!-- Insert an image/gif/code snippet of the working project -->

{% if cookiecutter.language == "Both" %}
[🇧🇷 Descrição em Português](#uso)
{% endif %}
{% if cookiecutter.language == "Both" or cookiecutter.language == "EN" %}
## Usage

The requirements are

- Python >= {{cookiecutter.python_version}}
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

1. Clone this repo
2. Run `uv sync --dev` (or `pip install -e .` if using pip)
3. 🎆

## Development

This project uses modern Python tooling:

- **[uv](https://docs.astral.sh/uv/)** for fast dependency management and virtual environments
- **[ruff](https://docs.astral.sh/ruff/)** for linting and code formatting
- **[pyright](https://github.com/microsoft/pyright)** for type checking
- **[pytest](https://docs.pytest.org/)** for testing
- **[pre-commit](https://pre-commit.com/)** for git hooks
{% if cookiecutter.enable_spec_kit == "yes" %}

### Spec-Driven Development

This project includes [GitHub Spec Kit](https://github.com/github/spec-kit) for spec-driven development. Available commands: `/speckit.constitution`, `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`

See `.specify/` for configuration.
{% endif %}

### Setup

1. Install [uv](https://docs.astral.sh/uv/) and [pre-commit](https://pre-commit.com/) globally
2. Clone this repository
3. Run `uv sync --dev` to install dependencies
4. Run `pre-commit install --install-hooks` to setup git hooks
5. Run `pre-commit install -t pre-push` to setup push hooks

### Commands

- `uv run pytest` - Run tests
- `uv run ruff check .` - Run linting
- `uv run ruff format .` - Format code
- `pyright` - Run type checking
- `pre-commit run --all-files` - Run all pre-commit hooks

{% endif %}
{% if cookiecutter.language == "Both" or cookiecutter.language == "PT-BR" %}
## Uso

Os requerimentos são

- Python >= {{cookiecutter.python_version}}
- [uv](https://docs.astral.sh/uv/) (recomendado) ou pip

1. Clone esse repositório
2. Execute `uv sync --dev` (ou `pip install -e .` se usando pip)
3. 🎆

## Desenvolvimento

Este projeto usa ferramentas modernas do Python:

- **[uv](https://docs.astral.sh/uv/)** para gerenciamento rápido de dependências e ambientes virtuais
- **[ruff](https://docs.astral.sh/ruff/)** para linting e formatação de código
- **[pyright](https://github.com/microsoft/pyright)** para verificação de tipos
- **[pytest](https://docs.pytest.org/)** para testes
- **[pre-commit](https://pre-commit.com/)** para git hooks
{% if cookiecutter.enable_spec_kit == "yes" %}

### Desenvolvimento Orientado por Especificações

Este projeto inclui [GitHub Spec Kit](https://github.com/github/spec-kit) para desenvolvimento orientado por especificações. Comandos disponíveis: `/speckit.constitution`, `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`

Veja `.specify/` para configuração.
{% endif %}

### Configuração

1. Instale [uv](https://docs.astral.sh/uv/) e [pre-commit](https://pre-commit.com/) globalmente
2. Clone este repositório
3. Execute `uv sync --dev` para instalar dependências
4. Execute `pre-commit install --install-hooks` para configurar git hooks
5. Execute `pre-commit install -t pre-push` para configurar push hooks

### Comandos

- `uv run pytest` - Executar testes
- `uv run ruff check .` - Executar linting
- `uv run ruff format .` - Formatar código
- `pyright` - Executar verificação de tipos
- `pre-commit run --all-files` - Executar todos os pre-commit hooks

{% endif %}