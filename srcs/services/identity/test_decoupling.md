Yes — **splitting `settings.py` out of `infrastructure/database/config` will decouple your architecture**, and after doing that, you may **not need to lazy-load `JWTTokenService` in `tests/fixtures/security.py`**.

 The important distinction is that there are **two different kinds of coupling** here.

 ## 1\. The current coupling

 Right now you effectively have:

```
tests/fixtures/security.py
        │
        ▼
JWTTokenService
        │
        ▼
database.config.settings
        │
        ▼
Settings()
```

 So importing a security fixture indirectly loads your **database configuration**.

 That's the undesirable coupling.

 After the refactor:

```
tests/fixtures/security.py
        │
        ▼
JWTTokenService
        │
        ▼
infrastructure.config.settings
```

 and separately:

```
database
   │
   ▼
infrastructure.config.settings
```

 So you get:

```
                 infrastructure/config/settings
                         ▲
                         │
              ┌──────────┴──────────┐
              │                     │
          database              security
```

 That's much better.

---

 ## 2\. Does that mean you can remove lazy loading?

 **Probably yes, but with one important condition.**

 If your new `settings.py` still does this:

```
settings = Settings()
```

 then importing:

```
from src.infrastructure.config.settings import settings
```

 still immediately validates **all required configuration**.

 So if `JWTTokenService` does:

```
from src.infrastructure.config.settings import settings
```

 then this:

```
from src.infrastructure.security.token.token_service import JWTTokenService
```

 will still instantiate:

```
Settings()
```

 during import.

 The difference is that it will no longer be loading **database configuration code**, but it will still require the complete application configuration.

---

 # 3\. In your specific case, I'd probably remove the lazy import

 Once you've moved `Settings` to:

```
src/infrastructure/config/settings.py
```

 I'd initially change `tests/fixtures/security.py` back to:

```
from src.infrastructure.security.token.token_service import JWTTokenService
```

 and:

```
@pytest.fixture
def jwt_token_service() -> JWTTokenService:
    return JWTTokenService()
```

 Then run:

```
uv run pytest tests.unit.application.test_login_account.py
```

 If it works, **keep it that way**.

 There's no need to introduce lazy imports just for the sake of avoiding imports.

---

 # 4\. But there's a deeper issue with your unit tests

 There's something I'd consider even more important than lazy loading.

 Your unit test:

```
tests.unit.application.test_login_account.py
```

 probably doesn't actually need:

```
JWTTokenService
```

 at all.

 Your application-level unit tests are already using:

```
FakeTokenService
```

 which is good.

 The problem is that `tests/fixtures/security.py` defines both:

```
FakeTokenService
```

 and:

```
JWTTokenService
```

 in the same fixture module.

 So pytest imports both.

 If you have:

```
from src.infrastructure.security.token.token_service import JWTTokenService
```

 at the top, Python imports the real infrastructure implementation even for tests that only need:

```
FakeTokenService
```

 That's a form of unnecessary coupling.

---

 # 5\. I'd actually separate those fixtures

 For your project, I'd consider:

```
tests/
└── fixtures/
    ├── security.py
    └── jwt.py
```

 ### `security.py`

 Only unit-test doubles:

```
class FakePasswordHasher:
    ...

class FakeTokenService:
    ...

@pytest.fixture
def password_hasher() -> FakePasswordHasher:
    return FakePasswordHasher()

@pytest.fixture
def token_service() -> FakeTokenService:
    return FakeTokenService()
```

 Then:

 ### `jwt.py`

 Real JWT implementation:

```
from src.infrastructure.security.token.token_service import JWTTokenService

@pytest.fixture
def jwt_token_service() -> JWTTokenService:
    return JWTTokenService()
```

 And:

```
pytest_plugins = [
    "tests.fixtures.accounts",
    "tests.fixtures.database",
    "tests.fixtures.http",
    "tests.fixtures.security",
    "tests.fixtures.sessions",
    "tests.fixtures.jwt",
]
```

 Now your separation is extremely explicit:

```
unit application tests
        │
        ▼
FakeTokenService
```

 while:

```
JWT infrastructure tests
        │
        ▼
JWTTokenService
        │
        ▼
Settings
```

---

 # 6\. You don't necessarily need a separate `jwt.py` fixture file

 If you don't have many JWT-specific tests, this is also perfectly reasonable:

```
# tests/fixtures/security.py

class FakePasswordHasher:
    ...

class FakeTokenService:
    ...

@pytest.fixture
def password_hasher() -> FakePasswordHasher:
    return FakePasswordHasher()

@pytest.fixture
def token_service() -> FakeTokenService:
    return FakeTokenService()

@pytest.fixture
def jwt_token_service():
    from src.infrastructure.security.token.token_service import JWTTokenService

    return JWTTokenService()
```

 That gives you a nice property:

```
Import security.py
        │
        ├── FakePasswordHasher
        │
        └── FakeTokenService

No infrastructure imports yet.
```

 Only when a test asks for:

```
jwt_token_service
```

 does the real JWT implementation get imported.

---

 # 7\. Which approach would I choose for your project?

 Given the architecture you've shown me, I'd do **both improvements**:

 ### Production code

 Move:

```
src/infrastructure/database/config/settings.py
```

 to:

```
src/infrastructure/config/settings.py
```

 and make:

```
database → config.settings
security → config.settings
```

 instead of:

```
security → database.config.settings
```

 ### Tests

 Keep:

```
FakeTokenService
```

 for application unit tests.

 And either:

 - put `JWTTokenService` in a separate `jwt.py` fixture module, **or**
- lazy-load it in the fixture.

 I slightly prefer the separate fixture module if you're going to have a growing JWT test suite.

---

 ## One important caveat

 Moving the file **doesn't automatically make your tests independent of configuration**.

 If you have:

```
# infrastructure/config/settings.py

settings = Settings()
```

 and:

```
# token_service.py

from src.infrastructure.config.settings import settings
```

 then importing `JWTTokenService` still requires valid configuration.

 So the architectural refactor solves:

 > "Why is my security code importing database configuration?"

 But it does **not** solve:

 > "Why does importing the real JWT implementation require all application settings?"

 Those are separate concerns.

 For your **application unit tests**, the cleanest answer is still to use `FakeTokenService` and avoid importing the real JWT implementation altogether. For **JWT infrastructure tests**, it's perfectly reasonable for them to require the JWT configuration.

 So I would aim for:

```
                    Settings
                       │
             ┌─────────┴─────────┐
             │                   │
        Database             JWT service
             │                   │
        integration          JWT tests
          tests
```

 while:

```
Application unit tests
          │
          ▼
   FakeTokenService
          │
          X
    no real Settings
```

 That's the decoupling you're really looking for.