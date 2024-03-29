import os
import logging
import json
import argparse
from collections import deque
import paho.mqtt.client as mqtt

Log = logging.getLogger('mqtt-laundry')

MQTT_host = "localhost"
MQTT_port = 1883
MQTT_TLS = False
MQTT_qos = 2
# Topic to receive laundry XBee data.
XBee3_laundry_topic = None
# Topic to publish laundry state.
Laundry_state_topic = "Laundry/state"

WasherQ = deque(maxlen=20)
DryerQ = deque(maxlen=20)
WasherThreshold = 20.0
DryerThreshold = 20.0
WasherState = False
DryerState = False


def parse_xbee3_payload(data):
    data_pairs = {}
    readings = "".join(data).split('&')
    for reading in readings:
        param = reading.split("=")
        if len(param) < 2:
            continue
        try:
            data_pairs[param[0]] = float(param[1])
        except ValueError:
            data_pairs[param[0]] = param[1]

    return data_pairs


def send_laundry_state(client):
    Log.debug(f"Sending laundry state: WasherState={WasherState}, DryerState={DryerState}")
    payload = {"Washer": "on" if WasherState else "off", "Dryer": "on" if DryerState else "off"}
    info = client.publish(topic=Laundry_state_topic, payload=json.dumps(payload), qos=MQTT_qos, retain=True)
    if mqtt.MQTT_ERR_SUCCESS != info[0]:
        Log.warning(info)


def on_connect(client, userdata, flags, rc):
    Log.info("Connected")
    client.subscribe(topic=XBee3_laundry_topic, qos=MQTT_qos)


def on_message(client, userdata, message):
    global DryerState, WasherState
    try:
        topic = message.topic
        data = message.payload.decode()
        if userdata:
            Log.debug(f"userdata: {userdata}")
        if topic != XBee3_laundry_topic:
            Log.warning(f"Unexpected topic: {topic}")
            return
        data_pairs = parse_xbee3_payload(data)
        # Expecting 2 ADC measurements.
        if len(data_pairs) < 2:
            Log.warning("Missing laundry ADC measurement.")
            return
        # Washer is XBee pin DIO1, dryer is DIO2.
        adc1 = data_pairs["A1"]
        adc2 = data_pairs["A2"]
        WasherQ.append(adc1)
        DryerQ.append(adc2)
        washerAvg = sum(WasherQ) / len(WasherQ)
        dryerAvg = sum(DryerQ) / len(DryerQ)
        Log.debug(f'Washer avg={washerAvg:.1f}, Dryer avg={dryerAvg:.1f}')
        # Detect current state and state change.
        dryerState = dryerAvg > DryerThreshold
        dryerChanged = dryerState != DryerState
        washerState = washerAvg > WasherThreshold
        washerChanged = washerState != WasherState
        if washerChanged:
            WasherState = washerState
            Log.info(f"Washer state changed to {WasherState}")
        if dryerChanged:
            DryerState = dryerState
            Log.info(f"Dryer state changed to {DryerState}")
        # Publish MQTT laundry state topics
        if washerChanged or dryerChanged:
            send_laundry_state(client)
    except Exception as e:
        Log.exception(e)


def loop():
    # Expecting MQTT credential variables in env.
    client = mqtt.Client()
    client.enable_logger(logger=Log)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_log = lambda x: Log.info("Log: %s", x)
    client.username_pw_set(username=os.environ['MQTT_USERNAME'], password=os.environ['MQTT_PASSWORD'])
    if MQTT_TLS:
        client.tls_set()
    client.connect(host=MQTT_host, port=MQTT_port)
    client.loop_forever()

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("--debug", required=False, action='store_true', default=False, help="Enable debugging output.")
    ap.add_argument("--host", required=False, default=MQTT_host, help="MQTT hostname")
    ap.add_argument("--port", required=False, default=MQTT_port, type=int, help="MQTT port")
    ap.add_argument("--tls", required=False, action='store_true', default=MQTT_TLS, help="Use TLS for MQTT.")
    ap.add_argument("--xbee", required=True, default=XBee3_laundry_topic, help="XBee data MQTT topic.")
    ap.add_argument("--state", required=False, default=Laundry_state_topic, help="Laundry state MQTT topic.")
    args = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format='%(asctime)s %(levelname)s:%(name)s:%(message)s',
                        datefmt='%m-%d-%Y %H:%M:%S')

    MQTT_host = args.host
    MQTT_port = args.port
    MQTT_TLS = args.tls
    XBee3_laundry_topic = args.xbee
    Laundry_state_topic = args.state

    loop()
