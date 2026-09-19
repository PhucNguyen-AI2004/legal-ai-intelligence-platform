import pytest
from pydantic import ValidationError
from pathlib import Path

import yaml

from app.core.config import Settings


def production_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "_env_file": None,
        "app_name": "Legal AI",
        "app_env": "production",
        "database_url": "postgresql+psycopg://legal_ai:strong-production-password@postgres:5432/legal_ai",
        "secret_key": "a-production-secret-with-enough-random-looking-characters-123",
        "llm_model": "production-model",
        "llm_api_key": "provider-key-placeholder-for-test-only",
    }
    values.update(overrides)
    return Settings(**values)


def test_production_configuration_accepts_complete_external_values() -> None:
    assert production_settings().app_env == "production"


def test_root_path_defaults_empty_and_accepts_production_api_prefix() -> None:
    assert production_settings().root_path == ""
    assert production_settings(root_path="/api").root_path == "/api"


@pytest.mark.parametrize("value", ["api", "/api/"])
def test_root_path_rejects_ambiguous_prefixes(value: str) -> None:
    with pytest.raises(ValidationError):
        production_settings(root_path=value)


def test_production_compose_sets_proxy_root_path_and_disables_worker_http_healthcheck() -> None:
    compose = yaml.safe_load(Path("docker-compose.prod.yml").read_text(encoding="utf-8"))
    services = compose["services"]

    assert services["backend"]["environment"]["ROOT_PATH"] == "/api"
    assert services["worker"]["healthcheck"] == {"disable": True}


def test_production_database_url_accepts_percent_encoded_reserved_characters() -> None:
    settings = production_settings(
        database_url="postgresql+psycopg://legal_ai:p%40ss%3Aword%2Fwith%23reserved%25chars@postgres:5432/legal_ai"
    )
    assert settings.database_url.hosts()[0]["host"] == "postgres"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("secret_key", "local_dev_only_change_me"),
        ("database_url", "postgresql+psycopg://legal_ai:local_dev_only_change_me@postgres:5432/legal_ai"),
        ("database_url", "postgresql+psycopg://legal_ai:CHANGE_ME_URL_ENCODED_PASSWORD@postgres:5432/legal_ai"),
        ("llm_model", ""),
        ("llm_api_key", ""),
        ("llm_model", "CHANGE_ME_MODEL"),
        ("llm_api_key", "CHANGE_ME_PROVIDER_KEY"),
    ],
)
def test_production_configuration_rejects_unsafe_or_missing_values(field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        production_settings(**{field: value})
