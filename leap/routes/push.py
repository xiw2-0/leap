import json
import logging
import fastapi
import typing

from leap.config import settings
from leap.services import trade_push_service, quote_push_service


router = fastapi.APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/push")
async def push(websocket: fastapi.WebSocket):
    await websocket.accept()
    logger.info(f"WebSocket connection established with {websocket.client}")

    trade_push_svc = trade_push_service.TradePushService()  # singleton
    # Get the quote push service from app state
    quote_push_svc: quote_push_service.QuotePushService = websocket.state.quote_push_service

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError as e:
                error_response: dict[str, typing.Any] = {
                    "error_code": -1,
                    "error_message": f"Invalid JSON format: {str(e)}"
                }
                await websocket.send_text(json.dumps(error_response))
                logger.error(
                    f"Failed to decode JSON from {websocket.client}: {e}")
                continue

            # Extract action, topic, and stock_codes from the message
            action = message.get("action")
            topic = message.get("topic")
            stock_codes = message.get("stock_codes", [])

            # Initialize response
            response: dict[str, typing.Any] = {
                "error_code": 0, "error_message": "", "subscribed_codes": []}

            # Process the action
            if action == "subscribe":
                if topic == "trade":
                    # Subscribe to the specific topic
                    trade_push_svc.subscribe_to_trade(websocket)
                    logger.info(
                        f"Client {websocket.client} subscribed to {topic}")
                elif topic == "quote":
                    # Subscribe to the specific topic with stock codes
                    subscribed_codes = quote_push_svc.subscribe_to_quotes(
                        websocket, stock_codes)
                    response["subscribed_codes"] = subscribed_codes
                else:
                    response = {
                        "error_code": -1,
                        "error_message": f"Invalid topic: {topic}. Supported topics are 'trade' and 'quote'",
                        "subscribed_codes": []
                    }
            elif action == "unsubscribe":
                if topic == "trade" or topic == "all":
                    # Unsubscribe from the specific topic
                    trade_push_svc.unsubscribe_from_trade(websocket)
                    logger.info(
                        f"Client {websocket.client} unsubscribed from {topic}.")
                if topic == "quote" or topic == "all":
                    # Unsubscribe from the specific topic with stock codes
                    quote_push_svc.unsubscribe_from_quotes(
                        websocket, stock_codes)
                    logger.info(
                        f"Client {websocket.client} unsubscribed from {topic} with stock_codes {stock_codes}")
            else:
                # Invalid action
                response = {
                    "error_code": -1,
                    "error_message": f"Invalid action: {action}. Supported actions are 'subscribe' and 'unsubscribe'",
                    "subscribed_codes": []
                }

            # Send response back to client
            await websocket.send_text(json.dumps(response))

    except fastapi.WebSocketDisconnect as e:
        logger.warning(f"WebSocket disconnected from {websocket.client}: {e}")

    finally:
        # Cleanup: unsubscribe all for this WebSocket connection when client disconnects
        trade_push_svc.unsubscribe_from_trade(websocket)
        quote_push_svc.unsubscribe_from_quotes(websocket, [])
        logger.info(
            f"Cleaned up subscriptions for {websocket.client} after disconnection")


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>WebSocket debug</title>
    </head>
    <body>
        <h1>WebSocket Messages</h1>
        <button onclick="subscribeTrade()">Subscribe to Trade</button>
        <button onclick="subscribeQuote()">Subscribe to Quote</button>
        <button onclick="unsubscribeTrade()">Unsubscribe from Trade</button>
        <button onclick="unsubscribeQuote()">Unsubscribe from Quote</button>
        <button onclick="unsubscribeAll()">Unsubscribe All</button>
        <br><br>
        <input type="text" id="stockCodeInput" placeholder="Enter stock code (e.g., 000001.SZ)" />
        <button onclick="addStockCode()">Add Stock Code</button>
        <div>
            Selected stock codes: <span id="selectedStockCodes">None</span>
        </div>
        <br>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://%s:%s/ws/push");
            var selectedStockCodes = [];
            
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages');
                var message = document.createElement('li');
                var content = document.createTextNode(event.data);
                message.appendChild(content);
                messages.appendChild(message);
            };
            
            ws.onclose = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode("Connection closed")
                message.appendChild(content)
                messages.appendChild(message)
            };
            
            function subscribeTrade() {
                var message = {
                    "action": "subscribe",
                    "topic": "trade",
                    "stock_codes": []
                };
                ws.send(JSON.stringify(message));
            }
            
            function subscribeQuote() {
                var message = {
                    "action": "subscribe",
                    "topic": "quote",
                    "stock_codes": selectedStockCodes
                };
                ws.send(JSON.stringify(message));
            }
            
            function unsubscribeTrade() {
                var message = {
                    "action": "unsubscribe",
                    "topic": "trade",
                    "stock_codes": []
                };
                ws.send(JSON.stringify(message));
            }
            
            function unsubscribeQuote() {
                var message = {
                    "action": "unsubscribe",
                    "topic": "quote",
                    "stock_codes": selectedStockCodes
                };
                ws.send(JSON.stringify(message));
            }
            
            function unsubscribeAll() {
                var message = {
                    "action": "unsubscribe",
                    "topic": "all",
                    "stock_codes": []
                };
                ws.send(JSON.stringify(message));
            }
            
            function addStockCode() {
                var input = document.getElementById('stockCodeInput');
                var code = input.value.trim();
                if (code) {
                    if (!selectedStockCodes.includes(code)) {
                        selectedStockCodes.push(code);
                        updateSelectedStockCodesDisplay();
                    }
                    input.value = '';
                }
            }
            
            function updateSelectedStockCodesDisplay() {
                var display = document.getElementById('selectedStockCodes');
                if (selectedStockCodes.length > 0) {
                    display.textContent = selectedStockCodes.join(', ');
                } else {
                    display.textContent = 'None';
                }
            }
            
            // Allow adding stock codes with Enter key
            document.getElementById('stockCodeInput').addEventListener('keypress', function(event) {
                if (event.key === 'Enter') {
                    addStockCode();
                }
            });
        </script>
    </body>
</html>
""" % (settings.HOST, settings.PORT)


@router.get("/debug")
async def debug():
    return fastapi.responses.HTMLResponse(html)
