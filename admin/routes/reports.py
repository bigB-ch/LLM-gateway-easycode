from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.usage_log import UsageLog
from models.user import User
from dependencies import get_current_user, require_admin

router = APIRouter(prefix="/admin/api/reports", tags=["reports"])


@router.get("/dashboard")
async def dashboard(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    call_result = await db.execute(
        select(func.count(UsageLog.id)).where(
            UsageLog.user_id == user["user_id"],
            UsageLog.created_at >= today_start,
        )
    )
    today_calls = call_result.scalar() or 0

    cost_result = await db.execute(
        select(func.coalesce(func.sum(UsageLog.bill_cost), 0)).where(
            UsageLog.user_id == user["user_id"],
            UsageLog.created_at >= today_start,
            UsageLog.status == "success",
        )
    )
    today_cost = cost_result.scalar() or 0

    user_result = await db.execute(select(User).where(User.id == user["user_id"]))
    u = user_result.scalar_one()
    balance = u.balance

    return {
        "today_calls": today_calls,
        "today_cost_yuan": round(today_cost / 100, 2),
        "balance_yuan": round(balance / 100, 2),
    }


@router.get("/trend")
async def trend(
    days: int = Query(7, le=30),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)

    result = await db.execute(
        select(
            func.date(UsageLog.created_at).label("day"),
            func.coalesce(func.sum(UsageLog.bill_cost), 0).label("total"),
        )
        .where(UsageLog.user_id == user["user_id"], UsageLog.created_at >= start, UsageLog.status == "success")
        .group_by(text("day"))
        .order_by(text("day"))
    )
    rows = result.all()
    return {
        "trend": [
            {"date": str(row.day), "cost_yuan": round(row.total / 100, 2)}
            for row in rows
        ]
    }


@router.get("/usage")
async def usage_details(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    result = await db.execute(
        select(UsageLog)
        .where(UsageLog.user_id == user["user_id"])
        .order_by(UsageLog.created_at.desc())
        .limit(page_size)
        .offset(offset)
    )
    logs = result.scalars().all()
    return {
        "items": [
            {
                "id": str(log.id),
                "request_id": log.request_id,
                "model": log.model,
                "provider": log.provider,
                "prompt_tokens": log.prompt_tokens,
                "completion_tokens": log.completion_tokens,
                "cost_yuan": round(log.bill_cost / 100, 4),
                "latency_ms": log.latency_ms,
                "status": log.status,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]
    }
