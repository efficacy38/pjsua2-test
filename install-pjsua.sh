#!/bin/env bash
# install the compiler
sudo apt-get install -y gcc g++ build-essential swig python3-dev default-jdk python3-pip

# compile the pjsip binary
git clone https://github.com/pjsip/pjproject.git
cd pjproject
export CFLAGS="$CFLAGS -fPIC"
./configure --enable-shared
make dep && make & sudo make install && sudo ldconfig

# install pjsua2 python3 wrapper
cd pjsip-apps/src/swig/
make && sudo make install
