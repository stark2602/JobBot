# syntax=docker/dockerfile:1
# Pin digest locally with: docker inspect python:3.12.14-slim-bookworm --format '{{index .RepoDigests 0}}'
FROM python:3.12.14-slim-bookworm AS build
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir .

FROM python:3.12.14-slim-bookworm AS runtime
WORKDIR /app
RUN useradd --create-home --uid 10001 jobbot
COPY --from=build /opt/venv /opt/venv
COPY src ./src
COPY JobBot ./JobBot
COPY infra/config ./infra/config
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    JOBBOT_ENV=production
USER jobbot
ENTRYPOINT ["python", "-m", "agent.cli", "--root", "/app"]
