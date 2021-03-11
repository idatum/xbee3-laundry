""" XBee Coordinator.
Expecting XBEE_LAUNDRY, XBEE_PORT, XBEE_BAUD env vars set.
"""
import struct
import os
import struct
from collections import deque
import logging
import aiozigbee

Log = logging.getLogger(__name__)

Laundry_Address = struct.pack(">Q", int(os.environ['XBEE_LAUNDRY'], 16))

class Controller(aiozigbee.ZigbeeAsyncSerialBase):
    """ Override aiozigbee base controller and handle laundry state """
    def __init__(self):
        super().__init__()
        self.address_data = {}
        # Laundry state: moving average of 20 readings with threshold of 20.
        self.washerQ = deque(maxlen=20)
        self.dryerQ = deque(maxlen=20)
        self.washerThreshold = 20.0
        self.dryerThreshold = 20.0
        self.washerState = None
        self.dryerState = None

    async def process_laundry_state(self, data: str):
        """ Calculate current laundry state. """
        # Washer is XBee pin DIO1, dryer is DIO2.
        self.washerQ.append(data["A1"])
        self.dryerQ.append(data["A2"])
        washerAvg = sum(self.washerQ) / len(self.washerQ)
        dryerAvg = sum(self.dryerQ) / len(self.dryerQ)
        Log.info(f'Washer avg={washerAvg:.1f}, Dryer avg={dryerAvg:.1f}')

        # Detect current state and state change.
        washerState = washerAvg > self.washerThreshold
        washerChanged = washerState != self.washerState
        dryerState = dryerAvg > self.dryerThreshold
        dryerChanged = dryerState != self.dryerState
        if washerChanged:
            self.washerState = washerState
            Log.info(f"=== Washer state changed to {self.washerState} ===")
        if dryerChanged:
            self.dryerState = dryerState
            Log.info(f"=== Dryer state changed to {self.dryerState} ===")

    async def process_laundry_data(self, data):
        """ Publish raw ADC values """
        # Expecting a packet with string that looks like: "A1=0&A2=0\r"
        data_pairs = {}
        try:
            readings = data.split('&')
            if len(readings) < 2:
                raise Exception("Malformed laundry packet.")
            a1_split = readings[0].split("=")
            if len(a1_split) < 2:
                raise Exception("Malformed laundry A1 reading.")
            a2_split = readings[1].split("=")
            if len(a2_split) < 2:
                raise Exception("Malformed laundry A2 reading.")
            data_pairs[a1_split[0]] = float(a1_split[1])
            data_pairs[a2_split[0]] = float(a2_split[1])
        except Exception as e:
            Log.exception(e)

        await self.process_laundry_state(data_pairs)

    # override
    async def handle_samples(self, address, samples):
        # Ignore samples
        Log.debug(f"{address} {samples}")

    # override
    async def handle_rx_data(self, address, rx_data):
        """ Handle data packet """
        if address != Laundry_Address:
            Log.debug('Not handling rx_data for {}: {}'.format(self.hex_address(address), rx_data))
            return
        # Data message terminated with "\r", fields are name=value, seperated by "&".
        # Frames can contain a partial message.
        data_splits = rx_data.decode('utf-8').split("\r")
        for i in range(len(data_splits)):
            data_split = data_splits[i].strip()
            if len(data_split) == 0:
                continue
            elif (i + 1) == len(data_splits):
                # partial data
                if address in self.address_data:
                    self.address_data[address] += data_split
                else:
                    self.address_data[address] = data_split
            else:
                # completed data
                await self.handle_data_tuple(address, data_split)

    async def handle_data_tuple(self, address, data):
        """ Handle complete data packet """
        if address in self.address_data:
            Log.debug("continuation of data")
            previous_data = self.address_data[address]
            del self.address_data[address]
            data = previous_data + data
        Log.debug(f"calling {self.process_laundry_data}")
        await self.process_laundry_data(data)
