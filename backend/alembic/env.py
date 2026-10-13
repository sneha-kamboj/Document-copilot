from sqlalchemy import create_engine, pool

import app.database.models  # noqa: F401  (registers all tables)
from alembic import context
from app.config import settings
from app.database.base import Base

config = context.config
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    context.configure(url=settings.sqlalchemy_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()