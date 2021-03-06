""" Read washer and dryer CT sensor values. """

import time
from machine import ADC
from micropython import const
import xbee

# XBee ZigBee
xb = xbee.XBee()
# Sum ADC readings n times before transmitting.
Sum_count = 5
# Delay between transmitting summed ADC readings.
Transmit_sleep_s = 10
# Delay between consecutive ADC readings.
Readings_sleep_s = .01

def wait_association():
    """Wait for association with network."""

    while True:
        ai = xb.atcmd('AI')
        if ai == 0:
            print('Associated')
            break
        else:
            print('Not associated')
        time.sleep(0.25)


def process_packet(payload):
    """Process rx_data packet.
       Set global settings with data packet in format name:value.
       e.g. Transmit_sleep_s:10"""

    global Sum_count
    global Transmit_sleep_s
    global Readings_sleep_s

    payload_split = payload.split(':')
    if len(payload_split) == 2:
        if payload_split[0] == 'Transmit_sleep_s':
            Transmit_sleep_s = float(payload_split[1])
        elif payload_split[0] == 'Sum_count':
            Sum_count = int(payload_split[1])
        elif payload_split[0] == 'Readings_sleep_s':
            Readings_sleep_s = float(payload_split[1])


def wait_receive(Transmit_sleep_s):
    """Poll every delay_ms milliseconds for rx_data packet.
       Wait for Transmit_sleep_s seconds before giving up."""

    delay_ms = const(125)
    ticks0 = time.ticks_ms()
    test_ticks = lambda : time.ticks_diff(time.ticks_ms(), ticks0) >= (1000 * Transmit_sleep_s)
    while True:
        packet = xbee.receive()
        if packet:
            # Ignore broadcast.
            if 'broadcast' in packet and not packet['broadcast']:
                # Packet received; exit delay.
                return packet
        if test_ticks():
            # No packet received within delay seconds.
            return None
        time.sleep_ms(delay_ms)


def transmit_data(a1, a2):
    """Transmit ADC values."""

    msg = 'A1={}&A2={}\r'.format(a1, a2)
    xbee.transmit(xbee.ADDR_COORDINATOR, msg.encode())


def main():
    """Main laundry processing loop reads and transmits
       ADC values and processes received packets."""

    # Washer
    adc1 = ADC("D1")
    # Dryer
    adc2 = ADC("D2")
    while True:
        # Take N readings and sum
        a1_sum = 0
        a2_sum = 0
        for i in range(Sum_count):
            a1 = adc1.read()
            a2 = adc2.read()
            a1_sum += a1
            a2_sum += a2
            time.sleep(Readings_sleep_s)
        print("a1=" + str(a1_sum) + " a2=" + str(a2_sum))
        # Transmit readings to coordinator.
        transmit_data(a1_sum, a2_sum)
        # Delay while polling for received packet.
        packet = wait_receive(Transmit_sleep_s)
        if packet and 'payload' in packet:
            payload = packet['payload'].decode('UTF-8')
            print(payload)
            process_packet(payload)

if __name__ == '__main__':
    # Process loop to handle exceptions and keep running.
    while True:
        try:
            wait_association()
            main()
        except Exception as e:
            print(e)
            time.sleep(1)
