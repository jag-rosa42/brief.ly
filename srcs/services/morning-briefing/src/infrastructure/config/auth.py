from shared_auth import AuthSettings

from src.infrastructure.config.base import BASE_DIR, SECRETS_DIR

auth_settings = AuthSettings(_env_file=BASE_DIR / ".env", _secrets_dir=SECRETS_DIR)
