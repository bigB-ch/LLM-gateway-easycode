import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.product import Product, ProductCategory
from models.product_order import ProductOrder
from models.download import Download
from dependencies import get_current_user, require_admin

router = APIRouter(prefix="/admin/api/store", tags=["store"])


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    category: str = "agent"
    price: float
    file_path: str | None = None
    file_size: int | None = None
    version: str | None = None
    system_requirements: str | None = None
    thumbnail_url: str | None = None
    screenshots: list[str] | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    price: float | None = None
    file_path: str | None = None
    file_size: int | None = None
    version: str | None = None
    system_requirements: str | None = None
    thumbnail_url: str | None = None
    screenshots: list[str] | None = None
    status: str | None = None


def _product_to_dict(p: Product) -> dict:
    screenshots = []
    if p.screenshots:
        try:
            screenshots = json.loads(p.screenshots)
        except (json.JSONDecodeError, TypeError):
            screenshots = []
    return {
        "id": str(p.id),
        "name": p.name,
        "description": p.description,
        "category": p.category.value if isinstance(p.category, ProductCategory) else p.category,
        "price": p.price,
        "price_yuan": round(p.price / 100, 2),
        "file_path": p.file_path,
        "file_size": p.file_size,
        "version": p.version,
        "system_requirements": p.system_requirements,
        "thumbnail_url": p.thumbnail_url,
        "screenshots": screenshots,
        "status": p.status,
        "sort_order": p.sort_order,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }


# ── Admin APIs ──

@router.get("/admin/products")
async def admin_list_products(
    category: str | None = Query(None),
    status: str | None = Query(None),
    _admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(Product).order_by(Product.sort_order.asc(), Product.created_at.desc())
    if category:
        query = query.where(Product.category == category)
    if status:
        query = query.where(Product.status == status)
    result = await db.execute(query)
    products = result.scalars().all()
    return {"items": [_product_to_dict(p) for p in products]}


@router.post("/admin/products")
async def admin_create_product(
    req: ProductCreate,
    _admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        category = ProductCategory(req.category)
    except ValueError:
        raise HTTPException(status_code=400, detail={"error": "invalid_category"})

    product = Product(
        id=uuid.uuid4(),
        name=req.name,
        description=req.description,
        category=category,
        price=int(req.price * 100),
        file_path=req.file_path,
        file_size=req.file_size,
        version=req.version,
        system_requirements=req.system_requirements,
        thumbnail_url=req.thumbnail_url,
        screenshots=json.dumps(req.screenshots or []),
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return _product_to_dict(product)


@router.put("/admin/products/{product_id}")
async def admin_update_product(
    product_id: str,
    req: ProductUpdate,
    _admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail={"error": "product_not_found"})

    update_data = req.model_dump(exclude_none=True)
    if "category" in update_data:
        try:
            update_data["category"] = ProductCategory(update_data["category"])
        except ValueError:
            raise HTTPException(status_code=400, detail={"error": "invalid_category"})
    if "price" in update_data:
        update_data["price"] = int(update_data["price"] * 100)
    if "screenshots" in update_data:
        update_data["screenshots"] = json.dumps(update_data["screenshots"])

    for field, value in update_data.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)
    return _product_to_dict(product)


@router.delete("/admin/products/{product_id}")
async def admin_delete_product(
    product_id: str,
    _admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail={"error": "product_not_found"})
    await db.delete(product)
    await db.commit()
    return {"message": "deleted"}


# ── User-facing APIs ──

@router.get("/products")
async def list_products(
    category: str | None = Query(None),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Product).where(Product.status == "active").order_by(Product.sort_order.asc(), Product.created_at.desc())
    if category:
        query = query.where(Product.category == category)
    result = await db.execute(query)
    products = result.scalars().all()
    return {"items": [_product_to_dict(p) for p in products]}


@router.get("/products/{product_id}")
async def get_product(
    product_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id, Product.status == "active"))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail={"error": "product_not_found"})

    # Check if user has purchased this product
    order_result = await db.execute(
        select(ProductOrder).where(
            ProductOrder.user_id == user["user_id"],
            ProductOrder.product_id == product_id,
            ProductOrder.status == "paid",
        )
    )
    purchased = order_result.scalar_one_or_none() is not None

    data = _product_to_dict(product)
    data["purchased"] = purchased
    return data


# ── Order & Payment ──


class CreateOrderRequest(BaseModel):
    product_id: str
    method: str = "alipay"


@router.post("/orders")
async def create_order(
    req: CreateOrderRequest,
    request: Request,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an order and redirect to Alipay for payment."""
    result = await db.execute(
        select(Product).where(Product.id == req.product_id, Product.status == "active")
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail={"error": "product_not_found"})

    if req.method == "alipay":
        from services.alipay import create_page_payment
        amount_yuan = product.price / 100

        order = ProductOrder(
            id=uuid.uuid4(),
            user_id=user["user_id"],
            product_id=product.id,
            amount=product.price,
            method="alipay",
            status="pending",
        )
        db.add(order)
        await db.flush()

        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        host = request.url.hostname
        port = request.url.port
        server_base = f"{scheme}://{host}" + (f":{port}" if port else "")
        from urllib.parse import quote
        store_return = f"{server_base}/admin/api/store/alipay/return?order_id={order.id}&frontend_url={quote(server_base + '/orders')}"
        notify_url = f"{server_base}/admin/api/store/alipay/notify"

        pay_result = await create_page_payment(
            amount_yuan=amount_yuan,
            subject=f"购买 {product.name}",
            return_url=store_return,
            notify_url=notify_url,
            db=db,
        )
        if not pay_result.get("success"):
            await db.rollback()
            raise HTTPException(status_code=400, detail={"error": pay_result.get("error", "payment_failed")})

        order.out_trade_no = pay_result.get("out_trade_no")
        await db.commit()

        return {
            "order_id": str(order.id),
            "redirect_url": pay_result["redirect_url"],
            "out_trade_no": pay_result["out_trade_no"],
            "amount_yuan": amount_yuan,
            "status": "pending",
        }
    else:
        raise HTTPException(status_code=400, detail={"error": "unsupported_payment_method"})


@router.post("/orders/{order_id}/query")
async def query_order_payment(
    order_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query payment status and auto-confirm if paid."""
    result = await db.execute(
        select(ProductOrder).where(
            ProductOrder.id == order_id,
            ProductOrder.user_id == user["user_id"],
        )
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail={"error": "order_not_found"})

    if order.status == "paid":
        return {"paid": True, "status": "paid"}

    if order.method == "alipay" and order.out_trade_no:
        from services.alipay import query_payment
        pay_result = await query_payment(order.out_trade_no, db)
        if pay_result.get("success") and pay_result.get("paid"):
            order.status = "paid"
            from datetime import datetime, timezone
            order.paid_at = datetime.now(timezone.utc)

            # Create download record
            download = Download(
                id=uuid.uuid4(),
                order_id=order.id,
                user_id=user["user_id"],
                product_id=order.product_id,
            )
            db.add(download)
            await db.commit()
            return {"paid": True, "status": "paid"}

    return {"paid": False, "status": order.status}


@router.get("/orders")
async def list_orders(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List current user's product orders."""
    result = await db.execute(
        select(ProductOrder)
        .where(ProductOrder.user_id == user["user_id"])
        .order_by(ProductOrder.created_at.desc())
        .limit(50)
    )
    orders = result.scalars().all()

    items = []
    for o in orders:
        prod_result = await db.execute(select(Product).where(Product.id == o.product_id))
        product = prod_result.scalar_one_or_none()
        items.append({
            "id": str(o.id),
            "product_id": str(o.product_id),
            "product_name": product.name if product else "deleted",
            "product_thumbnail": product.thumbnail_url if product else None,
            "amount": o.amount,
            "amount_yuan": round(o.amount / 100, 2),
            "method": o.method,
            "status": o.status,
            "paid_at": o.paid_at.isoformat() if o.paid_at else None,
            "created_at": o.created_at.isoformat(),
        })
    return {"items": items}



# ── Store Alipay Payment Callbacks ──


@router.get("/alipay/return")
async def store_alipay_return(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle Alipay return redirect after store purchase."""
    from urllib.parse import unquote
    import json as _json

    params = dict(request.query_params)
    order_id = params.pop("order_id", "")
    frontend_url = unquote(params.pop("frontend_url", "/"))

    from services.alipay import get_alipay_config, verify_callback_sign
    cfg = await get_alipay_config(db)
    alipay_public_key = cfg.get("alipay_public_key", "")

    if alipay_public_key:
        if not verify_callback_sign(params.copy(), alipay_public_key):
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=f"{frontend_url}?payment=fail&reason=verify_failed")

    out_trade_no = params.get("out_trade_no", "")
    payment_status = "pending"

    if out_trade_no:
        from services.alipay import query_payment
        try:
            pay_result = await query_payment(out_trade_no, db)
            if pay_result.get("paid"):
                # Update order status
                order_result = await db.execute(
                    select(ProductOrder).where(ProductOrder.out_trade_no == out_trade_no)
                )
                order = order_result.scalar_one_or_none()
                if order and order.status == "pending":
                    order.status = "paid"
                    from datetime import datetime, timezone
                    order.paid_at = datetime.now(timezone.utc)
                    # Create download record
                    download = Download(
                        id=uuid.uuid4(),
                        order_id=order.id,
                        user_id=order.user_id,
                        product_id=order.product_id,
                    )
                    db.add(download)
                    await db.commit()
                payment_status = "success"
        except Exception:
            pass

    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"{frontend_url}?payment={payment_status}&out_trade_no={out_trade_no}")


@router.post("/alipay/notify")
async def store_alipay_notify(request: Request):
    """Alipay async notification for store purchases."""
    from database import async_session as _session
    async with _session() as db:
        body = await request.body()
        from urllib.parse import parse_qs
        params = {k: v[0] for k, v in parse_qs(body.decode()).items()}

        from services.alipay import get_alipay_config, verify_callback_sign
        cfg = await get_alipay_config(db)
        alipay_public_key = cfg.get("alipay_public_key", "")
        if not alipay_public_key or not verify_callback_sign(params.copy(), alipay_public_key):
            return "fail"

        trade_status = params.get("trade_status", "")
        out_trade_no = params.get("out_trade_no", "")

        if trade_status == "TRADE_SUCCESS" and out_trade_no:
            order_result = await db.execute(
                select(ProductOrder).where(
                    ProductOrder.out_trade_no == out_trade_no,
                    ProductOrder.status == "pending",
                )
            )
            order = order_result.scalar_one_or_none()
            if order:
                order.status = "paid"
                from datetime import datetime, timezone
                order.paid_at = datetime.now(timezone.utc)
                download = Download(
                    id=uuid.uuid4(),
                    order_id=order.id,
                    user_id=order.user_id,
                    product_id=order.product_id,
                )
                db.add(download)
                await db.commit()
    return "success"


# ── Download ──


@router.get("/orders/{order_id}/download")
async def request_download(
    order_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a signed download URL for a purchased product."""
    result = await db.execute(
        select(ProductOrder).where(
            ProductOrder.id == order_id,
            ProductOrder.user_id == user["user_id"],
            ProductOrder.status == "paid",
        )
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail={"error": "order_not_found_or_not_paid"})

    prod_result = await db.execute(select(Product).where(Product.id == order.product_id))
    product = prod_result.scalar_one_or_none()
    if product is None or not product.file_path:
        raise HTTPException(status_code=404, detail={"error": "file_not_found"})

    import os
    if not os.path.isfile(product.file_path):
        raise HTTPException(status_code=404, detail={"error": "file_not_found_on_server"})

    # Update download count
    dl_result = await db.execute(
        select(Download).where(Download.order_id == order_id)
    )
    download_record = dl_result.scalar_one_or_none()
    if download_record:
        download_record.download_count += 1
        from datetime import datetime, timezone
        download_record.last_download_at = datetime.now(timezone.utc)
        await db.commit()

    # Generate a short-lived token for file download
    from jwt_utils import create_download_token
    download_token = create_download_token(
        user_id=user["user_id"],
        order_id=order_id,
        expires_seconds=300,
    )

    return {
        "download_url": f"/admin/api/store/download/file/{order_id}?token={download_token}",
        "filename": os.path.basename(product.file_path),
        "file_size": product.file_size,
    }


@router.get("/download/file/{order_id}")
async def serve_file(
    order_id: str,
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Serve the actual file with token verification."""
    from jwt_utils import decode_token
    import os
    try:
        payload = decode_token(token)
        if payload.get("purpose") != "download" or payload.get("order_id") != order_id:
            raise HTTPException(status_code=403, detail={"error": "invalid_token"})
    except Exception:
        raise HTTPException(status_code=403, detail={"error": "invalid_or_expired_token"})

    from fastapi.responses import FileResponse
    result = await db.execute(
        select(ProductOrder).where(
            ProductOrder.id == order_id,
            ProductOrder.user_id == payload["sub"],
            ProductOrder.status == "paid",
        )
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail={"error": "order_not_found"})

    prod_result = await db.execute(select(Product).where(Product.id == order.product_id))
    product = prod_result.scalar_one_or_none()
    if product is None or not product.file_path:
        raise HTTPException(status_code=404, detail={"error": "file_not_found"})

    return FileResponse(
        path=product.file_path,
        filename=os.path.basename(product.file_path),
        media_type="application/octet-stream",
    )
