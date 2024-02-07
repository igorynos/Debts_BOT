FROM python:3.9-buster

WORKDIR /src/Debts_bot_test

COPY requirements.txt /src/Debts_bot_test
RUN pip install -r /src/Debts_bot_test/requirements.txt
COPY . /src/Debts_bot_test
