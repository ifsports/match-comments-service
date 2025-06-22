import uvicorn
import socketio
import models
from app import app, socket_manager

from fastapi.middleware.cors import CORSMiddleware

from chats.routers import chats_router, messages_router
from comments.routers import comments_router

from shared.exceptions_handler import not_found_exception_handler, conflict_exception_handler
from shared.exceptions import NotFound, Conflict

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@socket_manager.on('connect')
async def connect(sid, environ):
    print(f"Cliente conectado: {sid}")
    await socket_manager.emit('connection_status', {'status': 'connected', 'sid': sid}, room=sid)

@socket_manager.on('disconnect')
async def disconnect(sid):
    print(f"Cliente desconectado: {sid}")

@socket_manager.on('join_chat')
async def handle_join_chat(sid, data):
    """
    Evento para entrar em uma room de chat específica
    data = {'match_id': 'uuid-do-match'}
    """
    match_id = str(data.get('match_id'))
    user_id = data.get('user_id')

    await socket_manager.enter_room(sid, match_id)
    print(f"Cliente {sid} (user: {user_id}) entrou no chat {match_id}")

    # Notificar outros usuários na room
    await socket_manager.emit('user_joined', {
        'user_id': user_id,
        'message': f'Usuário {user_id} entrou no chat'
    }, room=match_id, skip_sid=sid)

@socket_manager.on('ping')
async def handle_ping(sid, data):
    """
    Evento para testar conectividade
    """
    await socket_manager.emit('pong', {'timestamp': data.get('timestamp')}, room=sid)

app.include_router(chats_router.router)
app.include_router(messages_router.router)
app.include_router(comments_router.router)

app.add_exception_handler(NotFound, not_found_exception_handler)
app.add_exception_handler(Conflict, conflict_exception_handler)

app.mount("/socket.io", socketio.ASGIApp(socket_manager, socketio_path=""))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)