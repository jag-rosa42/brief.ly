from src.application.port.api_key.generator import GeneratedApiKey
from src.infrastructure.security.api_key_generator import SecretsApiKeyGenerator


class TestSecretsApiKeyGenerator:
    def test_key_starts_with_tr_and_carries_256_random_bits(self) -> None:
        generated: GeneratedApiKey = SecretsApiKeyGenerator().generate()

        assert generated.key.startswith("tr_")
        # 32 bytes in URL-safe base64, without padding: 43 characters.
        assert len(generated.key) == len("tr_") + 43

    def test_prefix_is_the_first_seven_characters(self) -> None:
        generated: GeneratedApiKey = SecretsApiKeyGenerator().generate()

        assert generated.prefix == generated.key[:7]
        assert len(generated.prefix) == 7

    def test_every_key_is_different(self) -> None:
        generator = SecretsApiKeyGenerator()

        keys: set[str] = {generator.generate().key for _ in range(100)}

        assert len(keys) == 100
