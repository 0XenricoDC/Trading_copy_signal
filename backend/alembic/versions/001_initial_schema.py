"""Initial schema with all tables and RLS

Revision ID: 001_initial_schema
Revises:
Create Date: 2024-01-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums
    subscription_tier_enum = postgresql.ENUM(
        'free', 'basic', 'pro', 'enterprise',
        name='subscriptiontier',
        create_type=False
    )
    subscription_tier_enum.create(op.get_bind(), checkfirst=True)

    source_type_enum = postgresql.ENUM(
        'telegram', 'fxblue', 'manual', 'webhook',
        name='sourcetype',
        create_type=False
    )
    source_type_enum.create(op.get_bind(), checkfirst=True)

    signal_direction_enum = postgresql.ENUM(
        'buy', 'sell',
        name='signaldirection',
        create_type=False
    )
    signal_direction_enum.create(op.get_bind(), checkfirst=True)

    signal_status_enum = postgresql.ENUM(
        'pending', 'processing', 'executed', 'partial', 'failed', 'cancelled', 'expired',
        name='signalstatus',
        create_type=False
    )
    signal_status_enum.create(op.get_bind(), checkfirst=True)

    trade_status_enum = postgresql.ENUM(
        'pending', 'opening', 'open', 'closing', 'closed', 'failed', 'cancelled',
        name='tradestatus',
        create_type=False
    )
    trade_status_enum.create(op.get_bind(), checkfirst=True)

    tp_strategy_enum = postgresql.ENUM(
        'equal', 'front_weighted', 'back_weighted', 'custom',
        name='tpstrategy',
        create_type=False
    )
    tp_strategy_enum.create(op.get_bind(), checkfirst=True)

    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('subscription_tier', subscription_tier_enum, server_default='free'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create telegram_channels table
    op.create_table(
        'telegram_channels',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('channel_id', sa.BigInteger(), nullable=False, index=True),
        sa.Column('channel_name', sa.String(255), nullable=False),
        sa.Column('channel_username', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create mt5_accounts table
    op.create_table(
        'mt5_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('login', sa.Integer(), nullable=False, index=True),
        sa.Column('encrypted_password', sa.Text(), nullable=False),
        sa.Column('server', sa.String(255), nullable=False),
        sa.Column('mt5_path', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('is_demo', sa.Boolean(), server_default='true'),
        sa.Column('last_connected', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_balance', sa.Float(), nullable=True),
        sa.Column('last_equity', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create signal_subscriptions table
    op.create_table(
        'signal_subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('channel_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('telegram_channels.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('mt5_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mt5_accounts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('lot_size', sa.Float(), nullable=True),
        sa.Column('risk_percent', sa.Float(), nullable=True),
        sa.Column('max_lot_size', sa.Float(), server_default='10.0'),
        sa.Column('tp_strategy', tp_strategy_enum, server_default='equal'),
        sa.Column('tp_split_ratios', postgresql.JSONB(), nullable=True),
        sa.Column('symbol_mapping', postgresql.JSONB(), nullable=True),
        sa.Column('allowed_symbols', postgresql.JSONB(), nullable=True),
        sa.Column('blocked_symbols', postgresql.JSONB(), nullable=True),
        sa.Column('min_sl_pips', sa.Float(), nullable=True),
        sa.Column('max_sl_pips', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create raw_signals table
    op.create_table(
        'raw_signals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('channel_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('telegram_channels.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('source_type', source_type_enum, server_default='telegram'),
        sa.Column('source_message_id', sa.BigInteger(), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column('is_processed', sa.Boolean(), server_default='false'),
    )

    # Create parsed_signals table
    op.create_table(
        'parsed_signals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('raw_signal_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('raw_signals.id', ondelete='SET NULL'), nullable=True),
        sa.Column('symbol', sa.String(20), nullable=False, index=True),
        sa.Column('direction', signal_direction_enum, nullable=False),
        sa.Column('entry_price', sa.Float(), nullable=True),
        sa.Column('entry_price_low', sa.Float(), nullable=True),
        sa.Column('entry_price_high', sa.Float(), nullable=True),
        sa.Column('stop_loss', sa.Float(), nullable=False),
        sa.Column('take_profits', postgresql.JSONB(), server_default='[]'),
        sa.Column('status', signal_status_enum, server_default='pending'),
        sa.Column('parser_confidence', sa.Float(), nullable=True),
        sa.Column('parser_notes', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create trades table
    op.create_table(
        'trades',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('parsed_signal_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('parsed_signals.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('mt5_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mt5_accounts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('mt5_ticket', sa.BigInteger(), nullable=True, index=True),
        sa.Column('mt5_order_id', sa.BigInteger(), nullable=True),
        sa.Column('symbol', sa.String(20), nullable=False, index=True),
        sa.Column('direction', signal_direction_enum, nullable=False),
        sa.Column('volume', sa.Float(), nullable=False),
        sa.Column('entry_price', sa.Float(), nullable=True),
        sa.Column('stop_loss', sa.Float(), nullable=False),
        sa.Column('take_profit', sa.Float(), nullable=True),
        sa.Column('tp_level', sa.Integer(), nullable=True),
        sa.Column('status', trade_status_enum, server_default='pending'),
        sa.Column('open_price', sa.Float(), nullable=True),
        sa.Column('close_price', sa.Float(), nullable=True),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('profit', sa.Float(), nullable=True),
        sa.Column('profit_pips', sa.Float(), nullable=True),
        sa.Column('commission', sa.Float(), nullable=True),
        sa.Column('swap', sa.Float(), nullable=True),
        sa.Column('error_code', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Enable RLS on all tenant-scoped tables
    tables_with_rls = [
        'telegram_channels',
        'mt5_accounts',
        'signal_subscriptions',
        'raw_signals',
        'parsed_signals',
        'trades',
    ]

    for table in tables_with_rls:
        op.execute(f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY')

        # Create RLS policy
        op.execute(f'''
            CREATE POLICY {table}_tenant_isolation ON {table}
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
        ''')


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('trades')
    op.drop_table('parsed_signals')
    op.drop_table('raw_signals')
    op.drop_table('signal_subscriptions')
    op.drop_table('mt5_accounts')
    op.drop_table('telegram_channels')
    op.drop_table('tenants')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS tradestatus')
    op.execute('DROP TYPE IF EXISTS signalstatus')
    op.execute('DROP TYPE IF EXISTS signaldirection')
    op.execute('DROP TYPE IF EXISTS sourcetype')
    op.execute('DROP TYPE IF EXISTS tpstrategy')
    op.execute('DROP TYPE IF EXISTS subscriptiontier')
