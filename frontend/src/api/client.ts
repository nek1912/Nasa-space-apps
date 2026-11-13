/* Fetch client targeting http://localhost:8000/api */
import { AnalyzeFieldResponse, RotationRecommendation } from "../types/fieldshift";

const API_BASE = "http://localhost:8000/api";

export async function getHeroFarms() {
    const res = await fetch(`${API_BASE}/hero-farms`);
    if (!res.ok) throw new Error("Failed to fetch hero farms");
    return res.json();
}

export async function analyzeField(farmId: string, includeUncertainty = true) {
    const res = await fetch(`${API_BASE}/analyze-field`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({farm_id: farmId, include_uncertainty: includeUncertainty}),
    });
    if (!res.ok) throw new Error("Analysis failed");
    return res.json() as Promise<AnalyzeFieldResponse>;
}

export async function recommendRotations(farmId: string) {
    const res = await fetch(`${API_BASE}/recommend-rotations`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({farmId}),
    });
    if (!res.ok) throw new Error("Recommendations failed");
    return res.json() as Promise<RotationRecommendation[]>;
}