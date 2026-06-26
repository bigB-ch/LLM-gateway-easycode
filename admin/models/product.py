import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, BigInteger, DateTime, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from database import Base
import enum


def utcnow():
    return datetime.now(timezone.utc)


class ProductCategory(str, enum.Enum):
    AGENT = "agent"
    DEV_TOOL = "dev_tool"
    ENV_PACK = "env_pack"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[ProductCategory] = mapped_column(SAEnum(ProductCategory), nullable=False, default=ProductCategory.AGENT)
    price: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="price in cents")
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="server path to download file")
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="file size in bytes")
    version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    system_requirements: Mapped[str | None] = mapped_column(String(256), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    screenshots: Mapped[str | None] = mapped_column(Text, nullable=True, comment="JSON array of screenshot URLs")
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
