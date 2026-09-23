"""add usuario table and fk in hosts

Revision ID: 002_add_usuario_table
Revises: 001_initial_hosts_migration
Create Date: 2026-09-03 21:48:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_add_usuario_table'
down_revision: Union[str, None] = '001_initial_hosts_migration'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Creates the 'usuarios' table
    op.create_table(
        'usuarios',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nome', sa.String(), nullable=False),
        sa.Column('sobrenome', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('endereco', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usuarios_id'), 'usuarios', ['id'], unique=False)
    op.create_index(op.f('ix_usuarios_username'), 'usuarios', ['username'], unique=True)

    # 2. Adds the 'user_id' column and the Foreign Key to the 'hosts' table
    op.add_column('hosts', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_hosts_user_id',
        source_table='hosts',
        referent_table='usuarios',
        local_cols=['user_id'],
        remote_cols=['id'],
        ondelete='CASCADE'
    )

def downgrade() -> None:
    op.drop_constraint('fk_hosts_user_id', 'hosts', type_='foreignkey')
    op.drop_column('hosts', 'user_id')
    op.drop_index(op.f('ix_usuarios_username'), table_name='usuarios')
    op.drop_index(op.f('ix_usuarios_id'), table_name='usuarios')
    op.drop_table('usuarios')
