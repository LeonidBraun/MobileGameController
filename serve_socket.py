import asyncio

# from concurrent.futures import process
import websockets
import pathlib
import pyvjoy
import ssl
import numpy as np
from scipy.spatial.transform import Rotation as R

from typing import Dict

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

j = [pyvjoy.VJoyDevice(i+1) for i in range(4)]


class ControllerData:
    def __init__(self):
        self.player_id = None
        self.X = 0.
        self.Y = 0.
        self.beta = 0.
        self.alpha_old = 0.
class UserData:
    def __init__(self):
        self.controllers = {}
        self.max_user_count = 0


def toVJoy(message: str, local_id, controllers : Dict[str,ControllerData]):
    if (controllers[local_id].player_id== None):
        return
    data = message.split(sep=":")

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

    # sum_beta = 0
    # sum_X = 0
    # sum_Y = 0
    # sum = 0
    # for key in controllers.keys():
    #     sum_beta += controllers[key].beta
    #     sum_X += controllers[key].X
    #     sum_Y += controllers[key].Y
    #     sum+=1

    # x = min(1,max(0,sum_X/sum))
    # y = min(1,max(0,sum_Y/sum))
    # z = (sum_beta/sum / (2 * np.pi)) + 0.5
    # z = min(1,max(0,z))

    x = min(1,max(0,controllers[local_id].X))
    y = min(1,max(0,controllers[local_id].Y))
    z = (controllers[local_id].beta / (2 * np.pi)) + 0.5
    z = min(1,max(0,z))

    j_player = j[controllers[local_id].player_id]

    j_player.data.wAxisX = int(x * 0x8000)
    j_player.data.wAxisY = int(y * 0x8000)
    j_player.data.wAxisZ = int(z * 0x8000)
    j_player.update()


async def reply(websocket, user_data):
    user_data.controllers[websocket.id] = ControllerData()
    user_data.max_user_count += 1
    print("connection opened",websocket.id, user_data.max_user_count)
    while True:
        try:
            message : str = await websocket.recv()
        except:
            user_data.controllers.pop(websocket.id)
            user_data.max_user_count -= 1
            print("connection closed",websocket.id,user_data.max_user_count)
            break
        if message.count("PLAYER:") == 1:
            player_id : int = int(message.split(":")[1])
            user_data.controllers[websocket.id].player_id = (player_id - 1) % 4
            print("connection",websocket.id, "is player", player_id)
        else:
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
