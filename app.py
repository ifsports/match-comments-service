from fastapi import FastAPI
import socketio

app = FastAPI()

socket_manager = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    logger=True,
    engineio_logger=True
)