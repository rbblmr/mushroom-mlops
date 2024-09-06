FROM python:3.9-slim

RUN pip install --upgrade pip && pip install pipenv
RUN apt-get update && apt-get install -y --no-install-recommends apt-utils
RUN apt-get -y install curl
RUN apt-get install libgomp1

WORKDIR /app

COPY [ "Pipfile", "Pipfile.lock", "*.py","./" ]

RUN pipenv install --system --deploy


