FROM python:3.13-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . .
RUN uv sync --frozen --no-dev

# NLTK data used by /chunk (sentence tokenization).
RUN uv run python -c "import nltk; nltk.download('punkt_tab', quiet=True)"

ENV PATH="/app/.venv/bin:$PATH"

RUN chmod +x /app/start.sh

EXPOSE 8000

CMD ["./start.sh"]
