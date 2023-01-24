FROM python:3.10
RUN pip install jsonpickle humanfriendly
RUN apt-get update
COPY ./install-pjsua.sh /
RUN /install-pjsua.sh
COPY ./client.py ./envDefault.py ./input.16.wav ./parseLog.py ./utils.py /
ENTRYPOINT python3 client.py

