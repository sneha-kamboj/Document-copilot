import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001_intial_schema"
down_revision =None
branch_labels = None

depend_on = None


def upgrade() -> None:
    op.create_table(
	"users",
	sa.Column(
		  "id",
		  postgresql.UUID(as_uuid=True),
		  primary_key=True,
		  server_default=sa.text("gen_random_uuid()"),
	  ),
	),
    sa.Column(
			  "emails",
			  sa.String(255),
			  nullable=False,
			  unique=True,
	),
    sa.Column(

	   "password",
		  sa.String(255),
		  nullable=False,

	),
    sa.Column(
		"created_at",
		sa.DateTime(timezone=True),
		nullable=False,
		server_default=sa.func.now(),
	),
    sa.Column(
		"updated_at",
		sa.DateTime(timezone=True),
	)


    op.create_table(
		"source_documents",
	sa.Column(
		"id",
		postgresql.UUID(as_uuid=True),
		primary_key=True,
		server_default=sa.text("gen_random_uuid()"),

		),

		sa.Column(
			"owner_id",
			postgresql.UUID(as_uuid=True),
			sa.ForeignKey("users.id", ondelete="CASCADE"),
			nullable=False,
		),
		sa.Column(
			"filename",
			sa.String(255),
			nullable=False,
		),
		sa.Column(
			"storage_path",
			sa.Text(),
			nullable=False,
		),
		sa.Column("file_hash", sa.String(64), nullable=False),
		sa.Column(
			"status",
			sa.String(30),
			nullable=False,
			server_default="pending",
		),
		sa.Column(
			"created_at",
			sa.DateTime(timezone=True),
			nullable=False,
			server_default=sa.func.now(),
		),
		sa.Column(
			"updated_at",
			sa.DateTime(timezone=True),
			nullable=False,
			server_default=sa.func.now(),
		),


		sa.UniqueConstraint(
			"owner_id",
			"file_hash",
			name="uq_source_documents_owner_file_hash",
		),
	)
    op.create_table(
		"document_chunks",
		sa.Column(
			"id",
			postgresql.UUID(as_uuid=True),
			primary_key=True,
			server_default=sa.text("gen_random_uuid()"),
		),
		sa.Column(
			"document_id",
			postgresql.UUID(as_uuid=True),
			sa.ForeignKey(
				"source_documents.id",
				ondelete="CASCADE",
			),
			nullable=False,
		),
		sa.Column("chunk_index", sa.Integer(), nullable=False),
		sa.Column("page_number", sa.Integer(), nullable=True),
		sa.Column("content", sa.Text(), nullable=False),

		sa.UniqueConstraint(
			"document_id",
			"chunk_index",
			name="uq_document_chunks_document_index",
		),
		sa.CheckConstraint(
			"chunk_index >= 0",
			name="ck_document_chunks_index_nonnegative",
		),
		sa.CheckConstraint(
			"page_number IS NULL OR page_number > 0",
			name="ck_document_chunks_page_positive",
		),
	)

    op.create_table(
		"chat_threads",
		sa.Column(
			"id",
			postgresql.UUID(as_uuid=True),
			primary_key=True,
			server_default=sa.text("gen_random_uuid()"),
		),
		sa.Column(
			"owner_id",
			postgresql.UUID(as_uuid=True),
			sa.ForeignKey("users.id", ondelete="CASCADE"),
			nullable=False,
		),
		sa.Column("title", sa.String(255), nullable=True),
		sa.Column(
			"created_at",
			sa.DateTime(timezone=True),
			nullable=False,
			server_default=sa.func.now(),
		),
		sa.Column(
			"updated_at",
			sa.DateTime(timezone=True),
			nullable=False,
			server_default=sa.func.now(),
		),
	)

    op.create_table(
		"chat_messages",
		sa.Column(
			"id",
			postgresql.UUID(as_uuid=True),
			primary_key=True,
			server_default=sa.text("gen_random_uuid()"),
		),
		sa.Column(
			"thread_id",
			postgresql.UUID(as_uuid=True),
			sa.ForeignKey("chat_threads.id", ondelete="CASCADE"),
			nullable=False,
		),
		sa.Column("role", sa.String(20), nullable=False),
		sa.Column("content", sa.Text(), nullable=False),
		sa.Column(
			"created_at",
			sa.DateTime(timezone=True),
			nullable=False,
			server_default=sa.func.now(),
		),
		sa.CheckConstraint(
			"role IN ('user', 'assistant', 'system')",
			name="ck_chat_messages_valid_role",
		),
	)
    op.create_table(
		"message_citations",
		sa.Column(
			"id",
			postgresql.UUID(as_uuid=True),
			primary_key=True,
			server_default=sa.text("gen_random_uuid()"),
		),
		sa.Column(
			"message_id",
			postgresql.UUID(as_uuid=True),
			sa.ForeignKey("chat_messages.id", ondelete="CASCADE"),
			nullable=False,
		),
		sa.Column(
			"chunk_id",
			postgresql.UUID(as_uuid=True),
			sa.ForeignKey("document_chunks.id", ondelete="CASCADE"),
			nullable=False,
		),
		sa.Column("citation_order", sa.Integer(), nullable=False),
		sa.Column("quote", sa.Text(), nullable=True),


		sa.UniqueConstraint(
			"message_id",
			"chunk_id",
			name="uq_message_citations_message_chunk",
		),
		sa.CheckConstraint(
			"citation_order >= 0",
			name="ck_message_citations_order_nonnegative",
		),
	)


    op.create_index(
        "ix_source_documents_owner_id",
        "source_documents",
        ["owner_id"],
    )

    op.create_index(
        "ix_document_chunks_document_id",
        "document_chunks",
        ["document_id"],
    )

    op.create_index(
        "ix_chat_threads_owner_id",
        "chat_threads",
        ["owner_id"],
    )

    op.create_index(
        "ix_chat_messages_thread_id",
        "chat_messages",
        ["thread_id"],
    )

    op.create_index(
        "ix_message_citations_message_id",
        "message_citations",
        ["message_id"],
    )


def downgrade() -> None:

    op.drop_table("message_citations")
    op.drop_table("chat_messages")
    op.drop_table("chat_threads")
    op.drop_table("document_chunks")
    op.drop_table("source_documents")
    op.drop_table("users")


