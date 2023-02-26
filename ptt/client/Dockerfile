FROM ghcr.io/efficacy38/pj-base:main
RUN pip install jsonpickle humanfriendly
COPY ./client.py ./envDefault.py ./input.16.wav ./parseLog.py ./utils.py /
ENTRYPOINT ["python3", "client.py"] 
