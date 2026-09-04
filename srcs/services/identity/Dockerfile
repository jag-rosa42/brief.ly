FROM python:3.14-slim

WORKDIR /transcendence

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

ENV UV_PROJECT_ENVIRONMENT=/opt/venv

COPY srcs/services/identity ./srcs/services/identity

COPY shared/packages ./shared/packages

WORKDIR /transcendence/srcs/services/identity

RUN uv sync --frozen

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
