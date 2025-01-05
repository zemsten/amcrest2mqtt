FROM python:3.13-alpine as base


RUN mkdir /app
COPY setup.py /app
COPY VERSION /app
COPY src /app/src
COPY bin /app/bin
WORKDIR /app

RUN python3 setup.py install

CMD [ "amcrest2mqtt" ]
