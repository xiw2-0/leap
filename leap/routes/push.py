import asyncio
import fastapi
import logging

from leap.config import settings
from leap.services import push_service


router = fastapi.APIRouter()


@router.websocket("/push")
async def trade_push(websocket: fastapi.WebSocket):
    await websocket.accept()

    push_svc = push_service.PushService()  # singleton
    push_svc.add_connection(websocket)

    while websocket.client_state == fastapi.websockets.WebSocketState.CONNECTED and websocket.application_state == fastapi.websockets.WebSocketState.CONNECTED:
        await asyncio.sleep(20)
    logging.debug(
        f"Websocket closed, application state: {websocket.application_state}, client state: {websocket.client_state}")

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>WebSocket debug</title>
    </head>
    <body>
        <h1>WebSocket Messages</h1>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://%s:%s/ws/push");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            ws.onclose = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode("Connection closed")
                message.appendChild(content)
                messages.appendChild(message)
            };
        </script>
    </body>
</html>
""" % (settings.HOST, settings.PORT)


@router.get("/debug")
async def debug():
    return fastapi.responses.HTMLResponse(html)
