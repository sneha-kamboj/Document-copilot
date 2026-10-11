import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class ChatThread(Base):
    __tablename__ = "chat_threads"


    id = Column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )


    user_id = Column(
        Uuid,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )


    title = Column(
        String(255),
        nullable=False,
        default="New Chat",
    )


    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


    user = relationship(
        "User",
        back_populates="chat_threads",
    )

    messages = relationship(
        "ChatMessage",
        back_populates="thread",
        cascade="all, delete-orphan",
    )
