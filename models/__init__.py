from chats.models.chats import Chat
from chats.models.messages import Message
from matches.models.matches import Match
from comments.models.comments import Comment

from sqlalchemy.orm import configure_mappers
configure_mappers()