FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system nethealth && useradd --system --gid nethealth nethealth
WORKDIR /app
COPY --from=builder /install /usr/local
COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app
RUN chown -R nethealth:nethealth /app
USER nethealth

EXPOSE 8000
CMD ["sh", "-c", "set -- $(hostname -i); exec uvicorn app.main:app --host \"$1\" --port 8000"]
