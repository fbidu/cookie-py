# Bidu's Basic Python Cookiecutter

This is a basic [cookiecutter](https://cookiecutter.readthedocs.io) template
for Python projects that includes everything I like to use.

It is highly opinionated since it reflects my personal choices about tooling,
static analysis, hooks and so on.

Feel free to use, fork and modify at will!

## Usage

1. Install [Cookiecutter](https://cookiecutter.readthedocs.io/en/latest/installation.html)

2. Run `cookiecutter gh:fbidu/cookie-py`

## Batteries Included

Checked items are implemented

* [x] Use Poetry to manage packages
* [x] Use Pre-commit to handle git pre-commit hooks
* [x] Install Pytest
* [x] Install Black
* [ ] Simple Dockerfile that handles Poetry dependencies


### Pre-Commit Hooks
* [x] Black
* [x] Pylint