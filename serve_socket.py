import asyncio

# from concurrent.futures import process
import websockets
import pathlib
import pyvjoy
import ssl
import numpy as np
from scipy.spatial.transform import Rotation as R

# import matplotlib.pyplot as plt

# fig : plt.Figure = plt.figure(0)
# ax : plt.Axes = fig.add_subplot(111)
# h = ax.plot([[0,0,0],[0,0,0]],[[0,0,0],[0,0,0]])
# ax.set_ylim(-1,1)
# ax.set_xlim(-1,1)
# ax.set_aspect("equal")

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

    mat = R.from_euler("ZXY", np.array(data[2:5]), True).as_matrix()

    # h[0].set_data([0,mat[2,0]],[0,mat[2,1]])
    # plt.pause(1e-10)
    # print(np.arctan2(mat[2,1],mat[2,0]))

    alpha = np.arctan2(mat[2,1],mat[2,0])
    
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
    z = (sum_beta/sum / (2 * np.pi)) + 0.5
    z = min(1,max(0,z))

    j.data.wAxisX = int(x * 0x8000)
    j.data.wAxisY = int(y * 0x8000)
    j.data.wAxisZ = int(z * 0x8000)
    j.update()


async def reply(websocket, user_data):
    user_data.controllers[websocket.id] = ControllerData()
    user_data.max_user_count += 1
    print("connection opened",websocket.id, user_data.max_user_count)
    while True:
        try:
            message = await websocket.recv()
        except:
            user_data.controllers.pop(websocket.id)
            user_data.max_user_count -= 1
            print("connection closed",websocket.id,user_data.max_user_count)
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
