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

- Python >= 3.8
- [Poetry](https://python-poetry.org/docs/#installation)

1. Clone this repo
2. Run `poetry install`
3. 🎆

## Development

`poetry install` installs the dependencies for development. You'll also need
[`pre-commit`](https://pre-commit.com/) available in your machine. After clonning,
run

```sh
pre-commit install -t pre-commit -t pre-push
```
{% endif %}

{% if cookiecutter.language == "Both" or cookiecutter.language == "PT-BR" %}

## Uso

Os requerimentos são

- Python >= 3.8
- [Poetry](https://python-poetry.org/docs/#installation)

1. Clone esse repositório
2. Execute `poetry install`
3. 🎆

## Desenvolvimento

`poetry install` instala as dependências necessárias. Você também precisará do
[`pre-commit`](https://pre-commit.com/) disponível em sua máquina. Depois de
clonar o projeto, execute

```sh
pre-commit install -t pre-commit -t pre-push
```

{% endif %}