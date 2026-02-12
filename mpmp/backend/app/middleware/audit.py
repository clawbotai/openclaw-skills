"""Audit logging middleware — records every PHI-touching operation."""
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log_audit(
    db: AsyncSession,
    user_id: uuid.UUID | None,
    action: str,
    resource_table: str,
    resource_id: str | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Write an immutable audit log entry."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_table=resource_table,
        resource_id=resource_id,
        detail=detail,
        ip_address=ip_address,
        user_agent=user_agent,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(entry)
    # Flush immediately — audit logs must persist even if the outer transaction rolls back
    await db.flush()
