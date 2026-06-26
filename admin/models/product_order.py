import uuid
from datetime import datetime, timezone
from sqlalchemy import String, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from database import Base


def utcnow():
    return datetime.now(timezone.utc)


class ProductOrder(Base):
    __tablename__ = "product_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="price in cents")
    method: Mapped[str] = mapped_column(String(32), nullable=False, comment="alipay/wechat")
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False, comment="pending/paid/expired")
    out_trade_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    qr_code: Mapped[str | None] = mapped_column(String, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
