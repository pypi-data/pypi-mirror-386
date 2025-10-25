# Contributing to Fast-Vindex

## Development workflow

### Creating a Python Environment

Before starting any development, you’ll need to create an isolated development environment:

```bash
# Create the build environment
mamba env create -n fast-vindex-tests -f ci/requirements/environment.yml

# Activate the environment
mamba activate fast-vindex-tests

# Build and install pytcube
pip install -e . --no-deps
```

```{note}
The `environment.yml` file contains the dependencies for `tests` and `docs`.
```

````{note}
Using an `environment.yml` file allows you to specify the exact version numbers of each dependency required in `pyproject.toml`, which then enables you to install the library with:

```bash
pip install -e . --no-deps
```
````

### Install pre-commit hooks

We highly recommend that you setup pre-commit hooks to automatically run all the above tools every time you make a git commit. To install the hooks:

```bash
pre-commit install
```

This can be done by running:

```bash
pre-commit run
```

from the root of the repository. You can skip the pre-commit checks with git commit --no-verify.

## Contributing to the documentation

### About the documentation

* The documentation consists of two parts: the docstrings in the code itself and the docs in this folder `fast_vindex/docs/`.
* The docstrings follow the `Google style` Standard

### How to build the documentation

To build the documentation run:

```bash
cd docs/
make html
```

To clean the build run:

```bash
make clean
```
