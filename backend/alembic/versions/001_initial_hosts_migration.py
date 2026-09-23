"""create hosts table

Revision ID: 001_initial_hosts_migration
Revises: 
Create Date: 2026-09-03 21:12:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_hosts_migration'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'hosts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('hostname', sa.String(), nullable=False),
        sa.Column('fabricante', sa.String(), nullable=False),
        sa.Column('modelo', sa.String(), nullable=False),
        sa.Column('cpu', sa.String(), nullable=False),
        sa.Column('qtdCpu', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('ram', sa.String(), nullable=False),
        sa.Column('disco', sa.String(), nullable=False),
        sa.Column('tipo', sa.String(), nullable=False),
        sa.Column('interfaces', sa.String(), nullable=False),
        sa.Column('ips', sa.String(), nullable=False),
        sa.Column('localizacao', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_hosts_id'), 'hosts', ['id'], unique=False)
    op.create_index(op.f('ix_hosts_hostname'), 'hosts', ['hostname'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_hosts_hostname'), table_name='hosts')
    op.drop_index(op.f('ix_hosts_id'), table_name='hosts')
    op.drop_table('hosts')
