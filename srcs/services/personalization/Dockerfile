FROM python:3.14-slim

WORKDIR /app/srcs/services/personalization

COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /uvx /usr/local/bin/

ENV UV_PROJECT_ENVIRONMENT=/opt/venv

COPY ./pyproject.toml ./
COPY ./uv.lock ./

COPY --from=shared_errors / /app/shared/packages/shared_errors/
COPY --from=shared_auth / /app/shared/packages/shared_auth/

# --no-editable: production gets a plain copy of the shared packages in the
# virtual environment, not a link to their source folder.
RUN uv sync --frozen --no-install-project --no-editable

COPY . ./

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

