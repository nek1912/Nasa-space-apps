/* Fetch client targeting the backend API base URL. */
import { LayerInfoResponse, RecommendRotationsResponse, RegionSummary } from "../types/fieldshift";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export async function fetchRegionSummary(): Promise<RegionSummary> {
    const res = await fetch(`${API_BASE}/region-summary`);
    if (!res.ok) throw new Error(`Region summary failed: ${res.status} ${res.statusText}`);
    return (await res.json()) as RegionSummary;
}

export async function fetchLayerInfo(): Promise<LayerInfoResponse> {
    const res = await fetch(`${API_BASE}/layer-info`);
    if (!res.ok) throw new Error(`Layer info failed: ${res.status} ${res.statusText}`);
    return (await res.json()) as LayerInfoResponse;
}

export async function fetchRecommendations(): Promise<RecommendRotationsResponse> {
    const res = await fetch(`${API_BASE}/recommend-rotations`);
    if (!res.ok) throw new Error(`Recommendations failed: ${res.status} ${res.statusText}`);
    return (await res.json()) as RecommendRotationsResponse;
}