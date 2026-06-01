import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.plan import Plan, UserPlan
from models.user import User
from dependencies import get_current_user, require_admin

router = APIRouter(prefix="/admin/api/plans", tags=["plans"])


class PlanCreate(BaseModel):
    name: str
    description: str | None = None
    token_quota: int
    price: int
    duration_days: int = 30


def _plan_to_response(p: Plan) -> dict:
    return {
        "id": str(p.id),
        "name": p.name,
        "description": p.description,
        "token_quota": p.token_quota,
        "price": p.price,
        "price_yuan": round(p.price / 100, 2),
        "duration_days": p.duration_days,
        "status": p.status,
    }


@router.get("")
async def list_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Plan).where(Plan.status == "active").order_by(Plan.price))
    plans = result.scalars().all()
    return {"items": [_plan_to_response(p) for p in plans]}


@router.post("")
async def create_plan(
    req: PlanCreate,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    plan = Plan(
        id=uuid.uuid4(),
        name=req.name,
        description=req.description,
        token_quota=req.token_quota,
        price=req.price,
        duration_days=req.duration_days,
    )
    db.add(plan)
    await db.commit()
    return _plan_to_response(plan)


@router.post("/{plan_id}/purchase")
async def purchase_plan(
    plan_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan_result = await db.execute(select(Plan).where(Plan.id == plan_id, Plan.status == "active"))
    plan = plan_result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail={"error": "plan_not_found"})

    user_result = await db.execute(select(User).where(User.id == user["user_id"]))
    u = user_result.scalar_one()

    if u.balance < plan.price:
        raise HTTPException(status_code=400, detail={"error": "insufficient_balance"})

    u.balance -= plan.price

    from datetime import datetime, timedelta, timezone
    up = UserPlan(
        id=uuid.uuid4(),
        user_id=u.id,
        plan_id=plan.id,
        token_remaining=plan.token_quota,
        expires_at=datetime.now(timezone.utc) + timedelta(days=plan.duration_days),
    )
    db.add(up)
    await db.commit()
    return {"message": "purchased", "balance_yuan": round(u.balance / 100, 2)}
