FROM python:3.13-slim

RUN apt-get update && \
    apt-get install --no-install-recommends -y libpq5 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && pip install poetry
RUN poetry config virtualenvs.create false

COPY . /code
WORKDIR /code
# Install all groups (incl. dev) so the CI image self-test (gunicorn.sh with
# TESTING=1 -> pytest) has pytest available.
RUN poetry install

CMD ["/code/run/gunicorn.sh"]
