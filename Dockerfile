FROM python:alpine

WORKDIR /opt/bureaugraph

ADD ./client ./client
ADD ./model ./model
ADD ./app.py ./app.py
ADD ./requirements.txt ./requirements.txt

RUN python -m pip install -r requirements.txt

ENTRYPOINT [ "python", "app.py" ]
