from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from database import get_db
from models.system_config import SystemConfig
from dependencies import get_current_user, require_admin

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


class AnnouncementUpsert(BaseModel):
    content: str


@router.get("/announcements")
async def get_announcements(
    _user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await _get_announcements(db)
    return {"items": items}


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
    for i, item in enumerate(items):
        if item["id"] == item_id:
            items.pop(i)
            await _save_announcements(db, items)
            return {"status": "deleted"}
    raise HTTPException(status_code=404, detail={"error": "not_found"})


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
    return {"alipay_qr_url": "", "wechat_qr_url": ""}


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
        merged = {**cfg.value, **value}
        cfg.value = merged
    else:
        cfg = SystemConfig(key="payment_config", value=value)
        db.add(cfg)
    await db.commit()
    return {"message": "saved", "config": cfg.value if cfg else value}
