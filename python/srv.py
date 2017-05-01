import asyncio
import websockets

async def myshell(websocket,path):
    cmd = await websocket.recv()
    print(">>> {}".format(cmd))
    try:
        res=eval(cmd)
        print("{}".format())
    except:
        print("error")
        res="error"
    await websocket.send(res)

start_server =websockets.serve(myshell,'localhost',8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
