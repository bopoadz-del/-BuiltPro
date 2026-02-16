"""Alembic environment configuration with advisory locking."""

from logging.config import fileConfig
import os
import sys
import time
import hashlib

from alembic import context
from sqlalchemy import engine_from_config, pool, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.database import Base  # noqa: E402

config = context.config
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL", "sqlite:///./app.db"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Advisory lock key (unique per database)
LOCK_KEY = 123456789


def _acquire_advisory_lock(connection):
    """Acquire advisory lock to prevent concurrent migrations."""
    db_url = os.getenv("DATABASE_URL", "")
    
    if "postgresql" in db_url.lower():
        # PostgreSQL advisory lock
        connection.execute(text(f"SELECT pg_advisory_lock({LOCK_KEY})"))
        return True
    elif "mysql" in db_url.lower():
        # MySQL GET_LOCK
        connection.execute(text(f"SELECT GET_LOCK('alembic_migration_{LOCK_KEY}', 30)"))
        return True
    # SQLite doesn't support advisory locks, use file-based or skip
    return False


def _release_advisory_lock(connection):
    """Release advisory lock."""
    db_url = os.getenv("DATABASE_URL", "")
    
    if "postgresql" in db_url.lower():
        connection.execute(text(f"SELECT pg_advisory_unlock({LOCK_KEY})"))
    elif "mysql" in db_url.lower():
        connection.execute(text(f"SELECT RELEASE_LOCK('alembic_migration_{LOCK_KEY}')"))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with advisory locking."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        # Acquire advisory lock
        lock_acquired = False
        retries = 5
        
        while retries > 0 and not lock_acquired:
            try:
                lock_acquired = _acquire_advisory_lock(connection)
                if not lock_acquired:
                    print("Could not acquire advisory lock, retrying...")
                    time.sleep(1)
                    retries -= 1
            except Exception as e:
                print(f"Lock acquisition error: {e}")
                time.sleep(1)
                retries -= 1
        
        try:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
        finally:
            if lock_acquired:
                try:
                    _release_advisory_lock(connection)
                except Exception as e:
                    print(f"Lock release error: {e}")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
