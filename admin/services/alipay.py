"""
Alipay F2F (Face-to-Face) payment integration.
Uses RSA2 signing with cryptography library.

Required Alipay merchant account with 当面付 (F2F) enabled.
Credentials stored in system_config table.
"""
import json
import time
import uuid
import base64
from base64 import b64encode
from urllib.parse import urlencode, quote_plus

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

_ALIPAY_GATEWAY = "https://openapi.alipay.com/gateway.do"


async def get_alipay_config(db):
    """Load Alipay config from system_config table."""
    from sqlalchemy import select
    from models.system_config import SystemConfig
    result = await db.execute(select(SystemConfig).where(SystemConfig.key == "payment_config"))
    cfg = result.scalar_one_or_none()
    if cfg and cfg.value:
        return cfg.value
    return {}


def _sign(data: str, private_key_pem: str) -> str:
    """RSA2-SHA256 sign the data string."""
    key = serialization.load_pem_private_key(
        private_key_pem.encode(), password=None, backend=default_backend()
    )
    signature = key.sign(data.encode(), padding.PKCS1v15(), hashes.SHA256())
    return b64encode(signature).decode()


async def create_qr_payment(
    amount_yuan: float,
    subject: str,
    notify_url: str,
    db,
) -> dict:
    """
    Create an Alipay precreate order and return QR code data.
    Returns {"success": True, "qr_code": "https://...", "out_trade_no": "..."}
    """
    cfg = await get_alipay_config(db)
    app_id = cfg.get("app_id", "")
    private_key = cfg.get("private_key", "")

    if not app_id or not private_key:
        return {"success": False, "error": "alipay_not_configured"}

    out_trade_no = f"PAY{int(time.time()*1000)}{uuid.uuid4().hex[:6]}"
    total_amount = f"{amount_yuan:.2f}"

    biz_content = json.dumps({
        "out_trade_no": out_trade_no,
        "total_amount": total_amount,
        "subject": subject,
        "timeout_express": "15m",
    })

    params = {
        "app_id": app_id,
        "method": "alipay.trade.precreate",
        "charset": "utf-8",
        "sign_type": "RSA2",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "version": "1.0",
        "notify_url": notify_url,
        "biz_content": biz_content,
    }

    # Build query string for signing
    sorted_items = sorted(params.items())
    sign_str = "&".join(f"{k}={v}" for k, v in sorted_items)
    params["sign"] = _sign(sign_str, private_key)

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            _ALIPAY_GATEWAY,
            data=urlencode(params),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    resp_data = resp.json()
    alipay_resp = resp_data.get("alipay_trade_precreate_response", {})

    if alipay_resp.get("code") == "10000":
        return {
            "success": True,
            "qr_code": alipay_resp.get("qr_code", ""),
            "out_trade_no": out_trade_no,
            "amount": total_amount,
        }
    return {
        "success": False,
        "error": alipay_resp.get("sub_msg", alipay_resp.get("msg", "unknown_error")),
        "out_trade_no": out_trade_no,
    }


async def create_page_payment(
    amount_yuan: float,
    subject: str,
    return_url: str,
    notify_url: str,
    db,
) -> dict:
    """
    Create an Alipay Computer Website Payment order (alipay.trade.page.pay).
    Returns a redirect URL for the Alipay payment page.
    """
    cfg = await get_alipay_config(db)
    app_id = cfg.get("app_id", "")
    private_key = cfg.get("private_key", "")

    if not app_id or not private_key:
        return {"success": False, "error": "alipay_not_configured"}

    out_trade_no = f"PAY{int(time.time()*1000)}{uuid.uuid4().hex[:6]}"
    total_amount = f"{amount_yuan:.2f}"

    biz_content = json.dumps({
        "out_trade_no": out_trade_no,
        "total_amount": total_amount,
        "subject": subject,
        "product_code": "FAST_INSTANT_TRADE_PAY",
    })

    params = {
        "app_id": app_id,
        "method": "alipay.trade.page.pay",
        "charset": "utf-8",
        "sign_type": "RSA2",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "version": "1.0",
        "return_url": return_url,
        "notify_url": notify_url,
        "biz_content": biz_content,
    }

    sorted_items = sorted(params.items())
    sign_str = "&".join(f"{k}={v}" for k, v in sorted_items)
    params["sign"] = _sign(sign_str, private_key)

    redirect_url = _ALIPAY_GATEWAY + "?" + urlencode(params)

    return {
        "success": True,
        "redirect_url": redirect_url,
        "out_trade_no": out_trade_no,
        "amount": total_amount,
    }


async def query_payment(out_trade_no: str, db) -> dict:
    """Query Alipay payment status."""
    cfg = await get_alipay_config(db)
    app_id = cfg.get("app_id", "")
    private_key = cfg.get("private_key", "")

    if not app_id or not private_key:
        return {"success": False, "error": "alipay_not_configured"}

    biz_content = json.dumps({"out_trade_no": out_trade_no})
    params = {
        "app_id": app_id,
        "method": "alipay.trade.query",
        "charset": "utf-8",
        "sign_type": "RSA2",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "version": "1.0",
        "biz_content": biz_content,
    }
    sorted_items = sorted(params.items())
    sign_str = "&".join(f"{k}={v}" for k, v in sorted_items)
    params["sign"] = _sign(sign_str, private_key)

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            _ALIPAY_GATEWAY,
            data=urlencode(params),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    resp_data = resp.json()
    alipay_resp = resp_data.get("alipay_trade_query_response", {})

    if alipay_resp.get("code") == "10000":
        trade_status = alipay_resp.get("trade_status", "")
        return {
            "success": True,
            "trade_status": trade_status,
            "paid": trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED"),
            "out_trade_no": out_trade_no,
            "total_amount": alipay_resp.get("total_amount", "0"),
        }
    return {"success": False, "error": alipay_resp.get("sub_msg", "unknown")}


def verify_callback_sign(params: dict, alipay_public_key_pem: str) -> bool:
    """Verify Alipay callback signature."""
    sign = params.pop("sign", "")
    sign_type = params.pop("sign_type", "RSA2")
    sorted_items = sorted(params.items())
    sign_str = "&".join(f"{k}={v}" for k, v in sorted_items)

    try:
        key = serialization.load_pem_public_key(
            alipay_public_key_pem.encode(), backend=default_backend()
        )
        signature = base64.b64decode(sign)
        key.verify(signature, sign_str.encode(), padding.PKCS1v15(), hashes.SHA256())
        return True
    except Exception:
        return False
