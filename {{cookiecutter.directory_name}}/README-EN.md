# {{cookiecutter.directory_name}

{{cookiecutter.description}

## Development Environment

In order to run this project, you're going to need:

* Python >= 3.7
* [Poetry](https://python-poetry.org/docs/#installation)

Clone this repo and inside its folder run

`poetry install`

After this, you should be able to run the project.

### Aditional Tooling

Besides Poetry, this project also uses [`Pylint`](https://www.pylint.org/) for
static checking and [`black`](https://github.com/psf/black) as automated formatter.

We also use git hooks in order to assure that both Pylint and Black are executed
before commiting. The hooks are managed by `[pre-commit]'(https://pre-commit.com/).
