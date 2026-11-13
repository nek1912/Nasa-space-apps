from pydantic import BaseModel, Field


# Crop catalog schema
class CropInfo(BaseModel):
    name: str
    family: str
    nfix: bool = Field(description="Whether the crop fixes nitrogen")


# Hero farms schema
class HeroFarm(BaseModel):
    id: str
    location: str
    crop: str
    area_hectares: float = Field(ge=0, description="Farm area in hectares")
    soil_type: str
    yield_last_year: float = Field(ge=0, description="Yield from last season")


# Analysis request schema
class AnalyzeFieldRequest(BaseModel):
    farm_id: str
    include_uncertainty: bool = True


# Analysis response schema
class StressSignal(BaseModel):
    name: str
    severity: float = Field(ge=0, le=1, description="Normalized severity 0-1")
    description: str


class AnalyzeFieldResponse(BaseModel):
    farm_id: str
    bare_soil_window: bool
    thermal_stress: StressSignal
    evaporative_stress: StressSignal
    erosion_risk: float = Field(ge=0, le=1, description="RUSLE erosion risk 0-1")
    uncertainty: float = Field(ge=0, le=1, description="Overall uncertainty 0-1")
    recommendations: list[str] = Field(default_factory=list)


# Rotation recommendation schema
class RotationRecommendation(BaseModel):
    sequence: list[str]
    score: float = Field(ge=0, description="Multi-objective score")
    tradeoffs: dict[str, float] = Field(description="Per-criterion tradeoff values")


class RecommendRotationsResponse(BaseModel):
    farm_id: str
    baseline_rotation: list[str]
    optimized_rotations: list[list[str]]
    scores: list[float]