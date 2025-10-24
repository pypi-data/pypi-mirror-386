"""Collection model for pgvector MCP server."""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Collection(Base):
    """Collection model for storing collection metadata."""

    __tablename__ = "collections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    dimension = Column(Integer, nullable=False, default=1536)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship with VectorRecord
    vectors = relationship(
        "VectorRecord", back_populates="collection", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Collection(id={self.id}, name='{self.name}', dimension={self.dimension})>"
