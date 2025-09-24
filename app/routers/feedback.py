from __future__ import annotations

from datetime import datetime
from typing import Iterable, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import Column, DateTime, Integer, String, create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from pydantic import BaseModel, Field, ConfigDict
import csv
import io
import os
import json


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./feedback.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class FeedbackCorrection(Base):
    __tablename__ = "feedback_corrections"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(String, index=True, nullable=False)
    original_name = Column(String, nullable=False)
    original_grams = Column(Integer, nullable=False)
    corrected_name = Column(String, index=True, nullable=False)
    corrected_grams = Column(Integer, nullable=False)
    # Optional per-ingredient adjustments, stored as JSON string
    adjustments_json = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    # Lightweight migration: add adjustments_json if missing
    with engine.connect() as conn:
        cols = conn.exec_driver_sql("PRAGMA table_info(feedback_corrections)").fetchall()
        col_names = {c[1] for c in cols}
        if "adjustments_json" not in col_names:
            conn.exec_driver_sql(
                "ALTER TABLE feedback_corrections ADD COLUMN adjustments_json TEXT"
            )
            conn.commit()


def get_db() -> Iterable[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DishPortion(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    grams: int = Field(..., ge=1, le=10000)


class CorrectionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    imageId: str = Field(..., min_length=1, max_length=200)
    original: DishPortion
    corrected: DishPortion
    adjustments: Optional[list[dict]] = Field(
        default=None,
        description="Optional list of per-ingredient adjustments, e.g., [{ingredient, deltaGrams}]",
    )


class ExportFormat(BaseModel):
    fmt: Literal["csv", "jsonl"] = Field(default="jsonl")


router = APIRouter()


@router.post("/correction", status_code=201)
def post_correction(payload: CorrectionIn, db: Session = Depends(get_db)) -> JSONResponse:
    rec = FeedbackCorrection(
        image_id=payload.imageId,
        original_name=payload.original.name,
        original_grams=payload.original.grams,
        corrected_name=payload.corrected.name,
        corrected_grams=payload.corrected.grams,
        adjustments_json=json.dumps(payload.adjustments) if payload.adjustments is not None else None,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return JSONResponse(
        status_code=201,
        content={
            "id": rec.id,
            "imageId": rec.image_id,
            "original": {"name": rec.original_name, "grams": rec.original_grams},
            "corrected": {"name": rec.corrected_name, "grams": rec.corrected_grams},
            **({"adjustments": json.loads(rec.adjustments_json)} if rec.adjustments_json else {}),
            "createdAt": rec.created_at.isoformat() + "Z",
        },
    )


@router.get("/export")
def export_feedback(
    format: str = Query("jsonl", pattern="^(csv|jsonl)$"),
    db: Session = Depends(get_db),
):
    stmt = select(FeedbackCorrection).order_by(FeedbackCorrection.id.asc())
    rows = list(db.scalars(stmt))

    if format == "jsonl":
        def iter_jsonl():
            for r in rows:
                obj = {
                    "id": r.id,
                    "imageId": r.image_id,
                    "original": {"name": r.original_name, "grams": r.original_grams},
                    "corrected": {"name": r.corrected_name, "grams": r.corrected_grams},
                    "createdAt": r.created_at.isoformat() + "Z",
                }
                if r.adjustments_json:
                    try:
                        obj["adjustments"] = json.loads(r.adjustments_json)
                    except Exception:
                        obj["adjustments"] = r.adjustments_json
                yield json.dumps(obj) + "\n"

        return StreamingResponse(iter_jsonl(), media_type="application/x-jsonlines")

    # CSV
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "imageId",
            "original_name",
            "original_grams",
            "corrected_name",
            "corrected_grams",
            "adjustments",
            "createdAt",
        ]
    )
    for r in rows:
        writer.writerow(
            [
                r.id,
                r.image_id,
                r.original_name,
                r.original_grams,
                r.corrected_name,
                r.corrected_grams,
                r.adjustments_json or "",
                r.created_at.isoformat() + "Z",
            ]
        )
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="text/csv")


@router.get("/stats")
def feedback_stats(db: Session = Depends(get_db)) -> dict[str, list[dict[str, int | str]]]:
    stmt = (
        select(FeedbackCorrection.corrected_name, func.count().label("count"))
        .group_by(FeedbackCorrection.corrected_name)
        .order_by(func.count().desc(), FeedbackCorrection.corrected_name.asc())
        .limit(5)
    )
    results = db.execute(stmt).all()
    top = [{"label": name, "count": int(count)} for name, count in results]
    return {"top5": top}


