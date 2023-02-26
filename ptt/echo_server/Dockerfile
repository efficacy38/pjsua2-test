FROM ghcr.io/efficacy38/pj-base:main
RUN pip install jsonpickle humanfriendly
COPY ./echo_server.py ./envDefault.py ./parseLog.py ./utils.py /
ENTRYPOINT ["python3", "echo_server.py"] 
