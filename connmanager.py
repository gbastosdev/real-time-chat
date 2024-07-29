from fastapi import WebSocket
class ConnManager:
    def __init__(self):
        self.active_conn: list[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_conn.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_conn.remove(websocket)
    
    async def broadcast(self, message:str, user: int):
        for connections in self.active_conn:
            await connections.send_text(f'{user}: {message}')