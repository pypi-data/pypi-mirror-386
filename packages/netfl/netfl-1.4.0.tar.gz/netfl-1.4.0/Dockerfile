FROM python:3.12.3-slim-bookworm

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    net-tools iproute2 iputils-ping && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY netfl ./netfl
COPY README.md .
COPY pyproject.toml .

RUN pip install --no-cache-dir .

ENV PYTHONPATH=/app
