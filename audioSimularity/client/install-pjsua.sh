#!/bin/bash
# install the compiler
apt-get install -y gcc g++ build-essential swig python3-dev default-jdk python3-pip

cd /tmp
# compile the pjsip binary
git clone https://github.com/pjsip/pjproject.git
cd pjproject
export CFLAGS="$CFLAGS -fPIC"
./configure --enable-shared
make dep && make & make install && ldconfig

# install pjsua2 python3 wrapper
cd pjsip-apps/src/swig/
make && make install

rm -rf /tmp/pjproject
