import asyncio
from re import X

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

class ControllerData:
    def __init__(self):
        self.X = 0.
        self.Y = 0.
        self.beta = 0.
        self.alpha_old = 0.
class UserData:
    def __init__(self):
        self.controllers = {}
        self.max_user_count = 0


def toVJoy(message: str,local_id,controllers):
    data = message.split(sep="_")
    data = list(map(lambda x: float(x), data))
    # print(data)
    controllers[local_id].X = max(0.0, min(1.0, 1.2 * data[0]))
    controllers[local_id].Y = max(0.0, min(1.0, 1.2 * data[1]))

    dir = R.from_euler("ZXY", np.array(data[2:5]), True).as_matrix()[2, [0, 1]]

    alpha = np.arccos(dir[1])
    alpha *= 1 if dir[0] < 0 else -1
    alpha += np.pi / 2
    alpha = alpha if alpha < np.pi else alpha - 2 * np.pi

    da = alpha - controllers[local_id].alpha_old
    if np.abs(da) > np.abs(da + 2 * np.pi):
        da = da + 2 * np.pi
    elif np.abs(da) > np.abs(da - 2 * np.pi):
        da = da - 2 * np.pi

    controllers[local_id].beta += da
    controllers[local_id].alpha_old = alpha

    sum_beta = 0
    sum_X = 0
    sum_Y = 0
    sum = 0
    for key in controllers.keys():
        sum_beta += controllers[key].beta
        sum_X += controllers[key].X
        sum_Y += controllers[key].Y
        sum+=1

    x = min(1,max(0,sum_X/sum))
    y = min(1,max(0,sum_Y/sum))
    z = (sum_beta / (2 * np.pi)) + 0.5
    z = min(1,max(0,z))

    j.data.wAxisX = int(x * 0x8000)
    j.data.wAxisY = int(y * 0x8000)
    j.data.wAxisZ = int(z * 0x8000)
    j.update()


async def reply(websocket, user_data):
    print("connection opened",websocket.id)
    user_data.controllers[websocket.id] = ControllerData()
    user_data.max_user_count += 1
    while True:
        try:
            message = await websocket.recv()
        except:
            print("connection closed")
            user_data.controllers.pop(websocket.id)
            user_data.max_user_count -= 1
            break
        toVJoy(message,websocket.id, user_data.controllers)


async def main():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile="./cert.pem", keyfile="./cert.pem")
    user_data = UserData()
    async with websockets.serve(lambda ws: reply(ws, user_data=user_data), hostName, serverPort, ssl=ssl_context):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    print("start")
    asyncio.run(main())
