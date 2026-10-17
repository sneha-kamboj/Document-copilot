import uuid
from datetime import datetime

from sqlalchemy import (
  Column,
  Integer,
  Text,
  String,
  DateTime,
  ForeignKey,
  Uuid,
  UniqueConstraint,
  func,
)
from sqlalchemy.orm import relationship
from app.database.base import Base

class MessageCitation(Base):
	__tablename__ = 'message_citations'


	id = Column( Uuid,
				 primary_key = True,
				 default=uuid.uuid4),

	message_id = Column( Uuid,
				ForeignKey("chat_messages.id"),
				nullable=False,
				index=True,
						  )
	chunk_id = Column(
		Uuid,
		ForeignKey("document_chunks.id"),
		nullable=False,
		index=True,
	)
	page_number = Column(
		Integer,
		nullable=False,
	)


	quote_text = Column(
		Text,
		nullable=True,
	)


	created_at = Column(
		DateTime(timezone=True),
		nullable=False,
		server_default=func.now(),
	)
	message = relationship(
		"ChatMessage",
		back_populates="citations",
	)
	chunk = relationship(
		"DocumentChunk",
	)

