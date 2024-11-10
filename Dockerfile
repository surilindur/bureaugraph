FROM python:alpine

WORKDIR /opt/quill

ADD ./client ./client
ADD ./commands ./commands
ADD ./events ./events
ADD ./graph ./graph
ADD ./updates ./updates
ADD ./app.py ./app.py
ADD ./requirements.txt ./requirements.txt

RUN python -m pip install -r requirements.txt

RUN adduser --no-create-home --disabled-password --uid 1000 --shell /bin/bash quill

USER quill

ENTRYPOINT [ "python", "app.py" ]
