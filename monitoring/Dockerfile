# syntax=docker/dockerfile:1

FROM python:3.9-slim-buster

WORKDIR /app

COPY metrics_app/ .

RUN pip3 install -r requirements.txt

RUN pip3 install evidently==0.1.51.dev0

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=8085"]