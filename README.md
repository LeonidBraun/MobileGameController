# MobileGameController

## Prerequisites 
you need to install the vjoy-driver and openssl (comes with git).

## Multiplayer

start Configure VJoy and add the first 4 devices

## how to run:

### Create certificate(on Windows):
openssl.exe req -new -x509 -days 365 -nodes -out cert.pem -keyout cert.pem

or

& "C:\Program Files\Git\usr\bin\openssl.exe" req -new -x509 -days 365 -nodes -out cert.pem -keyout cert.pem

### Run HTML server and Socket Server

python3 server.py

python3 socket_server.py

### Connect with Phone

Make sure that your phone is in the same local network as the server. Make sure your firewall is not blocking anything.

Enter 'https://ServerIP:4443' into your browser.
