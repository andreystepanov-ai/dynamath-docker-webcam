import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .core.simulator import DynamathSimulator

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

sim = DynamathSimulator()

@app.get("/")
async def index():
    return FileResponse("app/static/index.html")

@app.websocket("/ws")
async def ws(ws: WebSocket):
    await ws.accept()
    sending = True

    async def sender():
        try:
            while sending:
                drift, entropy = sim.step()
                snap = sim.snapshot()
                snap["drift"] = drift
                snap["entropy"] = entropy
                await ws.send_text(json.dumps(snap))
                await asyncio.sleep(0.033)  # ~30 fps
        except WebSocketDisconnect:
            pass
        except Exception:
            pass

    send_task = asyncio.create_task(sender())
    try:
        while True:
            msg = await ws.receive_text()
            data = json.loads(msg)
            t = data.get("type")
            if t == "control":
                sim.set_params(data.get("payload", {}))
            elif t == "reset":
                # reinit simulator quickly (preserve params)
                params = sim.params
                n = sim.E.shape[0]
                sim.__init__(n=n, seed=0)
                sim.params = params
            elif t == "sensor":
                sim.set_sensor(data.get("payload", {}))
    except WebSocketDisconnect:
        pass
    finally:
        sending = False
        send_task.cancel()
        try:
            await send_task
        except Exception:
            pass
