import uvicorn

from fastapi import FastAPI
from fastapi_socketio import SocketManager

from chats.routers import chats_router
from chats.routers import messages_router

from chats.shared.exceptions_handler import not_found_exception_handler, conflict_exception_handler
from chats.shared.exceptions import NotFound, Conflict

app = FastAPI()

socket_manager = SocketManager(app=app, cors_allowed_origins="*")

app.include_router(chats_router.router)
app.include_router(messages_router.router)

app.add_exception_handler(NotFound, not_found_exception_handler)
app.add_exception_handler(Conflict, conflict_exception_handler)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)