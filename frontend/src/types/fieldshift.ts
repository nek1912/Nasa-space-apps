/* Exact TS mirror of backend/app/schemas.py */
export interface CropInfo {
    name: string;
    family: string;
    nfix: boolean;
}

export interface HeroFarm {
    id: string;
    location: string;
    crop: string;
    area_hectares: number;
    soil_type: string;
    yield_last_year: number;
}

export interface StressSignal {
    name: string;
    severity: number;
    description: string;
}

export interface AnalyzeFieldResponse {
    farm_id: string;
    bare_soil_window: boolean;
    thermal_stress: StressSignal;
    evaporative_stress: StressSignal;
    erosion_risk: number;
    uncertainty: number;
    recommendations: string[];
}

export interface RotationRecommendation {
    sequence: string[];
    score: number;
    tradeoffs: Record<string, number>;
}

export interface RecommendRotationsResponse {
    farm_id: string;
    baseline_rotation: string[];
    optimized_rotations: string[][];
    scores: number[];
}