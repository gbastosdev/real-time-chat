from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi import Depends,status # Assuming you have the FastAPI class for routing
from fastapi.responses import RedirectResponse,HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi_login import LoginManager #Loginmanager Class
from fastapi_login.exceptions import InvalidCredentialsException #Exception class
import os
from connmanager import ConnManager

pth = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(pth, "templates"))

SECRET = os.urandom(24).hex()
# To obtain a suitable secret key you can run | import os; print(os.urandom(24).hex())

manager = LoginManager(SECRET,token_url="/auth/login",use_cookie=True)
manager.cookie_name = "some-name"

app = FastAPI()

connected_users = {}
conn_manager = ConnManager()

DB = {"biel":{"password":"qwertyuiop"}, "testing":{"password":"qwertyuiop"}} # unhashed

@manager.user_loader()
def load_user(username:str):
    user = DB.get(username)
    return user

@app.post("/auth/login")
def login(data: OAuth2PasswordRequestForm = Depends()):
    username = data.username
    password = data.password
    user = load_user(username)
    if not user:
        raise InvalidCredentialsException
    elif password != user['password']:
        raise InvalidCredentialsException

    access_token = manager.create_access_token(
        data={"sub":username}
    )
    resp = RedirectResponse(url="/main",status_code=status.HTTP_302_FOUND)
    manager.set_cookie(resp,access_token)
    return resp

@app.get("/main")
def getPrivateendpoint(_=Depends(manager)):
    with open(os.path.join(pth, "templates/main.html")) as f:
        return HTMLResponse(content=f.read())

@app.get("/",response_class=HTMLResponse)
def loginwithCreds(request:Request):
    with open(os.path.join(pth, "templates/login.html")) as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await conn_manager.connect(websocket)
    connected_users[client_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            for user, _ in connected_users.items():
                if user != client_id:
                    await conn_manager.broadcast(user,data)
    except WebSocketDisconnect:
        conn_manager.disconnect(websocket)
        for user, _ in connected_users.items():
                if user != client_id:
                    await conn_manager.broadcast("Client #{client_id} has disconnected!")