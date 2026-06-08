"""
WeChat Pay Native (QR code) integration. Uses API v3 with RSA signing.
Requires: WeChat Pay merchant account with Native Pay enabled.
Credentials stored in system_config table as "wechatpay_config".
"""
import json
import time
import uuid
from base64 import b64encode
from urllib.parse import urlencode

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend

_WECHAT_API = "https://api.mch.weixin.qq.com"


async def get_wechat_config(db):
    from sqlalchemy import select
    from models.system_config import SystemConfig
    result = await db.execute(select(SystemConfig).where(SystemConfig.key == "wechatpay_config"))
    cfg = result.scalar_one_or_none()
    if cfg and cfg.value:
        return cfg.value
    return {}


def _build_signature(method: str, path: str, timestamp: int, nonce: str, body: str, private_key_pem: str) -> str:
    """Build WeChat Pay API v3 signature."""
    message = f"{method}\n{path}\n{timestamp}\n{nonce}\n{body}\n"
    key = serialization.load_pem_private_key(
        private_key_pem.encode(), password=None, backend=default_backend()
    )
    signature = key.sign(message.encode(), padding.PKCS1v15(), hashes.SHA256())
    return b64encode(signature).decode()


async def create_native_payment(amount_yuan: float, subject: str, notify_url: str, db) -> dict:
    """Create a WeChat Native payment order, return QR code URL."""
    cfg = await get_wechat_config(db)
    mch_id = cfg.get("mch_id", "")
    app_id = cfg.get("app_id", "")
    private_key = cfg.get("private_key", "")
    serial_no = cfg.get("serial_no", "")

    if not all([mch_id, app_id, private_key]):
        return {"success": False, "error": "wechatpay_not_configured"}

    out_trade_no = f"WX{int(time.time()*1000)}{uuid.uuid4().hex[:6]}"
    total_fen = int(amount_yuan * 100)

    body = json.dumps({
        "appid": app_id,
        "mchid": mch_id,
        "description": subject,
        "out_trade_no": out_trade_no,
        "notify_url": notify_url,
        "amount": {
            "total": total_fen,
            "currency": "CNY",
        },
    })

    path = "/v3/pay/transactions/native"
    timestamp = int(time.time())
    nonce = uuid.uuid4().hex[:32]
    signature = _build_signature("POST", path, timestamp, nonce, body, private_key)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f'WECHATPAY2-SHA256-RSA2048 mchid="{mch_id}",nonce_str="{nonce}",signature="{signature}",timestamp="{timestamp}",serial_no="{serial_no}"',
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{_WECHAT_API}{path}",
            content=body,
            headers=headers,
        )
    data = resp.json()

    if "code_url" in data:
        return {
            "success": True,
            "qr_code": data["code_url"],
            "out_trade_no": out_trade_no,
            "amount": total_fen,
        }
    return {
        "success": False,
        "error": data.get("message", "unknown_error"),
    }


async def query_payment(out_trade_no: str, db) -> dict:
    """Query WeChat payment status."""
    cfg = await get_wechat_config(db)
    mch_id = cfg.get("mch_id", "")
    private_key = cfg.get("private_key", "")
    serial_no = cfg.get("serial_no", "")

    if not mch_id:
        return {"success": False, "error": "not_configured"}

    path = f"/v3/pay/transactions/out-trade-no/{out_trade_no}?mchid={mch_id}"
    timestamp = int(time.time())
    nonce = uuid.uuid4().hex[:32]
    signature = _build_signature("GET", path, timestamp, nonce, "", private_key)

    headers = {
        "Accept": "application/json",
        "Authorization": f'WECHATPAY2-SHA256-RSA2048 mchid="{mch_id}",nonce_str="{nonce}",signature="{signature}",timestamp="{timestamp}",serial_no="{serial_no}"',
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{_WECHAT_API}{path}",
            headers=headers,
        )
    data = resp.json()

    if "trade_state" in data:
        state = data["trade_state"]
        return {
            "success": True,
            "trade_state": state,
            "paid": state == "SUCCESS",
            "out_trade_no": out_trade_no,
            "amount_fen": data.get("amount", {}).get("total", 0),
        }
    return {"success": False, "error": data.get("message", "unknown")}


def verify_callback(wechatpay_public_key_pem: str, headers: dict, body: str) -> bool:
    """Verify WeChat Pay callback signature."""
    try:
        timestamp = headers.get("wechatpay-timestamp", "")
        nonce = headers.get("wechatpay-nonce", "")
        signature = headers.get("wechatpay-signature", "")
        serial = headers.get("wechatpay-serial", "")

        message = f"{timestamp}\n{nonce}\n{body}\n"
        key = serialization.load_pem_public_key(
            wechatpay_public_key_pem.encode(), backend=default_backend()
        )
        import base64
        sig_bytes = base64.b64decode(signature)
        key.verify(sig_bytes, message.encode(), padding.PKCS1v15(), hashes.SHA256())
        return True
    except Exception:
        return False
