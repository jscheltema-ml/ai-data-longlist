import logging
from pathlib import Path

from pydantic import ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


# .env lives at the repo root, one level above api/. Resolve it off __file__ rather than
# relying on the CWD, which differs between the local uvicorn run and the container (/app).
_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Config(BaseSettings):
    """
    A class to contain all configuration variables defined in the config directory of the repo.

    The `BaseSettings` class will try to find values (of any field without default values) from the environment
    variables. If no default value is provided, and no variable with the same name is found in the environment
    variables, a Validation Error will be thrown.

    Matching field names to environment variables is case-insensitive by default
    (i.e. azure_api_key WILL match with AZURE_API_KEY).

    The environment variables are defined in infra-longlist/main.tf, some come from the config JSON files,
    some are secrets stored in Key Vault and injected as container app secrets.
    """

    # extra="ignore": tolerate env keys this model doesn't declare.
    # env_file_encoding prevents issues between running locally and in the container
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Secrets ────────────────────────────────────────────────
    azure_api_key: str
    # Unset disables analytics entirely rather than failing startup.
    posthog_api_key: str | None = None

    # ── Azure OpenAI ───────────────────────────────────────────
    azure_endpoint: str
    azure_api_version: str
    # Deployment name as created in the Azure OpenAI resource, not a bare model name.
    llm_deployment: str

    # ── Foundry ───────────────────────────────────────────
    foundry_endpoint: str
    foundry_deployment: str

    # ── Auth ───────────────────────────────────────────────────
    app_client_id: str
    azure_tenant_id: str

    # ── Observability ──────────────────────────────────────────
    environment: str
    posthog_host: str | None = None
    log_level: str | None = "INFO"
    noisy_log_level: str | None = "DEBUG"
    # Deployed path only; unset locally, which skips the App Insights exporter.
    applicationinsights_connection_string: str | None = None

    # ── Run persistence ────────────────────────────────────────
    # These select the run-store backend: storage_account_name → Azure, else
    # archive_local_dir → local files, else persistence is disabled. All optional
    # by design, so the app boots without any of them.
    storage_account_name: str | None = None
    storage_container_name: str | None = None
    archive_local_dir: str | None = None

    # Managed identity client id; absent when running locally.
    azure_client_id: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _blank_is_unset(cls, values: dict) -> dict:
        """
        Before loading the values into the model, filter out any keys whose value is None or an empty string.

        A blank variable in the .env file, or an empty string assigned by terraform will be treated as "unset",
        in which case the field will not be passed to the model, and instead the default value will be used.
        """
        return {k: v for k, v in values.items() if v is not None and v != ""}


# Don't raise ValidationError directly as it contains the values of the environment variables,
# some of which are secrets. Instead we log the env name and error type
# (e.g. Field required, String should have at least 1 character, etc.)
try:
    config = Config()
except ValidationError as e:
    # compile a list of environment variable names and their corresponding error messages
    problems = "\n".join(f"  - {error['loc'][0]:<40}:     {error['msg']}" for error in e.errors(include_input=False))

    # only logger.error will work due to logging configuration being setup after config is loaded (see logging_setup.py)
    logger.error(f"Invalid configuration, check the environment variables: \n{problems}")
    raise RuntimeError(f"Invalid configuration, check the environment variables: \n{problems}") from None

except Exception as e:
    logger.error(f"Encountered an unexpected error: {e}")
    raise
