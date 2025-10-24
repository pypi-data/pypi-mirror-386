# Getting Started

## Installation

Install using pip

```shell
pip install sphinx-gha
```

or by adding it as a documentation dependency for your python project

```{code-block} toml
:caption: pyproject.toml

[project.optional-dependencies]
docs = [
    "sphinx-gha",
]
```

then add sphinx-gha to the extensions list in your sphinx configuration

```{code-block} toml
:caption: docs/conf.py

extensions = ['sphinx_gha']
```

## Configuration

````{confval} sphinx_gha_repo_slug

**Required Config Value**

The slug to use for usage examples, in the form `https://example.com/username/repo`.

```{note}
Github Actions runners do not support specifying the full URL, and assume all actions are sourced from Github.com. If your action is hosted on Github.com you might want to make your users aware of this.
```

```{rubric} Example
```

```python
sphinx_gha_repo_slug = 'https://git.offworldcolonies.nexus/drewcassidy/sphinx-gha'
```

````

````{confval} sphinx_gha_repo_ref
:default: `sphinx_gha.git_ref.get_git_ref()`{l=py}

The current git ref to use in examples

By default this is calculated using the current git repo and/or ReadTheDocs builder environment variables. You hopefully do not need to override this.
````

````{confval} sphinx_gha_repo_root
:default: `os.cwd()`{l=py}

The root of you repository, used to calculate the relative path of action/workflow files

You can set this relative to your conf.py using the python `__file__` dunder variable

```{rubric} Example
```

```python
sphinx_gha_repo_root = str(Path(__file__).parent.parent.absolute())  # docs/..
```
````

## Usage

Document your actions and workflows using the {any}`gha:action` and {any}`gha:workflow` directives
