import asyncio

# from concurrent.futures import process
import websockets
import pathlib
import pyvjoy
import ssl
import numpy as np
from scipy.spatial.transform import Rotation as R

# hostName = "localhost"
hostName = "0.0.0.0"
serverPort = 8082

j = pyvjoy.VJoyDevice(1)

alpha_old = 0.0
beta = 0.0


def toVJoy(message: str):
    global j
    global beta
    global alpha_old
    data = message.split(sep="_")
    data = list(map(lambda x: float(x), data))
    # print(data)
    x = max(0.0, min(1.0, 1.2 * data[0]))
    y = max(0.0, min(1.0, 1.2 * data[1]))

    dir = R.from_euler("ZXY", np.array(data[2:5]), True).as_matrix()[2, [0, 1]]

    alpha = np.arccos(dir[1])
    alpha *= 1 if dir[0] < 0 else -1
    alpha += np.pi / 2
    alpha = alpha if alpha < np.pi else alpha - 2 * np.pi

    da = alpha - alpha_old
    if np.abs(da) > np.abs(da + 2 * np.pi):
        da = da + 2 * np.pi
    elif np.abs(da) > np.abs(da - 2 * np.pi):
        da = da - 2 * np.pi

    beta += da
    alpha_old = alpha

    z = int(((beta / (2 * np.pi)) + 0.5) * 0x8000)

    # print(z, np.round(beta, 3))

    j.data.wAxisX = int(x * 0x8000)
    j.data.wAxisY = int(y * 0x8000)
    j.data.wAxisZ = z
    # j.data.wAxisZ= int(z*0x8000)
    # print(x,y)
    j.update()


async def reply(websocket):
    print("connection opened")
    # async for message in websocket:
    #    await toVJoy(message)
    while True:
        try:
            message = await websocket.recv()
        except:
            print("connection closed")
            break
        toVJoy(message)

    # greeting = f"Josen {message}!"
    # await websocket.send(greeting)
    # print(f">>> {greeting}")


async def main():
    # ssl_context.load_cert_chain("key.pem")
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile="./cert.pem", keyfile="./cert.pem")
    async with websockets.serve(reply, hostName, serverPort, ssl=ssl_context):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    print("start")
    asyncio.run(main())
