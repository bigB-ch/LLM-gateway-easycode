from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from database import get_db
from models.system_config import SystemConfig
from dependencies import get_current_user, require_admin
import redis_client

router = APIRouter(prefix="/admin/api/system", tags=["system"])


def _utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


async def _get_announcements(db: AsyncSession) -> list:
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "announcements")
    )
    cfg = result.scalar_one_or_none()
    return cfg.value if cfg and cfg.value else []


async def _save_announcements(db: AsyncSession, items: list):
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "announcements")
    )
    cfg = result.scalar_one_or_none()
    if cfg:
        cfg.value = items
    else:
        cfg = SystemConfig(key="announcements", value=items)
        db.add(cfg)
    await db.commit()


_DEFAULT_FAQ = [
    {"id": "1", "q": "How to create an API key?", "a": "Go to Keys page and click '+ Add Key'. The key is shown only once — save it immediately."},
    {"id": "2", "q": "How to top up?", "a": "Go to Plans page and click on a quick amount or enter custom amount. Balance is deducted from your account."},
    {"id": "3", "q": "Which models are supported?", "a": "DeepSeek V3/V4, OpenAI GPT-4o, Claude, Gemini, Qwen, GLM, Kimi, MiniMax and more. Check the Models page for full catalog."},
    {"id": "4", "q": "What is the API base URL?", "a": f"Use https://your-domain.com/v1 as the base URL. All models use the OpenAI chat completions format."},
]


class AnnouncementUpsert(BaseModel):
    content: str


# ── Announcements (user-facing) ──

@router.get("/announcements")
async def get_announcements(
    _user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await _get_announcements(db)
    return {"items": items}


# ── Announcement management (admin) ──

@router.get("/admin/announcements")
async def list_announcements_admin(
    _admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return {"items": await _get_announcements(db)}


@router.post("/admin/announcements")
async def create_announcement(
    req: AnnouncementUpsert,
    _admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    items = await _get_announcements(db)
    import uuid
    new_item = {"id": uuid.uuid4().hex[:12], "content": req.content, "date": _utcnow()}
    items.insert(0, new_item)
    await _save_announcements(db, items)
    return new_item


@router.put("/admin/announcements/{item_id}")
async def update_announcement(
    item_id: str,
    req: AnnouncementUpsert,
    _admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    items = await _get_announcements(db)
    for item in items:
        if item["id"] == item_id:
            item["content"] = req.content
            item["date"] = _utcnow()
            await _save_announcements(db, items)
            return item
    raise HTTPException(status_code=404, detail={"error": "not_found"})


@router.delete("/admin/announcements/{item_id}")
async def delete_announcement(
    item_id: str,
    _admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    items = await _get_announcements(db)
    items = [i for i in items if i["id"] != item_id]
    await _save_announcements(db, items)
    return {"message": "deleted"}


@router.get("/faq")
async def get_faq(
    _user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "faq")
    )
    cfg = result.scalar_one_or_none()
    if cfg and cfg.value:
        return {"items": cfg.value}
    return {"items": _DEFAULT_FAQ}


class PaymentConfigRequest(BaseModel):
    app_id: str | None = None
    alipay_public_key: str | None = None
    private_key: str | None = None
    alipay_qr_url: str | None = None
    wechat_qr_url: str | None = None


@router.get("/payment-config")
async def get_payment_config(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemConfig).where(SystemConfig.key == "payment_config"))
    cfg = result.scalar_one_or_none()
    if cfg and cfg.value:
        return cfg.value
    return {"app_id": "", "alipay_public_key": "", "private_key": "", "alipay_qr_url": "", "wechat_qr_url": ""}


@router.put("/payment-config")
async def save_payment_config(
    req: PaymentConfigRequest,
    _admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SystemConfig).where(SystemConfig.key == "payment_config"))
    cfg = result.scalar_one_or_none()
    value = req.model_dump(exclude_none=True)
    if cfg:
        # Merge with existing
        merged = {**cfg.value, **value}
        cfg.value = merged
    else:
        cfg = SystemConfig(key="payment_config", value=value)
        db.add(cfg)
    await db.commit()
    return {"message": "saved", "config": cfg.value if cfg else value}


# ── Model Pricing ──

@router.get("/pricing")
async def get_pricing(db: AsyncSession = Depends(get_db)):
    """Get current model pricing config. Falls back to defaults if not customized."""
    result = await db.execute(select(SystemConfig).where(SystemConfig.key == "model_pricing"))
    cfg = result.scalar_one_or_none()
    if cfg and cfg.value:
        return {"data": cfg.value}
    # Return hardcoded defaults from gateway
    from pathlib import Path
    import sys
    gateway_pricing = Path(__file__).parent.parent.parent / "gateway" / "pricing.py"
    sys.path.insert(0, str(gateway_pricing.parent))
    from pricing import PRICING, MARKUP
    sys.path.pop(0)
    return {"data": {"models": PRICING, "markup": MARKUP}}


@router.put("/pricing")
async def save_pricing(
    req: dict,
    _admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Save model pricing config. Accepts {"models": {...}, "markup": 1.5}."""
    result = await db.execute(select(SystemConfig).where(SystemConfig.key == "model_pricing"))
    cfg = result.scalar_one_or_none()

    value = {
        "models": req.get("models", {}),
        "markup": req.get("markup", 1.5),
    }
    if cfg:
        cfg.value = value
    else:
        cfg = SystemConfig(key="model_pricing", value=value)
        db.add(cfg)
    await db.commit()

    # Sync to Redis for gateway
    try:
        import json
        r = redis_client.redis
        await r.set("pricing_config", json.dumps(value), ex=86400)
    except Exception:
        pass

    return {"message": "saved", "data": value}
