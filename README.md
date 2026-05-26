# Bidu's Python Template
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

<p align="center">

`copier copy gh:fbidu/cookie-py my-project`

</p>

---

[:uk: English Description](#english)

Esse é um modelo de projeto Python usando [Copier](https://copier.readthedocs.io)
que inclui várias ferramentas modernas que gosto de usar.

Um template Copier serve para criar novos projetos com base em um formato
pré-definido. No caso em todo projeto Python, eu gosto de usar certas ferramentas
como Ruff, PyTest, Pyright, Pre-Commit e uv. Esse meu modelo instala
tudo e configura tudo isso para mim!

É um modelo fortemente enviesado para o que eu gosto, uma vez que ele reflete
minhas escolhas particulares sobre ferramentas, análises estáticas, hooks e etc.

Sinta-se livre para usar, forkear e modificar a vontade!

### Uso

1. Instale o [uv](https://docs.astral.sh/uv/getting-started/installation/)
2. Instale o [Copier](https://copier.readthedocs.io/en/stable/#installation): `uv tool install copier`
3. Execute `copier copy gh:fbidu/cookie-py meu-projeto`
4. O seu terminal irá te perguntar tudo o que precisar!

### Itens Inclusos

_Itens marcados estão implementados!_

* [x] Usar o uv para gerenciar pacotes e ambientes virtuais
* [x] Usar o pre-commit para cuidar de hooks pre-commit do git
* [x] Instalar o Pytest com plugins úteis (coverage, xdist, randomly)
* [x] Instalar o Ruff para formatação e linting
* [x] Instalar o Pyright para verificação de tipos
* [x] Executar Pytest pre-push
* [x] Relatório de Coverage no Pytest
* [x] Configurações modernas em pyproject.toml
* [x] Pipeline de CI opcional (GitHub Actions ou GitLab CI)
* [x] Atualização de projetos existentes com `copier update`

### Hooks de Pre-Commit Habilitados

* [x] Ruff (linting e formatação)
* [x] Pyright (verificação de tipos)
* [x] Bandit (segurança)
* [x] actionlint (valida workflows do GitHub Actions, quando aplicável)
* [x] Hooks básicos (trailing whitespace, end-of-file, etc.)

---

## English

This is a Python project template using [Copier](https://copier.readthedocs.io)
that includes modern tools I like to use.

A Copier template is useful to create new projects based on a pre-defined
model. In every Python project I like to use some tools like Ruff, PyTest,
Pyright, Pre-Commit and uv. This template installs and sets up all those
tools for me!

It is highly opinionated since it reflects my personal choices about tooling,
static analysis, hooks and so on.

Feel free to use, fork and modify at will!

### Usage

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
2. Install [Copier](https://copier.readthedocs.io/en/stable/#installation): `uv tool install copier`
3. Run `copier copy gh:fbidu/cookie-py my-project`
4. Your terminal will ask you everything it needs!

### Batteries Included

_Checked items are implemented_

* [x] Use uv to manage packages and virtual environments
* [x] Use Pre-commit to handle git pre-commit hooks
* [x] Install Pytest with useful plugins (coverage, xdist, randomly)
* [x] Install Ruff for linting and formatting
* [x] Install Pyright for type checking
* [x] Run Pytest pre-push
* [x] Coverage report on Pytest
* [x] Modern pyproject.toml configuration
* [x] Optional CI pipeline (GitHub Actions or GitLab CI)
* [x] Update existing projects with `copier update`

### Pre-Commit Hooks

* [x] Ruff (linting and formatting)
* [x] Pyright (type checking)
* [x] Bandit (security)
* [x] actionlint (validates GitHub Actions workflows, when applicable)
* [x] Basic hooks (trailing whitespace, end-of-file, etc.)
