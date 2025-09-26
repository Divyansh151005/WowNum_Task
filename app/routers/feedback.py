"""Feedback collection endpoints with streaming and structured data."""

import csv
import io
import json
from typing import Iterator, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import FeedbackCorrection, IngredientAdjustment, DishTaxonomy
from app.schemas import CorrectionIn, CorrectionOut, StatsOut, HealthOut
from app.auth import verify_api_key
from app.security import limiter, get_rate_limits

router = APIRouter()
rate_limits = get_rate_limits()


@router.get("/health", response_model=HealthOut)
def health_check() -> HealthOut:
    """Health check endpoint."""
    return HealthOut(status="ok")


@router.get("/healthz", response_model=HealthOut)
def health_check_alt() -> HealthOut:
    """Alternative health check endpoint."""
    return HealthOut(status="ok")


@router.post("/correction", response_model=CorrectionOut, status_code=status.HTTP_201_CREATED)
def post_correction(
    payload: CorrectionIn,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
) -> CorrectionOut:
    """Store a user correction with optional per-ingredient adjustments."""
    
    try:
        # Create the main correction record
        correction = FeedbackCorrection(
            image_id=payload.imageId,
            original_name=payload.original.name,
            original_grams=payload.original.grams,
            corrected_name=payload.corrected.name,
            corrected_grams=payload.corrected.grams,
        )
        
        db.add(correction)
        db.flush()  # Get the ID
        
        # Add ingredient adjustments if provided
        if payload.adjustments:
            for adj in payload.adjustments:
                adjustment = IngredientAdjustment(
                    correction_id=correction.id,
                    ingredient=adj.ingredient,
                    delta_grams=adj.deltaGrams,
                    notes=adj.notes,
                )
                db.add(adjustment)
        
        db.commit()
        db.refresh(correction)
        
        # Load adjustments for response
        db.refresh(correction, ["adjustments"])
        
        return CorrectionOut(
            id=correction.id,
            imageId=correction.image_id,
            original=payload.original,
            corrected=payload.corrected,
            adjustments=[
                {
                    "ingredient": adj.ingredient,
                    "deltaGrams": adj.delta_grams,
                    "notes": adj.notes,
                }
                for adj in correction.adjustments
            ] if correction.adjustments else None,
            createdAt=correction.created_at,
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store correction: {str(e)}"
        )


@router.get("/export")
def export_feedback(
    format: str = Query("jsonl", pattern="^(csv|jsonl)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Stream all corrections in JSONL or CSV format."""
    
    try:
        # Query with eager loading of adjustments
        stmt = (
            select(FeedbackCorrection)
            .options(selectinload(FeedbackCorrection.adjustments))
            .order_by(FeedbackCorrection.id.asc())
        )
        
        if format == "jsonl":
            return StreamingResponse(
                _stream_jsonl(db, stmt),
                media_type="application/x-jsonlines",
                headers={"Content-Disposition": "attachment; filename=feedback.jsonl"}
            )
        else:
            return StreamingResponse(
                _stream_csv(db, stmt),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=feedback.csv"}
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export data: {str(e)}"
        )


def _stream_jsonl(db: Session, stmt) -> Iterator[str]:
    """Stream corrections as JSONL."""
    result = db.execute(stmt)
    
    for correction in result.scalars():
        obj = {
            "id": correction.id,
            "imageId": correction.image_id,
            "original": {
                "name": correction.original_name,
                "grams": correction.original_grams
            },
            "corrected": {
                "name": correction.corrected_name,
                "grams": correction.corrected_grams
            },
            "createdAt": correction.created_at.isoformat() + "Z"
        }
        
        if correction.adjustments:
            obj["adjustments"] = [
                {
                    "ingredient": adj.ingredient,
                    "deltaGrams": adj.delta_grams,
                    "notes": adj.notes,
                }
                for adj in correction.adjustments
            ]
        
        yield json.dumps(obj) + "\n"


def _stream_csv(db: Session, stmt) -> Iterator[str]:
    """Stream corrections as CSV."""
    # Create CSV header
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "id", "imageId", "original_name", "original_grams",
        "corrected_name", "corrected_grams", "adjustments", "createdAt"
    ])
    yield buffer.getvalue()
    buffer.close()
    
    # Stream data rows
    result = db.execute(stmt)
    
    for correction in result.scalars():
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        
        adjustments_json = ""
        if correction.adjustments:
            adjustments_data = [
                {
                    "ingredient": adj.ingredient,
                    "deltaGrams": adj.delta_grams,
                    "notes": adj.notes,
                }
                for adj in correction.adjustments
            ]
            adjustments_json = json.dumps(adjustments_data)
        
        writer.writerow([
            correction.id,
            correction.image_id,
            correction.original_name,
            correction.original_grams,
            correction.corrected_name,
            correction.corrected_grams,
            adjustments_json,
            correction.created_at.isoformat() + "Z"
        ])
        
        yield buffer.getvalue()
        buffer.close()


@router.get("/stats", response_model=StatsOut)
def feedback_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
) -> StatsOut:
    """Get top 5 corrected labels with counts."""
    
    try:
        stmt = (
            select(FeedbackCorrection.corrected_name, func.count().label("count"))
            .group_by(FeedbackCorrection.corrected_name)
            .order_by(func.count().desc(), FeedbackCorrection.corrected_name.asc())
            .limit(5)
        )
        
        results = db.execute(stmt).all()
        top5 = [{"label": name, "count": int(count)} for name, count in results]
        
        return StatsOut(top5=top5)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )