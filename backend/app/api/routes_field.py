from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api", tags=["field"])


@router.get("/hero-farms")
def get_hero_farms():
    """Return the three pre-harmonized 3-decade cubes."""
    return {"farms": []}


@router.post("/analyze-field")
def analyze_field(request: dict):
    """Run SI diagnostics on a field given farm ID and parameters."""
    return {"signals": []}