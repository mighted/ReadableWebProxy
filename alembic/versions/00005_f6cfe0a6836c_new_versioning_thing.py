"""New versioning thing

Revision ID: f6cfe0a6836c
Revises: 09ec7dda0433
Create Date: 2016-02-05 19:57:26.713183

"""

# revision identifiers, used by Alembic.
revision = 'f6cfe0a6836c'
down_revision = '09ec7dda0433'
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
from sqlalchemy.dialects.postgresql import TSVECTOR
ischema_names['citext'] = citext.CIText

from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('transaction',
    sa.Column('issued_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('remote_addr', sa.String(length=50), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('web_pages_version',
    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('state', postgresql.ENUM('new', 'fetching', 'processing', 'complete', 'error', 'removed', name='dlstate_enum', create_type=False), autoincrement=False, nullable=True),
    sa.Column('errno', sa.Integer(), autoincrement=False, nullable=True),
    sa.Column('url', sa.Text(), autoincrement=False, nullable=True),
    sa.Column('starturl', sa.Text(), autoincrement=False, nullable=True),
    sa.Column('netloc', sa.Text(), autoincrement=False, nullable=True),
    sa.Column('file', sa.Integer(), autoincrement=False, nullable=True),
    sa.Column('priority', sa.Integer(), autoincrement=False, nullable=True),
    sa.Column('distance', sa.Integer(), autoincrement=False, nullable=True),
    sa.Column('is_text', sa.Boolean(), autoincrement=False, nullable=True),
    sa.Column('limit_netloc', sa.Boolean(), autoincrement=False, nullable=True),
    sa.Column('title', citext.CIText(), autoincrement=False, nullable=True),
    sa.Column('mimetype', sa.Text(), autoincrement=False, nullable=True),
    sa.Column('type', postgresql.ENUM('western', 'eastern', 'unknown', name='itemtype_enum', create_type=False), autoincrement=False, nullable=True),
    sa.Column('content', sa.Text(), autoincrement=False, nullable=True),
    sa.Column('fetchtime', sa.DateTime(), autoincrement=False, nullable=True),
    sa.Column('addtime', sa.DateTime(), autoincrement=False, nullable=True),
    sa.Column('ignoreuntiltime', sa.DateTime(), autoincrement=False, nullable=True),
    sa.Column('normal_fetch_mode', sa.Boolean(), autoincrement=False, nullable=True),
    sa.Column('tsv_content', sqlalchemy_utils.types.ts_vector.TSVectorType(), autoincrement=False, nullable=True),
    sa.Column('transaction_id', sa.BigInteger(), autoincrement=False, nullable=False),
    sa.Column('end_transaction_id', sa.BigInteger(), nullable=True),
    sa.Column('operation_type', sa.SmallInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id', 'transaction_id')
    )
    # op.create_index(op.f('ix_web_pages_version_distance'), 'web_pages_version', ['distance'], unique=False)
    # op.create_index(op.f('ix_web_pages_version_ignoreuntiltime'), 'web_pages_version', ['ignoreuntiltime'], unique=False)
    # op.create_index(op.f('ix_web_pages_version_netloc'), 'web_pages_version', ['netloc'], unique=False)
    # op.create_index(op.f('ix_web_pages_version_priority'), 'web_pages_version', ['priority'], unique=False)
    # op.create_index(op.f('ix_web_pages_version_state'), 'web_pages_version', ['state'], unique=False)
    # op.create_index('ix_web_pages_version_tsv_content', 'web_pages_version', ['tsv_content'], unique=False, postgresql_using='gin')
    # op.create_index(op.f('ix_web_pages_version_type'), 'web_pages_version', ['type'], unique=False)

    op.create_index(op.f('ix_web_pages_version_id'), 'web_pages_version', ['id'], unique=False)
    op.create_index(op.f('ix_web_pages_version_operation_type'), 'web_pages_version', ['operation_type'], unique=False)
    op.create_index(op.f('ix_web_pages_version_transaction_id'), 'web_pages_version', ['transaction_id'], unique=False)
    op.create_index(op.f('ix_web_pages_version_end_transaction_id'), 'web_pages_version', ['end_transaction_id'], unique=False)
    op.create_index(op.f('ix_web_pages_version_url'), 'web_pages_version', ['url'], unique=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_web_pages_version_url'), table_name='web_pages_version')
    op.drop_index(op.f('ix_web_pages_version_type'), table_name='web_pages_version')
    op.drop_index('ix_web_pages_version_tsv_content', table_name='web_pages_version')
    op.drop_index(op.f('ix_web_pages_version_transaction_id'), table_name='web_pages_version')
    op.drop_index(op.f('ix_web_pages_version_state'), table_name='web_pages_version')
    op.drop_index(op.f('ix_web_pages_version_priority'), table_name='web_pages_version')
    op.drop_index(op.f('ix_web_pages_version_operation_type'), table_name='web_pages_version')
    op.drop_index(op.f('ix_web_pages_version_netloc'), table_name='web_pages_version')
    op.drop_index(op.f('ix_web_pages_version_ignoreuntiltime'), table_name='web_pages_version')
    op.drop_index(op.f('ix_web_pages_version_id'), table_name='web_pages_version')
    op.drop_index(op.f('ix_web_pages_version_end_transaction_id'), table_name='web_pages_version')
    op.drop_index(op.f('ix_web_pages_version_distance'), table_name='web_pages_version')
    op.drop_table('web_pages_version')
    op.drop_table('transaction')
    ### end Alembic commands ###
