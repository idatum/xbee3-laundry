#!/bin/sh

docker build -t aioxbee-laundry .
xbee_laundry=<add your XBee module address>
docker run --rm \
           --device=/dev/ttyUSB0 \
           -e XBEE_PORT=/dev/ttyUSB0 \
           -e XBEE_BAUD=115200 \
           -e XBEE_LAUNDRY=$xbee_laundry \
           -v /etc/localtime:/etc/localtime:ro \
           --log-driver json-file --log-opt max-size=2m --log-opt max-file=8 \
           --name aioxbee-laundry \
           aioxbee-laundry
