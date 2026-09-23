# Python pinned to match CI (.github/actions/python-checks/action.yml) and the local venv,
# so the image runs the interpreter the tests actually ran against.
FROM python:3.12-slim

WORKDIR /app

# Poetry pinned for reproducible builds: an unpinned `pip install poetry` can change
# resolver behaviour between two builds of the same commit.
RUN pip install --no-cache-dir poetry==2.2.1

# Never build a virtualenv in the image. The container is already an isolated environment,
# so a venv only adds a layer and a path to get wrong. The env var beats any config file,
# including the committed poetry.toml.
ENV POETRY_VIRTUALENVS_CREATE=false

# Dependencies first, in their own layer: these two files change far less often than the
# source, so an edit to a route does not reinstall 132 packages.
COPY pyproject.toml poetry.lock ./
# --only main: the dev group (pytest, ruff, ipykernel) has no place in a runtime image.
RUN poetry install --only main --no-root --no-cache

COPY . .

# The import root is src/core, not the repo root (`pythonpath` in pyproject does the same
# for pytest), so `api.main` only resolves with --app-dir.
# Port 8000 matches ingress_target_port, pinned in infra-longlist/main.tf.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src/core"]
