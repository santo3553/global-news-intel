"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-14 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Sources table
    op.create_table(
        'sources',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('feed_url', sa.String(length=1024), nullable=False, unique=True),
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='rss'),
        sa.Column('country', sa.String(length=10), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('reliability_score', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_sources_domain', 'sources', ['domain'])

    # 2. Articles table
    op.create_table(
        'articles',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('source_id', sa.String(length=36), sa.ForeignKey('sources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=False, unique=True),
        sa.Column('canonical_url', sa.String(length=2048), nullable=True),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('raw_content', sa.Text(), nullable=True),
        sa.Column('cleaned_content', sa.Text(), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('title_hash', sa.String(length=64), nullable=True),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('processing_status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_articles_source_id', 'articles', ['source_id'])
    op.create_index('ix_articles_canonical_url', 'articles', ['canonical_url'])
    op.create_index('ix_articles_published_at', 'articles', ['published_at'])
    op.create_index('ix_articles_content_hash', 'articles', ['content_hash'])
    op.create_index('ix_articles_title_hash', 'articles', ['title_hash'])
    op.create_index('ix_articles_processing_status', 'articles', ['processing_status'])

    # 3. Events table
    op.create_table(
        'events',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('canonical_title', sa.String(length=512), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('subcategory', sa.String(length=100), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('geometry', sa.Text(), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('admin_region', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('location_confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('importance_score', sa.Float(), nullable=False, server_default='5.0'),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('human_impact_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('global_impact_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('economic_impact_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('political_impact_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('novelty_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('development_velocity_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('source_coverage_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_events_category', 'events', ['category'])
    op.create_index('ix_events_latitude', 'events', ['latitude'])
    op.create_index('ix_events_longitude', 'events', ['longitude'])
    op.create_index('ix_events_country', 'events', ['country'])
    op.create_index('ix_events_importance_score', 'events', ['importance_score'])
    op.create_index('ix_events_first_seen_at', 'events', ['first_seen_at'])
    op.create_index('ix_events_last_updated_at', 'events', ['last_updated_at'])
    op.create_index('ix_events_status', 'events', ['status'])
    op.create_index('idx_events_lat_lng', 'events', ['latitude', 'longitude'])
    op.create_index('idx_events_importance_first_seen', 'events', ['importance_score', 'first_seen_at'])

    # 4. Event Articles association table
    op.create_table(
        'event_articles',
        sa.Column('event_id', sa.String(length=36), sa.ForeignKey('events.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('article_id', sa.String(length=36), sa.ForeignKey('articles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('similarity_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('relationship_type', sa.String(length=50), nullable=False, server_default='corroborating'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 5. Entities table
    op.create_table(
        'entities',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('normalized_name', sa.String(length=255), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
    )
    op.create_index('ix_entities_name', 'entities', ['name'])
    op.create_index('ix_entities_entity_type', 'entities', ['entity_type'])
    op.create_index('ix_entities_normalized_name', 'entities', ['normalized_name'])

    # 6. Event Entities association table
    op.create_table(
        'event_entities',
        sa.Column('event_id', sa.String(length=36), sa.ForeignKey('events.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('entity_id', sa.String(length=36), sa.ForeignKey('entities.id', ondelete='CASCADE'), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table('event_entities')
    op.drop_table('entities')
    op.drop_table('event_articles')
    op.drop_table('events')
    op.drop_table('articles')
    op.drop_table('sources')
