
from sqlalchemy import Column, String, DateTime, ForeignKey,Text,Uuid,Index,func
from sqlalchemy.orm import relationship,Mapped,mapped_column,DeclarativeBase

from app.database.base import Base

class SourceDocument(Base):
	__tablename__ = 'source_documents'
	id =  Column(Uuid, primary_key=True, default=uuid.uuid4)
	owner_id = Column(Uuid, ForeignKey('user.id'),nullable=False)
	owner = relationship("User", back_populates="documents")
	filename=Column(String(255),nullable=False)
	storage_path = Column(Text, nullable=False)
	file_hash = Column(String(255), nullable=False,default="pending")
	status = Column(String(29), nullable=False,dafalut = "pending")
	created_at = Column(
		DateTime(timezone=True),
		nullable=False,
	    default = func.now()
	)
	updated_at = Column(  DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

	__table_args__ = (
		Index(
			"ix_source_documents_owner_file_hash",
            "owner_id",
            "file_hash",
            unique=True,
		),
	)

