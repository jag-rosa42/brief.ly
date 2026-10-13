from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_parent_containing(marker: str) -> Path:
    """Find the closest parent directory of this module that contains `marker`.

    Walking up the tree instead of using a fixed `parents[n]` index keeps this
    working if the module is moved, and in the container, where the code lives
    under /app with the same layout as the repository.

    Raises:
        RuntimeError: If no parent directory contains `marker`.
    """
    for parent in Path(__file__).resolve().parents:
        if (parent / marker).exists():
            return parent
    raise RuntimeError(f"Could not find a parent directory containing {marker}")


# The service directory (srcs/services/identity) holds the service's .env.
BASE_DIR = _find_parent_containing("pyproject.toml")
_container_secrets = Path("/run/secrets")

if _container_secrets.exists():
    SECRETS_DIR = _container_secrets
else:
    # The repository root holds shared/secrets.
    ROOT_DIR = _find_parent_containing("compose.yaml")
    SECRETS_DIR = ROOT_DIR / "shared" / "secrets"


class ServiceSettings(BaseSettings):
    """
    Common base for every settings class of this service.

    It only says WHERE configuration comes from; each subclass says WHAT it
    needs. pydantic merges `model_config` into subclasses, so they all read:
    - real environment variables (highest priority)
    - the service's .env file
    - one file per secret in the secrets directory (/run/secrets in a
      container, shared/secrets locally)

    `extra="ignore"` matters here: every subclass reads the same .env, so each
    one must skip the variables that belong to the others.
    """

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        secrets_dir=SECRETS_DIR,
    )
