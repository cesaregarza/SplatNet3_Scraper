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
RUN poetry install

###############################
#        Build Image          #
###############################
FROM dependencies AS build

COPY . /app/

# Build the application
RUN poetry build

###############################
#         Test  Image         #
###############################
FROM build AS test

# Install dev dependencies
RUN poetry install

# Define common paths and options using shell variables for conciseness.
RUN J_PATH=reports/junit \
    C_PATH=reports/coverage \
    F_PATH=reports/flake8 && \
    # Run tests with coverage
    poetry run pytest --junitxml=$J_PATH/junit.xml --cov=app --cov-report=xml:$C_PATH/coverage.xml --cov-report=html:$C_PATH/report.html && \
    # Generate badges
    poetry run genbadge tests -o $J_PATH/test-badge.svg && \
    poetry run genbadge coverage -o $C_PATH/coverage-badge.svg && \
    # Flake8 checks
    poetry run flake8 app/ --output-file=$F_PATH/flake8.txt --statistics && \
    poetry run genbadge flake8 -i $F_PATH/flake8.txt -o $F_PATH/flake8-badge.svg


###############################
#        Publish Image        #
###############################
FROM dependencies AS publish

ARG PYPI_TOKEN

ENV POETRY_PYPI_TOKEN=$PYPI_TOKEN

# Publish to PyPI
RUN poetry publish --build
