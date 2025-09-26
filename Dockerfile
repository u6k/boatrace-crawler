FROM python:3.9.16-bullseye
LABEL maintainer="u6k.apps@gmail.com"

RUN apt-get update && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    # Install Poetry
    curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/ && \
    poetry config virtualenvs.create false

# Install poetry packages
WORKDIR /var/myapp
VOLUME /var/myapp

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

CMD ["poetry", "run", "python", "./boatrace_mq/main.py"]
