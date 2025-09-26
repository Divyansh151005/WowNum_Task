"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, ConfigDict, validator


class DishPortion(BaseModel):
    """Dish portion with name and weight."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Dish name")
    grams: int = Field(..., ge=1, le=10000, description="Weight in grams")


class IngredientAdjustmentIn(BaseModel):
    """Ingredient adjustment input."""
    
    ingredient: str = Field(..., min_length=1, max_length=100, description="Ingredient name")
    deltaGrams: int = Field(..., description="Change in grams (positive or negative)")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")


class CorrectionIn(BaseModel):
    """Feedback correction input."""
    
    model_config = ConfigDict(extra="forbid")

    imageId: str = Field(..., min_length=1, max_length=200)
    original: DishPortion
    corrected: DishPortion
    adjustments: Optional[List[IngredientAdjustmentIn]] = Field(
        default=None,
        description="Optional per-ingredient adjustments",
    )


class IngredientAdjustmentOut(BaseModel):
    """Ingredient adjustment output."""
    
    ingredient: str
    deltaGrams: int
    notes: Optional[str] = None


class CorrectionOut(BaseModel):
    """Feedback correction output."""
    
    id: int
    imageId: str
    original: DishPortion
    corrected: DishPortion
    adjustments: Optional[List[IngredientAdjustmentOut]] = None
    createdAt: datetime


class StatsOut(BaseModel):
    """Statistics output."""
    
    top5: List[Dict[str, Any]]


class HealthOut(BaseModel):
    """Health check output."""
    
    status: str
