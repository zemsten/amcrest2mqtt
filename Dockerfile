FROM python:3.9-alpine as base


RUN mkdir /app
COPY setup.py /app
COPY VERSION /app
COPY src /app/src
WORKDIR /app
RUN ls /app

RUN python3 setup.py install

CMD [ "amcrest2mqtt" ]
