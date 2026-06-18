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
