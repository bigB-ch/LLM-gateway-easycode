import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.plan import Plan, UserPlan
from models.user import User
from models.recharge_record import RechargeRecord
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

    from redis_client import sync_balance_cache as _sync
    await _sync(str(u.id), u.balance)

    from datetime import datetime, timedelta, timezone
    up = UserPlan(
        id=uuid.uuid4(),
        user_id=u.id,
        plan_id=plan.id,
        token_remaining=plan.token_quota,
        expires_at=datetime.now(timezone.utc) + timedelta(days=plan.duration_days),
    )
    db.add(up)
    from redis_client import redis as _r
    try: await _r.set(f"user_has_plans:{u.id}", "1", ex=86400)
    except: pass
    await db.commit()
    return {"message": "purchased", "balance_yuan": round(u.balance / 100, 2)}


class RechargeRequest(BaseModel):
    amount_yuan: float
    method: str = "alipay"
    txn_id: str | None = None


@router.post("/recharge")
async def recharge(
    req: RechargeRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if req.amount_yuan <= 0:
        raise HTTPException(status_code=400, detail={"error": "invalid_amount"})
    amount_fen = int(req.amount_yuan * 100)

    rec = RechargeRecord(
        id=uuid.uuid4(),
        user_id=user["user_id"],
        amount=amount_fen,
        method=req.method,
        status="pending",
    )
    db.add(rec)
    await db.commit()
    return {
        "message": "payment_submitted",
        "id": str(rec.id),
        "amount_yuan": req.amount_yuan,
        "status": "pending",
    }


class RedeemRequest(BaseModel):
    code: str


@router.post("/redeem")
async def redeem_code(
    req: RedeemRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Redeem a topup code."""
    code = req.code.strip()
    if not code or len(code) < 6:
        raise HTTPException(status_code=400, detail={"error": "invalid_code"})

    # Check if code exists in system_config as a redemption code
    from models.system_config import SystemConfig
    cfg_result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == f"redeem_{code}")
    )
    cfg = cfg_result.scalar_one_or_none()
    if cfg is None or not cfg.value:
        raise HTTPException(status_code=404, detail={"error": "code_not_found_or_used"})

    amount_fen = int(cfg.value.get("amount_yuan", 0) * 100)
    if amount_fen <= 0:
        raise HTTPException(status_code=400, detail={"error": "invalid_code"})

    user_result = await db.execute(select(User).where(User.id == user["user_id"]))
    u = user_result.scalar_one()
    u.balance += amount_fen

    from redis_client import sync_balance_cache as _sync2
    await _sync2(str(u.id), u.balance)

    rec = RechargeRecord(
        id=uuid.uuid4(),
        user_id=u.id,
        amount=amount_fen,
        method="redeem",
        status="success",
    )
    db.add(rec)

    # Delete the code (single use)
    await db.delete(cfg)
    await db.commit()
    return {
        "message": "redeemed",
        "amount_yuan": round(amount_fen / 100, 2),
        "balance_yuan": round(u.balance / 100, 2),
    }


# ── Alipay F2F Payment ──

class AlipayRechargeRequest(BaseModel):
    amount_yuan: float


@router.post("/recharge/alipay")
async def alipay_recharge(
    req: AlipayRechargeRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an Alipay QR code payment order."""
    if req.amount_yuan <= 0:
        raise HTTPException(status_code=400, detail={"error": "invalid_amount"})

    from services.alipay import create_qr_payment
    # Use the frontend origin as base for the callback URL
    notify_url = ""  # Alipay requires an accessible URL; use polling fallback

    result = await create_qr_payment(
        amount_yuan=req.amount_yuan,
        subject="LLM Gateway API Credit Top-up",
        notify_url=notify_url,
        db=db,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail={"error": result.get("error", "alipay_failed")})

    # Save pending recharge record with QR code and trade number
    amount_fen = int(req.amount_yuan * 100)
    rec = RechargeRecord(
        id=uuid.uuid4(),
        user_id=user["user_id"],
        amount=amount_fen,
        method="alipay",
        status="pending",
        qr_code=result.get("qr_code"),
        out_trade_no=result.get("out_trade_no"),
    )
    db.add(rec)
    await db.commit()

    return {
        "success": True,
        "qr_code": result["qr_code"],
        "out_trade_no": result["out_trade_no"],
        "amount": result["amount"],
        "record_id": str(rec.id),
    }


# ── Alipay Computer Website Payment (电脑网站支付) ──

class AlipayPagePaymentRequest(BaseModel):
    amount_yuan: float
    return_url: str | None = None  # frontend URL to redirect back after payment


@router.post("/recharge/alipay/page")
async def alipay_page_payment(
    req: AlipayPagePaymentRequest,
    request: Request,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an Alipay Computer Website Payment order. Redirects user to Alipay."""
    if req.amount_yuan <= 0:
        raise HTTPException(status_code=400, detail={"error": "invalid_amount"})

    from services.alipay import create_page_payment

    # Construct return_url (with frontend redirect URL param) and notify_url
    # Respect X-Forwarded-Proto from nginx (ssl termination)
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.url.hostname
    port = request.url.port
    server_base = f"{scheme}://{host}" + (f":{port}" if port else "")

    # Save the frontend return URL for redirect after payment
    frontend_return_url = req.return_url or server_base

    from urllib.parse import quote
    alipay_return_url = f"{server_base}/admin/api/plans/alipay/return?frontend_url={quote(frontend_return_url)}"
    notify_url = f"{server_base}/admin/api/plans/alipay/notify"

    result = await create_page_payment(
        amount_yuan=req.amount_yuan,
        subject="LLM Gateway API Credit Top-up",
        return_url=alipay_return_url,
        notify_url=notify_url,
        db=db,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail={"error": result.get("error", "alipay_failed")})

    # Store payment intent in Redis (not in DB — only create record on confirmed payment)
    amount_fen = int(req.amount_yuan * 100)
    out_trade_no = result["out_trade_no"]
    import json as _json
    try:
        from redis_client import redis as _r
        await _r.set(
            f"alipay_pay:{out_trade_no}",
            _json.dumps({"user_id": user["user_id"], "amount_fen": amount_fen}),
            ex=3600,
        )
    except Exception:
        pass  # Redis failure is non-fatal; return handler will create without prepay info

    return {
        "success": True,
        "redirect_url": result["redirect_url"],
        "out_trade_no": out_trade_no,
        "amount": result["amount"],
    }


@router.get("/alipay/return")
async def alipay_return(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle Alipay synchronous return redirect after payment."""
    from urllib.parse import unquote
    import json as _json

    params = dict(request.query_params)

    # Pop our own params (not signed by Alipay)
    frontend_url = unquote(params.pop("frontend_url", "/"))

    from services.alipay import get_alipay_config
    cfg = await get_alipay_config(db)
    alipay_public_key = cfg.get("alipay_public_key", "")

    out_trade_no = params.get("out_trade_no", "")

    if alipay_public_key:
        from services.alipay import verify_callback_sign
        if not verify_callback_sign(params.copy(), alipay_public_key):
            return RedirectResponse(url=f"{frontend_url}?payment=fail&reason=verify_failed")

    payment_status = "pending"

    if out_trade_no:
        # Check if async notification already credited this
        existing = await db.execute(
            select(RechargeRecord).where(RechargeRecord.out_trade_no == out_trade_no, RechargeRecord.status == "success")
        )
        if existing.scalar_one_or_none():
            payment_status = "success"
        else:
            # Read payment intent from Redis
            prepay_info = None
            try:
                from redis_client import redis as _r
                data = await _r.get(f"alipay_pay:{out_trade_no}")
                if data:
                    prepay_info = _json.loads(data)
            except Exception:
                pass

            if prepay_info:
                # Verify with Alipay and credit
                try:
                    from services.alipay import query_payment
                    pay_result = await query_payment(out_trade_no, db)
                    if pay_result.get("paid"):
                        rec = RechargeRecord(
                            id=uuid.uuid4(),
                            user_id=uuid.UUID(prepay_info["user_id"]),
                            amount=prepay_info["amount_fen"],
                            method="alipay",
                            status="success",
                            out_trade_no=out_trade_no,
                        )
                        db.add(rec)
                        user_result = await db.execute(select(User).where(User.id == rec.user_id))
                        u = user_result.scalar_one()
                        u.balance += rec.amount
                        from redis_client import sync_balance_cache as _sync3
                        await _sync3(str(u.id), u.balance)
                        await db.commit()
                        payment_status = "success"
                        # Clean up Redis
                        try:
                            await _r.delete(f"alipay_pay:{out_trade_no}")
                        except Exception:
                            pass
                except Exception:
                    pass
            else:
                # No prepay info — async notification will handle when it arrives
                pass

    return RedirectResponse(url=f"{frontend_url}?payment={payment_status}&out_trade_no={out_trade_no}")


@router.post("/recharge/alipay/query")
async def alipay_query(
    out_trade_no: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query Alipay payment status and auto-credit if paid."""
    from services.alipay import query_payment
    result = await query_payment(out_trade_no, db)
    if not result.get("success"):
        return result

    if result.get("paid"):
        # Auto-credit: find the pending record and approve
        rec_result = await db.execute(
            select(RechargeRecord).where(
                RechargeRecord.status == "pending",
                RechargeRecord.user_id == user["user_id"],
            ).order_by(RechargeRecord.created_at.desc()).limit(1)
        )
        rec = rec_result.scalar_one_or_none()
        if rec:
            rec.status = "success"
            user_result = await db.execute(select(User).where(User.id == user["user_id"]))
            u = user_result.scalar_one()
            u.balance += rec.amount
            await _sync(str(u.id), u.balance)
            await db.commit()
            return {
                "paid": True,
                "trade_status": result["trade_status"],
                "balance_yuan": round(u.balance / 100, 2),
            }

    return {"paid": False, "trade_status": result.get("trade_status", "")}


@router.post("/alipay/notify")
async def alipay_notify(request: Request):
    """Alipay async payment notification callback."""
    from database import async_session
    async with async_session() as db:
        body = await request.body()
        from urllib.parse import parse_qs
        params = {k: v[0] for k, v in parse_qs(body.decode()).items()}

        from services.alipay import get_alipay_config
        cfg = await get_alipay_config(db)
        alipay_public_key = cfg.get("alipay_public_key", "")

        if not alipay_public_key:
            return "fail"

        from services.alipay import verify_callback_sign
        if not verify_callback_sign(params.copy(), alipay_public_key):
            return "fail"

        trade_status = params.get("trade_status", "")
        out_trade_no = params.get("out_trade_no", "")
        total_amount = float(params.get("total_amount", 0))

        if trade_status == "TRADE_SUCCESS":
            import json as _json
            prepay_info = None
            try:
                from redis_client import redis as _r
                data = await _r.get(f"alipay_pay:{out_trade_no}")
                if data:
                    prepay_info = _json.loads(data)
            except Exception:
                pass

            if prepay_info:
                # Check if already credited (e.g., via return handler)
                existing = await db.execute(
                    select(RechargeRecord).where(
                        RechargeRecord.out_trade_no == out_trade_no,
                        RechargeRecord.status == "success",
                    )
                )
                if not existing.scalar_one_or_none():
                    rec = RechargeRecord(
                        id=uuid.uuid4(),
                        user_id=uuid.UUID(prepay_info["user_id"]),
                        amount=prepay_info["amount_fen"],
                        method="alipay",
                        status="success",
                        out_trade_no=out_trade_no,
                    )
                    db.add(rec)
                    user_result = await db.execute(select(User).where(User.id == rec.user_id))
                    u = user_result.scalar_one()
                    u.balance += rec.amount
                    await _sync(str(u.id), u.balance)
                    await db.commit()
                # Clean up Redis
                try:
                    from redis_client import redis as _r2
                    await _r2.delete(f"alipay_pay:{out_trade_no}")
                except Exception:
                    pass
    return "success"


@router.get("/recharge-history")
async def recharge_history(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RechargeRecord)
        .where(RechargeRecord.user_id == user["user_id"])
        .order_by(RechargeRecord.created_at.desc())
        .limit(50)
    )
    records = result.scalars().all()
    return {
        "items": [
            {
                "id": str(r.id),
                "amount": r.amount,
                "method": r.method,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
            }
            for r in records
        ]
    }


# ── Payment Management (Admin) ──

@router.get("/payments/pending")
async def list_pending_payments(
    _admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RechargeRecord)
        .where(RechargeRecord.status == "pending")
        .order_by(RechargeRecord.created_at.desc())
        .limit(100)
    )
    records = result.scalars().all()
    items = []
    for r in records:
        user_result = await db.execute(select(User).where(User.id == r.user_id))
        u = user_result.scalar_one_or_none()
        items.append({
            "id": str(r.id),
            "user_id": str(r.user_id),
            "username": u.username if u else "-",
            "email": u.email if u else "-",
            "amount": r.amount,
            "amount_yuan": round(r.amount / 100, 2),
            "method": r.method,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
        })
    return {"items": items}


class ApproveRequest(BaseModel):
    approved: bool


@router.post("/payments/{payment_id}/verify")
async def verify_payment(
    payment_id: str,
    req: ApproveRequest,
    _admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(RechargeRecord).where(RechargeRecord.id == payment_id))
    rec = result.scalar_one_or_none()
    if rec is None:
        raise HTTPException(status_code=404, detail={"error": "payment_not_found"})
    if rec.status != "pending":
        raise HTTPException(status_code=400, detail={"error": "already_processed"})

    if req.approved:
        rec.status = "success"
        user_result = await db.execute(select(User).where(User.id == rec.user_id))
        u = user_result.scalar_one()
        u.balance += rec.amount
        await _sync(str(u.id), u.balance)
        await db.commit()
        return {"message": "payment_approved", "balance_yuan": round(u.balance / 100, 2)}
    else:
        rec.status = "rejected"
        await db.commit()
        return {"message": "payment_rejected"}
