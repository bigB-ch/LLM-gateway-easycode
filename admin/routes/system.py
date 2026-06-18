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
    {"id": "1", "q": "如何创建 API 密钥？", "a": "进入令牌管理页面，点击"+ 添加令牌"，填写名称和权限，密钥仅显示一次，请立即保存。"},
    {"id": "2", "q": "如何充值？", "a": "进入钱包管理页面，选择充值金额和支付方式，扫码支付后等待管理员审核到账。"},
    {"id": "3", "q": "支持哪些模型？", "a": "支持 DeepSeek V3/V4、OpenAI GPT-4o、Claude、Gemini、Qwen、GLM、Kimi、MiniMax、可灵等主流模型。进入模型广场可查看完整列表和价格。"},
    {"id": "4", "q": "API 接口地址是什么？", "a": "使用 https://8.163.17.83/v1 作为接口地址，格式兼容 OpenAI Chat Completions API。"},
    {"id": "5", "q": "如何查看用量？", "a": "进入使用日志页面，可按日期范围和模型筛选查看每次调用的 Token 消耗和费用。"},
    {"id": "6", "q": "余额怎么扣费？", "a": "按实际消耗的 Token 计费，费用 = 模型价格 x 加价系数。优先消耗套餐内 Token，套餐不足时从余额扣减。"},
]


class AnnouncementUpsert(BaseModel):
    content: str


# 鈹�鈹� Announcements (user-facing) 鈹�鈹�

@router.get("/announcements")
async def get_announcements(
    _user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await _get_announcements(db)
    return {"items": items}


# 鈹�鈹� Announcement management (admin) 鈹�鈹�

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


# 鈹�鈹� Model Pricing 鈹�鈹�

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
