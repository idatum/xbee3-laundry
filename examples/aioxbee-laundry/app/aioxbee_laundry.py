""" Run XBee controller based on aioxbee.
    Expecting XBEE_PORT, XBEE_BAUD env vars.
"""
import os
import logging
import logging.handlers
import sys
import asyncio
import serial_asyncio
import controller
import argparse

Log = logging.getLogger("aioxbee-laundry")


async def exit_timer(secs: int):
    """ Exit after secs during profiling """
    await asyncio.sleep(secs)
    sys.exit(0)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("--debug", required=False, action='store_true', default=False, help="Enable debugging output.")
    ap.add_argument("--profiler", required=False, action='store_true', default=False, help="Enable profiler.")
    args = ap.parse_args()
    
    debug = args.debug or args.profiler
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO,
                        format='%(asctime)s %(levelname)s:%(name)s:%(message)s',
                        datefmt='%m-%d-%Y %H:%M:%S')

    loop = asyncio.get_event_loop()
    loop.set_debug(debug)

    if args.profiler:
        # Profile for n seconds
        Log.warning('Starting exit timer.')
        loop.create_task(exit_timer(120))

    coro = serial_asyncio.create_serial_connection(loop, controller.Controller,
                                                   os.environ['XBEE_PORT'],
                                                   baudrate=int(os.environ['XBEE_BAUD']))
    loop.run_until_complete(coro)
    loop.run_forever()

    loop.close()
