"""rename usuarios table and columns to english names

Revision ID: 003_rename_schema_to_english
Revises: 002_add_usuario_table
Create Date: 2026-09-16 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = '003_rename_schema_to_english'
down_revision: Union[str, None] = '002_add_usuario_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# old column name -> new column name (reversed for the downgrade)
USER_COLUMN_RENAMES = {
    "nome": "first_name",
    "sobrenome": "last_name",
    "endereco": "address",
}

HOST_COLUMN_RENAMES = {
    "fabricante": "manufacturer",
    "modelo": "model",
    "qtdCpu": "cpu_count",
    "disco": "disk",
    "tipo": "storage_type",
    "localizacao": "location",
}


def _rename_columns(table_name: str, renames: dict) -> None:
    """Renames columns in place, preserving every existing row."""
    for old_name, new_name in renames.items():
        op.alter_column(table_name, old_name, new_column_name=new_name)


def upgrade() -> None:
    # 1. Renames the 'usuarios' table to 'users'
    op.rename_table("usuarios", "users")

    # 2. Renames the user columns to english names
    _rename_columns("users", USER_COLUMN_RENAMES)

    # 3. Renames the host columns to english names
    _rename_columns("hosts", HOST_COLUMN_RENAMES)

    # 4. Recreates the indexes so their names match the new table name
    op.drop_index("ix_usuarios_id", table_name="users")
    op.drop_index("ix_usuarios_username", table_name="users")
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)


def downgrade() -> None:
    # Reverses every step of upgrade() in the opposite order
    _rename_columns("users", {new: old for old, new in USER_COLUMN_RENAMES.items()})
    _rename_columns("hosts", {new: old for old, new in HOST_COLUMN_RENAMES.items()})

    op.drop_index("ix_users_id", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.rename_table("users", "usuarios")
    op.create_index(op.f("ix_usuarios_id"), "usuarios", ["id"], unique=False)
    op.create_index(op.f("ix_usuarios_username"), "usuarios", ["username"], unique=True)
