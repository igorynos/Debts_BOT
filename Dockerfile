FROM python:3.9-buster

WORKDIR /src/Debs_bot

COPY requirements.txt /src/Debs_bot
RUN pip install -r /src/Debs_bot/requirements.txt
COPY . /src/Debs_bot
