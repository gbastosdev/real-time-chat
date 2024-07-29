from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Real-time Chat</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.3/css/bootstrap.min.css" integrity="sha512-jnSuA4Ss2PkkikSOLtYs8BlYIeeIK1h99ty4YfvRPAlzr377vr3CXDb7sb7eEEBYjDtcYj+AjBH3FLv5uSJuXg==" crossorigin="anonymous" referrerpolicy="no-referrer" />
    </head>
    <body>
        <div class="container mt-3">
            <h1> WebSocket Chat </h1>
            <h2> Your connection ID: <span id="ws-id"></span></h2>
            <form action="" onsubmit="sendMessage(event)">
                <input type="text" class="form-control" id="messageText" autocomplete="off"/>
                <button class="btn btn-outline-primary mt-2">Send</button>
            </form>
            <ul id="messages" class="mt-5">
            </ul>
        </div>

        <script type="text/javascript">
                var client_id = randomInt()
                document.querySelector("#ws-id").textContent = client_id;
                var ws = new WebSocket("ws://localhost:8000/ws/"+ client_id)
    
                ws.onmessage = function(data){
                    var messages = document.getElementById('messages')
                    var message = document.createElement('li')
                    var content = document.createTextNode(event.data)
                    message.appendChild(content)
                    messages.appendChild(message)
                };

                function sendMessage(event){
                    var input = document.getElementById("messageText")
                    ws.send(input.value)
                    input.value = ''
                    event.preventDefault()
                }

                function randomInt(){
                    return Math.floor(Math.random()*(200 - 100 + 1)) + 100
                }
        </script>
    </body>
</html>
"""

class ConnManager:
    def __init__(self):
        self.active_conn: list[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_conn.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_conn.remove(websocket)
    
    async def broadcast(self, message:str):
        for connections in self.active_conn:
            await connections.send_text(message)

manager = ConnManager()

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    for n in websocket:
        print(n)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Client #{client_id} said: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} has disconnected!")