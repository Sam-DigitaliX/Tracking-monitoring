"""Monitoring dashboard endpoints.

Provides aggregated views of the data collected by the Probr GTM Listener tag:
- Event volumes & trends
- Tag health (success rates, execution times)
- User data quality scores
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import MonitoringBatch, Site
from app.schemas import (
    EventVolumeSummary,
    MonitoringBatchRead,
    MonitoringOverview,
    TagHealthSummary,
    UserDataQualitySummary,
)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/sites/{site_id}/overview", response_model=MonitoringOverview)
async def get_monitoring_overview(
    site_id: uuid.UUID,
    hours: int = 24,
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated monitoring overview for a site over the last N hours."""

    # Verify site
    site_result = await db.execute(select(Site).where(Site.id == site_id))
    site = site_result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    # Fetch all batches in the time window
    stmt = (
        select(MonitoringBatch)
        .where(
            MonitoringBatch.site_id == site_id,
            MonitoringBatch.window_start >= since,
        )
        .order_by(MonitoringBatch.window_start.desc())
    )
    result = await db.execute(stmt)
    batches = result.scalars().all()

    if not batches:
        return MonitoringOverview(
            site_id=site_id,
            site_name=site.name,
            container_id=None,
            period_hours=hours,
            total_events=0,
            events=[],
            tags=[],
            user_data=None,
            last_seen=None,
        )

    # Aggregate across all batches
    total_events = 0
    event_totals: dict[str, int] = {}
    tag_totals: dict[str, dict[str, int]] = {}
    ud_totals = {"email": 0, "phone": 0, "address": 0, "total": 0}
    container_id = batches[0].container_id
    last_seen = batches[0].window_start

    for batch in batches:
        total_events += batch.total_events

        for event_name, count in (batch.event_counts or {}).items():
            event_totals[event_name] = event_totals.get(event_name, 0) + count

        for tag_name, metrics in (batch.tag_metrics or {}).items():
            if tag_name not in tag_totals:
                tag_totals[tag_name] = {
                    "success": 0, "failure": 0, "timeout": 0,
                    "exception": 0, "total_exec_ms": 0, "count": 0,
                }
            for k, v in metrics.items():
                tag_totals[tag_name][k] = tag_totals[tag_name].get(k, 0) + v

        for k in ("email", "phone", "address", "total"):
            ud_totals[k] += (batch.user_data_quality or {}).get(k, 0)

    # Build event volume summaries
    events = [
        EventVolumeSummary(event_name=name, total_count=count)
        for name, count in sorted(event_totals.items(), key=lambda x: -x[1])
    ]

    # Build tag health summaries
    tags = []
    for tag_name, m in sorted(tag_totals.items(), key=lambda x: -x[1].get("count", 0)):
        total = m.get("count", 0)
        success = m.get("success", 0)
        failure = m.get("failure", 0) + m.get("timeout", 0) + m.get("exception", 0)
        tags.append(TagHealthSummary(
            tag_name=tag_name,
            total_executions=total,
            success_count=success,
            failure_count=failure,
            success_rate=round(success / total * 100, 2) if total > 0 else 0.0,
            avg_execution_time_ms=round(m.get("total_exec_ms", 0) / total, 1) if total > 0 else 0.0,
        ))

    # User data quality
    ud_total = ud_totals["total"]
    user_data = UserDataQualitySummary(
        email_rate=round(ud_totals["email"] / ud_total * 100, 2) if ud_total > 0 else 0.0,
        phone_rate=round(ud_totals["phone"] / ud_total * 100, 2) if ud_total > 0 else 0.0,
        address_rate=round(ud_totals["address"] / ud_total * 100, 2) if ud_total > 0 else 0.0,
        total_events=ud_total,
    ) if ud_total > 0 else None

    return MonitoringOverview(
        site_id=site_id,
        site_name=site.name,
        container_id=container_id,
        period_hours=hours,
        total_events=total_events,
        events=events,
        tags=tags,
        user_data=user_data,
        last_seen=last_seen,
    )


@router.get("/sites/{site_id}/batches", response_model=list[MonitoringBatchRead])
async def get_monitoring_batches(
    site_id: uuid.UUID,
    hours: int = 24,
    limit: int = 1440,
    db: AsyncSession = Depends(get_db),
):
    """Get raw monitoring batches for a site (for time-series charts)."""

    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    stmt = (
        select(MonitoringBatch)
        .where(
            MonitoringBatch.site_id == site_id,
            MonitoringBatch.window_start >= since,
        )
        .order_by(MonitoringBatch.window_start.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/sites/{site_id}/tags/{tag_name}", response_model=TagHealthSummary)
async def get_tag_health(
    site_id: uuid.UUID,
    tag_name: str,
    hours: int = 24,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed health metrics for a specific tag."""

    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    stmt = (
        select(MonitoringBatch)
        .where(
            MonitoringBatch.site_id == site_id,
            MonitoringBatch.window_start >= since,
        )
    )
    result = await db.execute(stmt)
    batches = result.scalars().all()

    totals = {"success": 0, "failure": 0, "timeout": 0, "exception": 0, "total_exec_ms": 0, "count": 0}

    for batch in batches:
        metrics = (batch.tag_metrics or {}).get(tag_name, {})
        for k, v in metrics.items():
            totals[k] = totals.get(k, 0) + v

    total = totals["count"]
    if total == 0:
        raise HTTPException(status_code=404, detail=f"No data for tag '{tag_name}'")

    success = totals["success"]
    failure = totals["failure"] + totals["timeout"] + totals["exception"]

    return TagHealthSummary(
        tag_name=tag_name,
        total_executions=total,
        success_count=success,
        failure_count=failure,
        success_rate=round(success / total * 100, 2),
        avg_execution_time_ms=round(totals["total_exec_ms"] / total, 1),
    )
