FROM python:3.6
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
RUN mkdir /config

ADD /requirements.txt /config
RUN pip install -r /config/requirements.txt

ADD . /code
WORKDIR /code