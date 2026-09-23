import pytest
from pydantic import ValidationError  # noqa: E402

from api.config import Config  # noqa: E402


def _build() -> Config:
    """Build a Config from the environment only.

    ``_env_file=None`` disables the .env source so a developer's populated
    ``src/core/.env`` cannot mask a var these tests deliberately unset. The
    required fields all come from conftest's ``os.environ.setdefault`` block.
    """
    return Config(_env_file=None)


def test_config_reads_required_fields_from_uppercase_env_vars(monkeypatch):
    # Field names are lowercase; matching against the environment is case-insensitive.
    monkeypatch.setenv("AZURE_API_VERSION", "2099-01-01")
    assert _build().azure_api_version == "2099-01-01"


def test_config_raises_error_for_missing_required_fields(monkeypatch):
    """
    Test that a validation error is raised when a set of required fields are missing from the environment variables,
    and that the validation error message contains the names of the missing fields.
    """
    monkeypatch.delenv("APP_CLIENT_ID", raising=False)
    monkeypatch.delenv("AZURE_API_KEY", raising=False)
    with pytest.raises(ValidationError) as excinfo:
        _build()
    message = str(excinfo.value)
    assert "app_client_id" in message
    assert "azure_api_key" in message


def test_config_raises_error_for_empty_required_fields(monkeypatch):
    # _blank_is_unset treats "" as unset; with no default to fall back on, that is still an error.
    monkeypatch.setenv("AZURE_ENDPOINT", "")
    with pytest.raises(ValidationError):
        _build()


def test_config_blank_optional_fields_fall_back_to_defaults(monkeypatch):
    # Terraform injects "" for unset optional vars, and .env.example ships them blank,
    # so `cp .env.example .env` must boot with the declared defaults intact.
    for name in ("POSTHOG_API_KEY", "STORAGE_ACCOUNT_NAME", "LOG_LEVEL", "NOISY_LOG_LEVEL"):
        monkeypatch.setenv(name, "")
    config = _build()
    assert config.log_level == "INFO"
    assert config.noisy_log_level == "DEBUG"
    assert config.posthog_api_key is None
    assert config.storage_account_name is None


def test_config_unknown_env_vars_are_ignored(monkeypatch):
    # extra="ignore" — the container gets env vars no field maps to (e.g. KEY_VAULT_URL).
    monkeypatch.setenv("SOME_VAR_NO_FIELD_MAPS_TO", "whatever")
    assert not hasattr(_build(), "some_var_no_field_maps_to")
