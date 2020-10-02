"""Local fetch attempts column

Revision ID: 4c8331188a48
Revises: 47d2fbfacf1b
Create Date: 2020-10-02 19:40:24.882891

"""

# revision identifiers, used by Alembic.
revision = '4c8331188a48'
down_revision = '47d2fbfacf1b'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

from sqlalchemy_utils.types import TSVectorType
from sqlalchemy_searchable import make_searchable
import sqlalchemy_utils

# Patch in knowledge of the citext type, so it reflects properly.
from sqlalchemy.dialects.postgresql.base import ischema_names
import citext
import queue
import datetime
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import TSVECTOR
ischema_names['citext'] = citext.CIText



def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    print("Adding column")
    op.add_column('nu_release_item', sa.Column('local_fetch_attempts', sa.Integer(), nullable=True))

    print("Setting default values....")

    op.execute("SET statement_timeout TO 14400000;")
    op.execute("UPDATE nu_release_item SET local_fetch_attempts = 0;")

    print("Adding nullable constraint")
    op.alter_column('nu_release_item', 'local_fetch_attempts',
               existing_type=sa.Integer(),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('nu_release_item', 'local_fetch_attempts')
    # ### end Alembic commands ###
