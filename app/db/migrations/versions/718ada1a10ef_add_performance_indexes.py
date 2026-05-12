"""add performance indexes
Revision ID: 718ada1a10ef
Revises: fea294711add
Create Date: 2026-05-12 15:16:01.656309
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '718ada1a10ef'
down_revision: Union[str, Sequence[str], None] = 'fea294711add'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_telemetry_device_id", "telemetry_records", ["device_id"])
    op.create_index("ix_telemetry_timestamp", "telemetry_records", ["timestamp"])
    op.create_index("ix_telemetry_anomaly_score", "telemetry_records", ["anomaly_score"])
    op.create_index("ix_telemetry_device_timestamp", "telemetry_records", ["device_id", "timestamp"])
    op.create_index("ix_devices_vertical", "devices", ["vertical"])
    op.create_index("ix_devices_status", "devices", ["status"])
    op.create_index("ix_devices_is_active", "devices", ["is_active"])


def downgrade() -> None:
    op.drop_index("ix_telemetry_device_id", "telemetry_records")
    op.drop_index("ix_telemetry_timestamp", "telemetry_records")
    op.drop_index("ix_telemetry_anomaly_score", "telemetry_records")
    op.drop_index("ix_telemetry_device_timestamp", "telemetry_records")
    op.drop_index("ix_devices_vertical", "devices")
    op.drop_index("ix_devices_status", "devices")
    op.drop_index("ix_devices_is_active", "devices")
