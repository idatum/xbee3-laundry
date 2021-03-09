#!/bin/sh

docker build -t aioxbee-laundry .

docker run --rm \
           --device=/dev/ttyUSB0 \
           -e XBEE_PORT=/dev/ttyUSB0 \
           -e XBEE_BAUD=115200 \
           -e XBEE_LAUNDRY=0x0013A20041B7B024 \
           -v /etc/localtime:/etc/localtime:ro \
           --log-driver json-file --log-opt max-size=2m --log-opt max-file=8 \
           --name aioxbee-laundry \
           aioxbee-laundry
