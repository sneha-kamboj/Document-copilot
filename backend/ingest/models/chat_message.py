
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(
				 Uuid,
				 primary_key = True,
				 default=uuid.uuid4,
				 )
    thread_id = Column(
		        Uuid,
				ForeignKey("chat_thread.id",ondelete="CASCADE"),
				nullable=False,
				index=True,
					)
    role = Column(
		String(20),
		nullable=False,
	)

    content= Column(Text,
					nullable=False,
					)

    created_at = Column(
			DateTime(timezone=True),
			nullable=False,
			server_default=func.now(),
		)
    citations = relationship(
		"MessageCitation",
		back_populates="message",
		cascade="all, delete-orphan",
	)