import uvicorn

from fastapi import FastAPI
from fastapi_socketio import SocketManager

app = FastAPI()

socket_manager = SocketManager(app=app, cors_allowed_origins="*")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)