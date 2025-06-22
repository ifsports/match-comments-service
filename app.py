import socketio
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager

from messaging.consumers import main_consumer

app = FastAPI()

socket_manager = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)