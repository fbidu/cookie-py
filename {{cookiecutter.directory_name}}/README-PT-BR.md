# {{cookiecutter.directory_name}

{{cookiecutter.description}

## Ambiente de Desenvolvimento

Para rodar esse projeto, você precisará de:

* Python >= 3.7
* [Poetry](https://python-poetry.org/docs/#installation)

Clone esse repositório e execute dentro da pasta

`poetry install`

Após o processo, você deverá ser capaz de rodar o projeto.

### Ferramentas Adicionais

Além do Poetry, esse projeto também define o uso do [ `Pylint` ](https://www.pylint.org/)
como verificador estático de código e do [ `black` ](https://github.com/psf/black)
como formatador automático.

Embora `black` e `pylint` possam ser executados manualmente, nós também utilizamos
de git hooks para garantir que eles sejam executados _antes_ de um commit. Esses
hooks são gerenciados pelo `[pre-commit]` (https://pre-commit.com/).
