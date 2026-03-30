###############################
#         Base Image          #
###############################
ARG BASE_IMAGE=python:3.10-slim

FROM $BASE_IMAGE AS base

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    make \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

###############################
#    Install  Dependencies    #
###############################
FROM base AS dependencies

COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --no-install-project

###############################
#        Build Image          #
###############################
FROM dependencies AS build

ARG BUILD_VERSION

COPY . /app/

# Update version in pyproject.toml
RUN sed -i "s/^version = \".*\"/version = \"${BUILD_VERSION}\"/" pyproject.toml

# Build the application
RUN uv build

###############################
#         Test  Image         #
###############################
FROM build AS test

RUN uv sync --extra parquet --extra dev

RUN J_PATH=reports/junit \
    C_PATH=reports/coverage \
    F_PATH=reports/flake8 && \
    # Run tests with coverage
    uv run coverage run -m pytest --junitxml=$J_PATH/junit.xml --html=${J_PATH}/report.html -k . && \
    uv run coverage xml -o $C_PATH/coverage.xml --omit="app/tests/*" && \
    uv run coverage html -d $C_PATH/htmlcov --omit="app/tests/*" && \
    # Generate badges
    uv run genbadge tests -o $J_PATH/test-badge.svg && \
    uv run genbadge coverage -o $C_PATH/coverage-badge.svg && \
    # Type checks (pyright replaces mypy)
    uv run pyright src/ && \
    # Lint checks (ruff replaces flake8)
    mkdir -p ${F_PATH} && \
    uv run ruff check src/ --output-format concise --statistics > ${F_PATH}/flake8stats.txt || \
    (cat ${F_PATH}/flake8stats.txt && exit 1) && \
    cat ${F_PATH}/flake8stats.txt && \
    uv run genbadge flake8 -i $F_PATH/flake8stats.txt -o $F_PATH/flake8-badge.svg
