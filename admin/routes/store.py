import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, Query
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
