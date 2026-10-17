from sqlalchemy import Column, String, DateTime, ForeignKey,Integer,Text,Uuid,Index,UniqueConstraint,func
from sqlalchemy.orm import relationship,Mapped,mapped_column,DeclarativeBase

from app.database.base import Base

class DocumentChunk(Base):
	__tablename__ = 'document_chunks'

	id = Column( Uuid,
				 primary_key = True,
				 default=Uuid),

	document_id = Column( Uuid,
				ForeignKey("source_documents.id",ondelete="CASCADE"),
				nullable=False,
				index=True,
						  )

	chunk_index = Column(
		 Integer,
		nullable= False,

	),
	content = Column( Text,
					  nullable= False,
					  ),
	page_number = Column(
		Integer,
	    nullable= False,
	),



	created_at = Column(
		DateTime(timezone=True),
		nullable=False,
	    server_default = func.now()
	)
	updated_at = Column(  DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

	__table_args__ = (
		UniqueConstraint(
			"document_id",
			"chunk_index",
			name="uq_document_chunk_index"
		),
	)

