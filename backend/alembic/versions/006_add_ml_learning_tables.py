"""Add ML learning tables



Revision ID: 006

Revises: 005

Create Date: 2025-10-16



"""

from alembic import op

import sqlalchemy as sa

from sqlalchemy.dialects.sqlite import JSON



# revision identifiers, used by Alembic.

revision = '006'

down_revision = '005'

branch_labels = None

depends_on = None





def upgrade():
    # ML learning tables migration
    pass


def downgrade():
    # Downgrade migration
    pass