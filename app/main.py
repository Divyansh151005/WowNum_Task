"""FastAPI application factory with security and database initialization."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.routers import feedback
from app.database import engine
from app.models import Base
from app.security import setup_security


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting up...")
    
    # Create tables if they don't exist (for development)
    if os.getenv("CREATE_TABLES", "true").lower() == "true":
        Base.metadata.create_all(bind=engine)
        print("Database tables created/verified")
    
    # Load taxonomy data if needed
    await load_taxonomy_data()
    
    yield
    
    # Shutdown
    print("Shutting down...")


async def load_taxonomy_data():
    """Load taxonomy data from JSON file into database."""
    try:
        import json
        from app.database import get_db_session
        from app.models import DishTaxonomy
        
        taxonomy_file = "data/taxonomy.json"
        if not os.path.exists(taxonomy_file):
            print(f"Taxonomy file {taxonomy_file} not found, skipping...")
            return
        
        with open(taxonomy_file, "r") as f:
            data = json.load(f)
        
        db = get_db_session()
        try:
            # Check if data already exists
            existing = db.query(DishTaxonomy).first()
            if existing:
                print("Taxonomy data already loaded")
                return
            
            # Load dishes
            for dish_data in data.get("dishes", []):
                dish = DishTaxonomy(
                    id=dish_data["id"],
                    name=dish_data["name"],
                    aliases=dish_data.get("aliases", []),
                    ingredients=dish_data.get("ingredients", []),
                    macros_per_100g=dish_data.get("macros_per_100g", {}),
                )
                db.add(dish)
            
            db.commit()
            print(f"Loaded {len(data.get('dishes', []))} dishes into taxonomy")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"Failed to load taxonomy data: {e}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="WowNom Feedback Collector",
        description="Production-ready feedback collection for food detection/classification",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # Setup security middleware
    setup_security(app)
    
    # Include routers
    app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])
    
    # Add root health check for backward compatibility
    @app.get("/healthz")
    def root_health() -> dict[str, str]:
        return {"status": "ok"}
    
    return app


app = create_app()