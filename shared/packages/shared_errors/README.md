# Shared Errors Package

## Package Layout

This package uses the standard Python src layout:
```shell
shared_errors/
├── pyproject.toml
├── README.md
└── src/
    └── shared_errors/
        ├── __init__.py
        ├── handlers.py
        └── schemas.py
```

The two shared_errors directories have different purposes:

- `shared_errors/` at the project root is the project/distribution directory. It contains the package metadata, documentation, lock file, and source code.
- `src/` is the source root. It separates the package source code from project-level files.
- `src/shared_errors/` is the actual Python package and therefore the namespace used by imports.

This means the package is installed and imported as:
```python
from shared_errors.handlers import ...
from shared_errors.schemas import ...
```

rather than importing from `src` directly.

Although this results in the path:
```python
shared_errors/src/shared_errors/
```

the duplication is intentional. The outer `shared_errors` identifies the project, while the inner `shared_errors` identifies the Python package.

This layout also allows the project to follow Python packaging conventions and lets Hatchling automatically discover the package without additional package-selection configuration.