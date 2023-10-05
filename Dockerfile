###############################
#         Base Image          #
###############################
FROM python:3.11-slim AS base

WORKDIR /app

ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_NO_INTERACTION=1
ENV PATH="$PATH:$POETRY_HOME/bin"

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    make \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 - 

RUN poetry config virtualenvs.create false

###############################
#    Install  Dependencies    #
###############################
FROM base AS dependencies

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --extras "parquet"

###############################
#        Build Image          #
###############################
FROM dependencies AS build

ARG BUILD_VERSION

COPY . /app/

# Build the application
RUN poetry version $BUILD_VERSION && \
    poetry build

###############################
#         Test  Image         #
###############################
FROM build AS test

RUN poetry install --extras "parquet"

RUN J_PATH=reports/junit \
    C_PATH=reports/coverage \
    F_PATH=reports/flake8 && \
    # Run tests with coverage
    poetry run coverage run -m pytest --junitxml=$J_PATH/junit.xml --html=${J_PATH}/report.html && \
    poetry run coverage xml -o $C_PATH/coverage.xml --omit="app/tests/*" && \
    poetry run coverage html -d $C_PATH/htmlcov --omit="app/tests/*" && \
    # Generate badges
    poetry run genbadge tests -o $J_PATH/test-badge.svg && \
    poetry run genbadge coverage -o $C_PATH/coverage-badge.svg && \
    # Flake8 checks
    poetry run flake8 --exit-zero --format=html --htmldir ${F_PATH} --statistics --tee --output-file ${F_PATH}/flake8stats.txt && \
    poetry run genbadge flake8 -i $F_PATH/flake8stats.txt -o $F_PATH/flake8-badge.svg
