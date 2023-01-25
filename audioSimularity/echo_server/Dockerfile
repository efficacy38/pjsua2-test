FROM python:3.10
RUN pip install jsonpickle humanfriendly
COPY ./pjsua-python.patch /
RUN apt-get update && \
    cd /tmp && \
    apt-get install -y gcc g++ build-essential swig python3-dev && \
    git clone https://github.com/pjsip/pjproject.git && \
    cd pjproject && \
    patch -p1 -i /pjsua-python.patch && \
    export CFLAGS="$CFLAGS -fPIC" && \
    ./configure --enable-shared && \
    make dep && make && make install && ldconfig && \
    cd pjsip-apps/src/swig/ && \
    make python && make install && \
    rm -rf /tmp/pjproject
COPY ./echo_server.py ./envDefault.py ./parseLog.py ./utils.py /
ENTRYPOINT ["python3", "echo_server.py"] 
