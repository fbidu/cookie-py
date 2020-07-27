# Bidu's Python Cookiecutter
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

<p align="center">
  
`cookiecutter gh:fbidu/cookie-py`

</p>

---

[:uk: English Description](#english)

Esse é um modelo básico de [cookiecutter](https://cookiecutter.readthedocs.io)
para projetos Python que inclui várias ferramentas que gosto de usar.

Um modelo de cookiecutter serve para criar novos projetos com base em um formato
pré-definido. No caso em todo projeto Python, eu gosto de usar certas ferramentas
como Black, PyTest, PyLint, Pre-Commit e Poetry. Esse meu modelo instala
tudo e configura tudo isso para mim!

É um modelo fortemente enviesado para o que eu gosto, uma vez que ele reflete
minhas escolhas particulares sobre ferramentas, análises estáticas, hooks e etc.

Sinta-se livre para usar, forkear e modificar a vontade!

### Uso

1. Instale o [Poetry](https://python-poetry.org/docs/#installation)
2. Instale o [Cookiecutter](https://cookiecutter.readthedocs.io/en/latest/installation.html)
3. Execute `cookiecutter gh:fbidu/cookie-py`
4. O seu terminal irá te perguntar tudo o que precisar!

### Itens Inclusos

_Itens marcados estão implementados!_

* [x] Usar o Poetry para gerenciar pacotes
* [x] Usar o pre-commit para cuidar de hooks pre-commit do git
* [x] Instalar o Pytest
* [x] Instalar o Black
* [x] Executar Pytest pre-push
* [x] Relatório de Coverage no Pytest
* [ ] Adicionar um Dockerfile simples que cuida das dependências do Poetry

### Hooks de Pre-Commit Habilitados

* [x] Black
* [x] Pylint

---

## 🇬🇧 English

This is a basic [cookiecutter](https://cookiecutter.readthedocs.io) template
for Python projects that includes everything I like to use.

A cookiecutter template is useful to create new projects based on a pre-defined
model. In every Python project I like to use some tools like Black, PyTest, PyLint, Pre-Commit and Poetry. This template install and sets up all those tools for me!

It is highly opinionated since it reflects my personal choices about tooling, 
static analysis, hooks and so on.

Feel free to use, fork and modify at will!

### Usage

1. Install [Poetry](https://python-poetry.org/docs/#installation)
2. Install [Cookiecutter](https://cookiecutter.readthedocs.io/en/latest/installation.html)
3. Run `cookiecutter gh:fbidu/cookie-py`
4. Your terminal will ask you everything it needs!

### Batteries Included

_Checked items are implemented_

* [x] Use Poetry to manage packages
* [x] Use Pre-commit to handle git pre-commit hooks
* [x] Install Pytest
* [x] Install Black
* [x] Run Pytest pre-push
* [x] Coverage report on Pytest
* [ ] Simple Dockerfile that handles Poetry dependencies

### Pre-Commit Hooks

* [x] Black
* [x] Pylint
