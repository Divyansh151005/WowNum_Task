"""SQLAlchemy models for the feedback collector."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.sqlite import JSON

Base = declarative_base()


class FeedbackCorrection(Base):
    """Main feedback correction record."""
    
    __tablename__ = "feedback_corrections"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(String(200), index=True, nullable=False)
    original_name = Column(String(200), nullable=False)
    original_grams = Column(Integer, nullable=False)
    corrected_name = Column(String(200), index=True, nullable=False)
    corrected_grams = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    adjustments = relationship("IngredientAdjustment", back_populates="correction", cascade="all, delete-orphan")


class IngredientAdjustment(Base):
    """Structured ingredient adjustments for corrections."""
    
    __tablename__ = "ingredient_adjustments"
    
    id = Column(Integer, primary_key=True, index=True)
    correction_id = Column(Integer, ForeignKey("feedback_corrections.id"), nullable=False, index=True)
    ingredient = Column(String(100), nullable=False)
    delta_grams = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Relationships
    correction = relationship("FeedbackCorrection", back_populates="adjustments")
    
    # Indexes
    __table_args__ = (
        Index("ix_ingredient_adjustments_correction_ingredient", "correction_id", "ingredient"),
    )


class DishTaxonomy(Base):
    """Dish taxonomy for name aliasing and validation."""
    
    __tablename__ = "dish_taxonomy"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    aliases = Column(JSON, nullable=False, default=list)
    ingredients = Column(JSON, nullable=False, default=list)
    macros_per_100g = Column(JSON, nullable=False)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index("ix_dish_taxonomy_name", "name"),
        Index("ix_dish_taxonomy_active", "is_active"),
    )
