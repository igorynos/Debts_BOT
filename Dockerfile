FROM python:3.9-buster

WORKDIR /src/Debts_bot

COPY requirements.txt /src/Debts_bot
RUN pip install -r /src/Debts_bot/requirements.txt
COPY . /src/Debts_bot
