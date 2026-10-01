Yes. I would refactor this so that **`infrastructure/config/settings.py` owns application configuration**, while **`infrastructure/database/config/` owns SQLAlchemy-specific setup**.

 The key principle is:

 > `Settings` knows what configuration exists. The database package knows how to turn database configuration into engines/connections.

 That also fixes the architectural smell you currently have where `JWTTokenService` imports something called `database.config.settings`.

 ## 1\. Recommended structure

 I'd aim for:

```
src/
└── infrastructure/
    ├── config/
    │   ├── __init__.py
    │   └── settings.py
    │
    ├── database/
    │   ├── __init__.py
    │   └── config/
    │       ├── __init__.py
    │       ├── engine.py
    │       └── session.py          # optional, if you have session setup
    │
    └── security/
        └── token/
            └── token_service.py
```

 Depending on your project, you may not need `database/config/` at all. You could have:

```
src/
└── infrastructure/
    ├── config/
    │   └── settings.py
    ├── database/
    │   ├── engine.py
    │   └── session.py
    └── security/
        └── token/
            └── token_service.py
```

 I actually prefer the second version unless `database/config/` is already an established convention in your project.

---

 # 2\. What goes into `infrastructure/config/settings.py`

 Your `Settings` class should contain **configuration values**, including database, JWT, CORS, etc.

 So most of your current file moves there.

 I'd make it look approximately like this:

```
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]

_container_secrets = Path("/run/secrets")

if _container_secrets.exists():
    SECRETS_DIR = _container_secrets
else:
    ROOT_DIR = Path(__file__).resolve().parents[6]
    SECRETS_DIR = ROOT_DIR / "shared" / "secrets"

class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables
    and Docker secrets.
    """

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        secrets_dir=SECRETS_DIR,
    )

    # -----------------------------------------------------------------------
    # Application
    # -----------------------------------------------------------------------

    PROJECT_NAME: str

    # -----------------------------------------------------------------------
    # CORS
    # -----------------------------------------------------------------------

    BACKEND_CORS_ORIGINS: list[str] = []

    # -----------------------------------------------------------------------
    # Database
    # -----------------------------------------------------------------------

    DATABASE_DIALECT: Literal["postgresql"] = "postgresql"
    DATABASE_DRIVER: Literal["psycopg", "asyncpg"] = "psycopg"

    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr

    POSTGRES_DB_NAME: str
    POSTGRES_TEST_DB_NAME: str | None = None
    POSTGRES_DEFAULT_DB_NAME: str = "postgres"

    # -----------------------------------------------------------------------
    # JWT
    # -----------------------------------------------------------------------

    JWT_ALGORITHM: Literal["HS256", "RS256"] = "RS256"

    JWT_PRIVATE_KEY: SecretStr
    JWT_PUBLIC_KEY: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

settings = Settings()
```

 Notice what disappeared:

```
PostgresDsn
ClassVar
computed_field
_build_database_uri()
SQLALCHEMY_DATABASE_URI
TEST_DATABASE_URI
alembic_database_uri
```

 Those aren't really **application settings**.

 They're database infrastructure behavior.

---

 # 3\. What goes into `infrastructure/database/config/`?

 This is where I would put your database URL construction and SQLAlchemy objects.

 For example:

```
infrastructure/
└── database/
    └── config/
        ├── __init__.py
        └── engine.py
```

 ### `engine.py`

 Something like:

```
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from src.infrastructure.config.settings import settings

def build_database_url(
    *,
    database: str,
    driver: str,
) -> str:
    """
    Build a PostgreSQL SQLAlchemy URL.
    """

    return (
        f"{settings.DATABASE_DIALECT}+{driver}://"
        f"{settings.POSTGRES_USER}:"
        f"{settings.POSTGRES_PASSWORD.get_secret_value()}@"
        f"{settings.POSTGRES_HOST}:"
        f"{settings.POSTGRES_PORT}/"
        f"{database}"
    )

DATABASE_URL = build_database_url(
    database=settings.POSTGRES_DB_NAME,
    driver=settings.DATABASE_DRIVER,
)

engine: Engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)
```

 However, because you're already using `PostgresDsn`, I'd actually preserve that rather than manually concatenating strings.

---

 # 4\. I'd keep `PostgresDsn` in the database module

 For example:

```
from pydantic import PostgresDsn

from src.infrastructure.config.settings import settings

def build_database_url(
    *,
    database: str,
    driver: str,
) -> str:
    return str(
        PostgresDsn.build(
            scheme=f"{settings.DATABASE_DIALECT}+{driver}",
            username=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD.get_secret_value(),
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            path=database,
        )
    )
```

 Then:

```
DATABASE_URL = build_database_url(
    database=settings.POSTGRES_DB_NAME,
    driver=settings.DATABASE_DRIVER,
)
```

 This is a much cleaner responsibility boundary.

---

 # 5\. What about the test database URL?

 This is also database infrastructure, so I'd move:

```
TEST_DATABASE_URI
```

 out of `Settings`.

 For example:

```
# infrastructure/database/config/engine.py

from pydantic import PostgresDsn

from src.infrastructure.config.settings import settings

def build_database_url(
    *,
    database: str,
    driver: str,
) -> str:
    return str(
        PostgresDsn.build(
            scheme=f"{settings.DATABASE_DIALECT}+{driver}",
            username=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD.get_secret_value(),
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            path=database,
        )
    )

def get_application_database_url() -> str:
    return build_database_url(
        database=settings.POSTGRES_DB_NAME,
        driver=settings.DATABASE_DRIVER,
    )

def get_test_database_url() -> str:
    database = (
        settings.POSTGRES_TEST_DB_NAME
        or f"{settings.POSTGRES_DB_NAME}_test"
    )

    return build_database_url(
        database=database,
        driver="psycopg",
    )

def get_alembic_database_url() -> str:
    return build_database_url(
        database=settings.POSTGRES_DB_NAME,
        driver="psycopg",
    )
```

 Then your pytest fixture becomes:

```
from src.infrastructure.database.config.engine import get_test_database_url

@pytest.fixture(scope="session")
def database_url() -> str:
    url = get_test_database_url()

    _assert_test_database(url)
    _create_test_database_if_needed(url)

    return url
```

 That is much cleaner than:

```
settings.TEST_DATABASE_URI
```

 because `TEST_DATABASE_URI` isn't really a setting supplied by the environment.

 It's a **derived database resource URL**.

---

 # 6\. Your `POSTGRES_DEFAULT_DB_NAME` stays in Settings

 This one is slightly different.

 Keep:

```
POSTGRES_DEFAULT_DB_NAME: str = "postgres"
```

 in `Settings`.

 Why?

 Because this is configuration:

 > "Which PostgreSQL database should I initially connect to when creating/checking another database?"

 Then your database infrastructure uses it:

```
def get_default_database_url() -> str:
    return build_database_url(
        database=settings.POSTGRES_DEFAULT_DB_NAME,
        driver="psycopg",
    )
```

 And your test fixture can use that when creating the test database.

 For example:

```
def _create_test_database_if_needed(url: str) -> None:
    target_url = make_url(url)

    database_name = target_url.database

    if not database_name:
        raise RuntimeError("Test database URL has no database name")

    existing_db_url = target_url.set(
        database=settings.POSTGRES_DEFAULT_DB_NAME
    )

    engine = create_engine(
        existing_db_url,
        isolation_level="AUTOCOMMIT",
    )

    ...
```

 This is exactly where that setting belongs.

---

 # 7\. What should `database/config/__init__.py` contain?

 Keep this minimal.

 For example:

```
from .engine import (
    engine,
    get_alembic_database_url,
    get_application_database_url,
    get_test_database_url,
)

__all__ = [
    "engine",
    "get_alembic_database_url",
    "get_application_database_url",
    "get_test_database_url",
]
```

 Or even better, don't expose everything through `__init__.py` unless you actually need it.

 Then imports are explicit:

```
from src.infrastructure.database.config.engine import engine
```

 I generally prefer that while the project is still evolving.

---

 # 8\. The important dependency direction

 After the refactor, you get this:

```
                    ┌─────────────────────┐
                    │      Settings       │
                    │ infrastructure/    │
                    │ config/settings.py  │
                    └──────────┬──────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
       ┌─────────────────┐          ┌──────────────────┐
       │    Database     │          │     Security     │
       │ infrastructure │          │ infrastructure   │
       └─────────────────┘          └──────────────────┘
```

 So:

```
database → settings
```

 and:

```
JWT → settings
```

 but **not**:

```
JWT → database.settings
```

 That's the main architectural improvement.

---

 # 9\. Your JWT service becomes cleaner

 Currently you apparently have:

```
from src.infrastructure.database.config.settings import settings
```

 inside `token_service.py`.

 After the refactor:

```
from src.infrastructure.config.settings import settings
```

 Now it makes semantic sense:

```
JWTTokenService
      │
      ▼
  application
  configuration
```

 rather than:

```
JWTTokenService
      │
      ▼
database configuration
```

---

 # 10\. One thing I'd change in your naming

 I'd consider renaming:

```
DATABASE_DIALECT
DATABASE_DRIVER
```

 to something like:

```
DATABASE_DIALECT
DATABASE_DRIVER
```

 and leave them as-is for now.

 They're fine.

 But I would **not** put things like:

```
SQLALCHEMY_DATABASE_URI
TEST_DATABASE_URI
alembic_database_uri
```

 inside `Settings`.

 These are computed infrastructure values.

 A useful mental distinction is:

 ### Settings

 Things you configure externally:

```
POSTGRES_HOST
POSTGRES_PORT
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB_NAME

JWT_ALGORITHM
JWT_PRIVATE_KEY
JWT_PUBLIC_KEY

ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS
```

 ### Database infrastructure

 Things your application derives from those settings:

```
database URL
test database URL
Alembic URL
SQLAlchemy Engine
SessionFactory
```

---

 # 11\. One caveat: your `BASE_DIR` calculation must change

 This is important.

 Your current file is:

```
src/infrastructure/database/config/settings.py
```

 and you're using:

```
BASE_DIR = Path(__file__).resolve().parents[4]
```

 Once you move it to:

```
src/infrastructure/config/settings.py
```

 the number of `.parents[]` changes.

 Don't blindly copy:

```
parents[4]
```

 into the new file.

 For example, assuming your structure is:

```
identity/
├── .env
├── src/
│   └── infrastructure/
│       └── config/
│           └── settings.py
```

 then:

```
Path(__file__).resolve()
```

 is:

```
identity/src/infrastructure/config/settings.py
```

 and the project root is:

```
identity/
```

 which is:

```
Path(__file__).resolve().parents[3]
```

 Similarly, your current:

```
ROOT_DIR = Path(__file__).resolve().parents[7]
```

 will need to be recalculated after moving the file.

 I'd actually avoid magic numbers entirely if possible.

---

 # 12\. My preferred final arrangement

 I'd personally end up with:

```
src/
└── infrastructure/
    ├── config/
    │   ├── __init__.py
    │   └── settings.py
    │
    ├── database/
    │   ├── __init__.py
    │   ├── engine.py
    │   └── session.py
    │
    └── security/
        └── token/
            └── token_service.py
```

 ### `config/settings.py`

 Contains:

```
Settings
settings
```

 ### `database/engine.py`

 Contains:

```
build_database_url()
get_application_database_url()
get_test_database_url()
get_alembic_database_url()
engine
```

 ### `database/session.py`

 Contains things such as:

```
SessionLocal
get_db()
```

 if that's where your current `get_db`/session factory belongs.

 ### `security/token/token_service.py`

 Contains:

```
JWTTokenService
```

 and imports:

```
from src.infrastructure.config.settings import settings
```

---

 ## The resulting relationship is clean

```
                     config/settings.py
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
         database/engine.py      security/token/
                │                       │
                ▼                       ▼
          SQLAlchemy               JWTTokenService
```

 And importantly, **`Settings` doesn't need to know about SQLAlchemy, Alembic, or JWT implementation details**. It simply describes the application's configuration.

 That would be the refactor I'd recommend for your current project.