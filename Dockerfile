FROM python:3.9-buster

WORKDIR /src/Debs_bot_test

COPY requirements.txt /src/Debs_bot_test
RUN pip install -r /src/Debs_bot_test/requirements.txt
COPY . /src/Debs_bot_test
