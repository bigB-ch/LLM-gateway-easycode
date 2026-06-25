import uuid
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.usage_log import UsageLog
from models.user import User
from models.api_key import ApiKey
from dependencies import get_current_user, require_admin

router = APIRouter(prefix="/admin/api/reports", tags=["reports"])


def parse_date_end(d: str) -> datetime:
    """Convert date string 'YYYY-MM-DD' to exclusive end-of-day boundary (< next day)."""
    return datetime.fromisoformat(d) + timedelta(days=1)


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

    # All-time totals
    total_calls_result = await db.execute(
        select(func.count(UsageLog.id)).where(UsageLog.user_id == user["user_id"])
    )
    total_calls = total_calls_result.scalar() or 0

    total_tokens_result = await db.execute(
        select(func.coalesce(func.sum(UsageLog.prompt_tokens + UsageLog.completion_tokens), 0)).where(
            UsageLog.user_id == user["user_id"]
        )
    )
    total_tokens = total_tokens_result.scalar() or 0

    total_cost_result = await db.execute(
        select(func.coalesce(func.sum(UsageLog.bill_cost), 0)).where(
            UsageLog.user_id == user["user_id"],
            UsageLog.status == "success",
        )
    )
    total_cost = total_cost_result.scalar() or 0

    key_count_result = await db.execute(
        select(func.count(ApiKey.id)).where(
            ApiKey.user_id == user["user_id"],
            ApiKey.status == "active",
        )
    )
    key_count = key_count_result.scalar() or 0

    return {
        "today_calls": today_calls,
        "today_cost_yuan": round(today_cost / 100, 2),
        "balance_yuan": round(balance / 100, 2),
        "total_calls": total_calls,
        "total_tokens": total_tokens,
        "total_cost_yuan": round(total_cost / 100, 2),
        "key_count": key_count,
    }


@router.get("/admin-dashboard")
async def admin_dashboard(
    _admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0

    today_calls_result = await db.execute(
        select(func.count(UsageLog.id)).where(UsageLog.created_at >= today_start)
    )
    today_calls = today_calls_result.scalar() or 0

    today_revenue_result = await db.execute(
        select(func.coalesce(func.sum(UsageLog.bill_cost), 0)).where(
            UsageLog.created_at >= today_start,
            UsageLog.status == "success",
        )
    )
    today_revenue = today_revenue_result.scalar() or 0

    # Active suppliers count (from gateway Redis — fallback to 0)
    active_suppliers = 0
    try:
        from redis_client import redis
        keys = await redis.hkeys("supplier_configs")
        active_suppliers = len(keys)
    except Exception:
        pass

    # Top models today
    top_models_result = await db.execute(
        select(UsageLog.model, func.count(UsageLog.id).label("cnt"))
        .where(UsageLog.created_at >= today_start, UsageLog.status == "success")
        .group_by(UsageLog.model)
        .order_by(text("cnt DESC"))
        .limit(5)
    )
    top_models = [{"model": row.model, "count": row.cnt} for row in top_models_result.all()]

    # Recent calls
    recent_result = await db.execute(
        select(UsageLog)
        .order_by(UsageLog.created_at.desc())
        .limit(10)
    )
    recent = [
        {
            "id": str(log.id),
            "user_id": str(log.user_id),
            "model": log.model,
            "provider": log.provider,
            "prompt_tokens": log.prompt_tokens,
            "completion_tokens": log.completion_tokens,
            "cost_yuan": round(log.bill_cost / 100, 4),
            "latency_ms": log.latency_ms,
            "status": log.status,
            "created_at": log.created_at.isoformat(),
        }
        for log in recent_result.scalars().all()
    ]

    return {
        "total_users": total_users,
        "today_calls": today_calls,
        "today_revenue_yuan": round(today_revenue / 100, 2),
        "active_suppliers": active_suppliers,
        "top_models": top_models,
        "recent_calls": recent,
    }


@router.get("/admin-trend")
async def admin_trend(
    days: int = Query(7, le=30),
    _admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)

    result = await db.execute(
        select(
            func.date(UsageLog.created_at).label("day"),
            func.count(UsageLog.id).label("calls"),
            func.coalesce(func.sum(UsageLog.prompt_tokens + UsageLog.completion_tokens), 0).label("tokens"),
            func.coalesce(func.sum(UsageLog.bill_cost), 0).label("total"),
        )
        .where(UsageLog.created_at >= start, UsageLog.status == "success")
        .group_by(text("day"))
        .order_by(text("day"))
    )
    return {
        "trend": [
            {"date": str(row.day), "calls": row.calls, "tokens": row.tokens, "cost_yuan": round(row.total / 100, 2)}
            for row in result
        ]
    }


@router.get("/admin-daily")
async def admin_daily(
    page: int = Query(1, ge=1),
    page_size: int = Query(14, le=90),
    _admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Daily summary with pagination."""
    base = select(
        func.date(UsageLog.created_at).label("day"),
        func.count(UsageLog.id).label("calls"),
        func.count(UsageLog.id).filter(UsageLog.status == "success").label("success_calls"),
        func.coalesce(func.sum(UsageLog.prompt_tokens), 0).label("prompt_tokens"),
        func.coalesce(func.sum(UsageLog.completion_tokens), 0).label("completion_tokens"),
        func.coalesce(func.sum(UsageLog.bill_cost).filter(UsageLog.status == "success"), 0).label("cost"),
    )
    count_q = select(func.count()).select_from(
        base.group_by(text("day")).subquery()
    )
    total = (await db.execute(count_q)).scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        base.group_by(text("day")).order_by(text("day DESC")).limit(page_size).offset(offset)
    )
    return {
        "items": [
            {"date": str(r.day), "calls": r.calls, "success": r.success_calls,
             "prompt_tokens": r.prompt_tokens, "completion_tokens": r.completion_tokens,
             "cost_yuan": round(r.cost / 100, 2)}
            for r in result
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/user-daily")
async def admin_user_daily(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    _admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Daily usage grouped by user, with pagination."""
    from sqlalchemy import Date, cast

    conditions = []
    if date_from:
        conditions.append(UsageLog.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        conditions.append(UsageLog.created_at < parse_date_end(date_to))

    base = select(
        cast(UsageLog.created_at, Date).label("date"),
        UsageLog.user_id,
        User.username,
        User.email,
        UsageLog.model,
        func.count(UsageLog.id).label("calls"),
        func.count(UsageLog.id).filter(UsageLog.status == "success").label("success_calls"),
        func.coalesce(func.sum(UsageLog.prompt_tokens), 0).label("prompt_tokens"),
        func.coalesce(func.sum(UsageLog.completion_tokens), 0).label("completion_tokens"),
        func.coalesce(func.sum(UsageLog.bill_cost), 0).label("cost"),
    ).join(User, UsageLog.user_id == User.id).where(*conditions)

    order = text("date DESC, user_id, model")

    count_q = select(func.count()).select_from(
        base.group_by(text("date"), UsageLog.user_id, User.username, User.email, UsageLog.model).subquery()
    )
    total = (await db.execute(count_q)).scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        base.group_by(text("date"), UsageLog.user_id, User.username, User.email, UsageLog.model)
        .order_by(order)
        .limit(page_size)
        .offset(offset)
    )
    return {
        "items": [
            {
                "date": str(r.date),
                "user_id": str(r.user_id),
                "username": r.username,
                "email": r.email,
                "model": r.model,
                "calls": r.calls,
                "success": r.success_calls,
                "prompt_tokens": r.prompt_tokens,
                "completion_tokens": r.completion_tokens,
                "cost_yuan": round(r.cost / 100, 2),
            }
            for r in result
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
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
    # Also get call counts and token counts per day
    detail_result = await db.execute(
        select(
            func.date(UsageLog.created_at).label("day"),
            func.count(UsageLog.id).label("calls"),
            func.coalesce(func.sum(UsageLog.prompt_tokens + UsageLog.completion_tokens), 0).label("tokens"),
            func.coalesce(func.sum(UsageLog.bill_cost), 0).label("total"),
        )
        .where(UsageLog.user_id == user["user_id"], UsageLog.created_at >= start, UsageLog.status == "success")
        .group_by(text("day"))
        .order_by(text("day"))
    )
    return {
        "trend": [
            {"date": str(row.day), "cost_yuan": round(row.total / 100, 2)}
            for row in rows
        ],
        "details": [
            {"date": str(r.day), "calls": r.calls, "tokens": r.tokens, "cost_yuan": round(r.total / 100, 2)}
            for r in detail_result
        ],
    }


@router.get("/usage")
async def usage_details(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size

    conditions = [UsageLog.user_id == user["user_id"]]
    if date_from:
        conditions.append(UsageLog.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        conditions.append(UsageLog.created_at < parse_date_end(date_to))

    base_query = select(UsageLog).where(*conditions)
    count_q = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    # Total cost for filtered period (successful calls only)
    cost_q = select(func.coalesce(func.sum(UsageLog.bill_cost), 0)).where(
        *conditions, UsageLog.status == "success"
    )
    total_cost_result = await db.execute(cost_q)
    total_cost_fen = total_cost_result.scalar() or 0

    result = await db.execute(
        base_query.order_by(UsageLog.created_at.desc())
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
                "key_name": log.api_key_prefix,
                "prompt_tokens": log.prompt_tokens,
                "completion_tokens": log.completion_tokens,
                "cost_yuan": round(log.bill_cost / 100, 4),
                "latency_ms": log.latency_ms,
                "status": log.status,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_cost_yuan": round(total_cost_fen / 100, 2),
    }


@router.get("/all-usage")
async def all_usage(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    _admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    count_result = await db.execute(select(func.count(UsageLog.id)))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(UsageLog)
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
                "user_id": str(log.user_id) if log.user_id else "",
                "model": log.model,
                "provider": log.provider,
                "prompt_tokens": log.prompt_tokens,
                "completion_tokens": log.completion_tokens,
                "total_tokens": log.prompt_tokens + log.completion_tokens,
                "cost_yuan": round(log.bill_cost / 100, 4),
                "latency_ms": log.latency_ms,
                "status": log.status,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/user-usage-summary")
async def user_usage_summary(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    _admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Aggregated usage per user. One row per user with total calls, tokens, cost."""
    base = select(
        UsageLog.user_id,
        User.username,
        User.email,
        func.count(UsageLog.id).label("calls"),
        func.count(UsageLog.id).filter(UsageLog.status == "success").label("success_calls"),
        func.coalesce(func.sum(UsageLog.prompt_tokens), 0).label("prompt_tokens"),
        func.coalesce(func.sum(UsageLog.completion_tokens), 0).label("completion_tokens"),
        func.coalesce(func.sum(UsageLog.bill_cost), 0).label("cost"),
        func.max(UsageLog.created_at).label("last_used"),
    ).join(User, UsageLog.user_id == User.id).group_by(UsageLog.user_id, User.username, User.email)

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        base.order_by(text("cost DESC")).limit(page_size).offset(offset)
    )
    return {
        "items": [
            {
                "user_id": str(r.user_id),
                "username": r.username,
                "email": r.email,
                "calls": r.calls,
                "success": r.success_calls,
                "prompt_tokens": r.prompt_tokens,
                "completion_tokens": r.completion_tokens,
                "total_tokens": r.prompt_tokens + r.completion_tokens,
                "cost_yuan": round(r.cost / 100, 2),
                "last_used": r.last_used.isoformat() if r.last_used else None,
            }
            for r in result
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/user-model-usage/{user_id}")
async def user_model_usage(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    _admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Per-model aggregated stats + paginated detailed logs for a specific user."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail={"error": "invalid_user_id"})

    # Per-model aggregation
    model_result = await db.execute(
        select(
            UsageLog.model,
            func.count(UsageLog.id).label("calls"),
            func.count(UsageLog.id).filter(UsageLog.status == "success").label("success"),
            func.coalesce(func.sum(UsageLog.prompt_tokens), 0).label("prompt_tokens"),
            func.coalesce(func.sum(UsageLog.completion_tokens), 0).label("completion_tokens"),
            func.coalesce(func.sum(UsageLog.bill_cost), 0).label("cost"),
        )
        .where(UsageLog.user_id == uid)
        .group_by(UsageLog.model)
        .order_by(text("cost DESC"))
    )
    models = [
        {
            "model": r.model,
            "calls": r.calls,
            "success": r.success,
            "prompt_tokens": r.prompt_tokens,
            "completion_tokens": r.completion_tokens,
            "cost_yuan": round(r.cost / 100, 2),
        }
        for r in model_result
    ]

    # Detailed logs (paginated)
    offset = (page - 1) * page_size
    count_result = await db.execute(
        select(func.count(UsageLog.id)).where(UsageLog.user_id == uid)
    )
    total = count_result.scalar() or 0

    log_result = await db.execute(
        select(UsageLog)
        .where(UsageLog.user_id == uid)
        .order_by(UsageLog.created_at.desc())
        .limit(page_size)
        .offset(offset)
    )
    logs = [
        {
            "id": str(log.id),
            "request_id": log.request_id,
            "model": log.model,
            "provider": log.provider,
            "prompt_tokens": log.prompt_tokens,
            "completion_tokens": log.completion_tokens,
            "total_tokens": log.prompt_tokens + log.completion_tokens,
            "cost_yuan": round(log.bill_cost / 100, 4),
            "latency_ms": log.latency_ms,
            "status": log.status,
            "created_at": log.created_at.isoformat(),
        }
        for log in log_result.scalars().all()
    ]

    return {
        "models": models,
        "logs": logs,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
