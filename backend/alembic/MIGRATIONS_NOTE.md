# Database Migrations Setup

## Manual Setup Required

The `versions/` directory needs to be created for Alembic migrations.

### Steps:

1. Create the versions directory:
```bash
cd backend
mkdir -p alembic/versions
```

2. Initialize alembic (if not already done):
```bash
cd backend
alembic init alembic
```

3. Create migration files:

**File: `backend/alembic/versions/001_base.py`**
```python
"""Base migration - users and refresh_tokens tables.

Revision ID: 001
Revises: 
Create Date: 2026-02-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

revision: str = '001'
down_revision: Union[str, None] = None

def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])
    
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
        sa.Column('revoked', sa.Boolean(), default=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    op.create_index('ix_refresh_tokens_id', 'refresh_tokens', ['id'])
    op.create_index('ix_refresh_tokens_token', 'refresh_tokens', ['token'])

def downgrade() -> None:
    op.drop_index('ix_refresh_tokens_token', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_id', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_table('users')
```

**File: `backend/alembic/versions/002_sessions.py`**
```python
"""Add conversation_sessions table for long-session mode.

Revision ID: 002
Revises: 001
Create Date: 2026-02-16 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

revision: str = '002'
down_revision: Union[str, None] = '001'

def upgrade() -> None:
    op.create_table(
        'conversation_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('context_data', sa.Text(), nullable=True),
        sa.Column('capacity_used', sa.Integer(), default=0),
        sa.Column('capacity_max', sa.Integer(), default=100000),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_conversation_sessions_id', 'conversation_sessions', ['id'])
    op.create_index('ix_conversation_sessions_user_id', 'conversation_sessions', ['user_id'])
    op.create_index('ix_conversation_sessions_is_active', 'conversation_sessions', ['is_active'])

def downgrade() -> None:
    op.drop_index('ix_conversation_sessions_is_active', table_name='conversation_sessions')
    op.drop_index('ix_conversation_sessions_user_id', table_name='conversation_sessions')
    op.drop_index('ix_conversation_sessions_id', table_name='conversation_sessions')
    op.drop_table('conversation_sessions')
```

4. Run migrations:
```bash
cd backend
alembic upgrade head
```

## Advisory Locking

The `env.py` has been configured with advisory locking to prevent concurrent migrations:
- PostgreSQL: Uses `pg_advisory_lock()`
- MySQL: Uses `GET_LOCK()`
- SQLite: No locking (single writer)
