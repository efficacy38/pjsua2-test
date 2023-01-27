# pjsua2-test
This is a learning project of pjsua2.

## install pjsua and python3 wrapper version
```
cd pjsua2-test
sudo ./install-pjsua.sh
```

## build the pjsua2 environment
- use it with container
    1. `docker run -it --name pj-practice ghcr.io/efficacy38/pj-base python3`
- build the base image
    1. `cd pjsua2-container`
    2. `docker build -t pj-base .`
- test the image
    1. `docker run -it --rm pj-base python3`
    2. at python terminal, run the `>>> import pjsua2`, it is ok if no error occur

### Audio Simularity
- use client
    - docker package: `docker run -it -v ~/server.log:/server.log --network host  ghcr.io/efficacy38/echo-server -u {YOUR_USERNAME} -p {YOUR_PASSWORD} -R sip:{YOUR_SIP_SERVER_IP}`
    - standar usage 
        - `python3 client.py -u 1 -p test -R sip:kamailio -c "sip:2@kamailio" -t 1`
    - get some help `python3 client.py --help`
- use server
    - docker package: `docker run -it efficacy38/pj-client -u {YOUR_USERNAME} -p {YOUR_PASSWORD} -R sip:{YOUR_SIP_SERVER_IP} -c {CALL_URI} -t {CALL_DURATION} -r {SEQUENTIALLY_REPECT_TIMES}`
    - get some help `python3 echo_server.py --help`
