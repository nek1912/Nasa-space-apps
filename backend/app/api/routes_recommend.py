from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api", tags=["recommend"])


@router.post("/recommend-rotations")
def recommend_rotations(request: dict):
    """Generate multi-objective crop rotation recommendations."""
    return {"rotations": [], "scores": []}