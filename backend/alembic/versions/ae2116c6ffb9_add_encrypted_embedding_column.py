"""add_encrypted_embedding_column

Revision ID: ae2116c6ffb9
Revises: 8d532af5baa7
Create Date: 2025-12-21 00:34:15.661277

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae2116c6ffb9'
down_revision: Union[str, None] = '8d532af5baa7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add encrypted_embedding column to document_chunks table
    op.add_column('document_chunks', sa.Column('encrypted_embedding', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove encrypted_embedding column from document_chunks table
    op.drop_column('document_chunks', 'encrypted_embedding')
