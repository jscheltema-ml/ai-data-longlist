import os

# api.config instantiates Config() at IMPORT time and every field below has no
# default, so a missing one raises a ValidationError before a single test runs. Set
# harmless dummy values here in conftest so they exist before pytest imports ANY test
# module — hence before the first `import api.config` / `api.main`, whatever the
# collection order. (A per-test-file block breaks the moment another test imports app
# code first and caches `config` with no creds — e.g. test_config.) CI has no real
# credentials and no real calls are made; setdefault leaves a local .env untouched.
#
# KEEP IN SYNC with the required (default-less) fields of Config in api/config.py.
os.environ.setdefault("AZURE_API_KEY", "dummy")
os.environ.setdefault("AZURE_ENDPOINT", "https://dummy.openai.azure.com/")
os.environ.setdefault("AZURE_API_VERSION", "2024-02-01")
os.environ.setdefault("LLM_DEPLOYMENT", "dummy-deployment")
os.environ.setdefault("FOUNDRY_ENDPOINT", "https://dummy.services.ai.azure.com/api/projects/dummy")
os.environ.setdefault("FOUNDRY_DEPLOYMENT", "dummy-foundry-deployment")
os.environ.setdefault("APP_CLIENT_ID", "dummy-app-client-id")
os.environ.setdefault("AZURE_TENANT_ID", "dummy-tenant-id")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("POSTHOG_HOST", "https://eu.i.posthog.com")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("NOISY_LOG_LEVEL", "WARNING")
