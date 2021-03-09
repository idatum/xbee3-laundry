FROM python:3.9

RUN python -m pip install --disable-pip-version-check paho-mqtt
RUN python -m pip install --disable-pip-version-check pyserial_asyncio

# Copy and install python xbee
COPY ./aioxbee/pythonxbee /root/pythonxbee
WORKDIR /root/pythonxbee
RUN python /root/pythonxbee/setup.py install
RUN rm -rf /root/pythonxbee

ADD /aioxbee/app /app/
ADD /app /app/

WORKDIR /app

CMD [ "python", "/app/aioxbee_laundry.py", "--debug" ]
