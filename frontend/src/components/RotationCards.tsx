/* Rotation strategy cards — displays 4 MCDA-scored strategies with explainability. */
import React from "react";
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from "recharts";
import { RotationStrategy } from "../types/fieldshift";

const SCORE_AXES = [
    { name: "water_efficiency", label: "Water Efficiency" },
    { name: "soil_health", label: "Soil Health" },
    { name: "erosion_armor", label: "Erosion Armor" },
    { name: "pest_disruption", label: "Pest Disruption" },
    { name: "climate_resilience", label: "Climate Resilience" },
    { name: "market_return", label: "Market Return" },
];

const strategyColors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"];

interface Props {
    strategies: RotationStrategy[];
}

export const RotationCards: React.FC<Props> = ({ strategies }) => {
    if (!strategies.length) {
        return (
            <div style={{ padding: "1rem", background: "#f8f9fa", marginBottom: "1rem" }}>
                <h3>Rotation Recommendations</h3>
                <p>No rotation strategies available.</p>
            </div>
        );
    }

    return (
        <div style={{ marginBottom: "1rem" }}>
            <h3 style={{ marginBottom: "0.75rem" }}>Rotation Strategies</h3>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem" }}>
                {strategies.map((strategy, idx) => (
                    <RotationCard key={strategy.strategy_id} strategy={strategy} index={idx} color={strategyColors[idx % strategyColors.length]} />
                ))}
            </div>
        </div>
    );
};

interface RotationCardProps {
    strategy: RotationStrategy;
    index: number;
    color: string;
}

const RotationCard: React.FC<RotationCardProps> = ({ strategy, index, color }) => {
    const radarData = SCORE_AXES.map((a) => ({
        name: a.label,
        value: strategy.scores[a.name] ?? 0,
    }));

    const isBaseline = strategy.is_baseline;
    return (
        <div
            style={{
                width: "280px",
                border: `2px solid ${isBaseline ? "#3b82f6" : "#e2e8f0"}`,
                borderRadius: "8px",
                padding: "1rem",
                background: isBaseline ? "#eff6ff" : "#ffffff",
                boxShadow: isBaseline ? "0 4px 6px -1px rgba(59, 130, 246, 0.3)" : "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
            }}
        >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                <div style={{ fontWeight: "700", fontSize: "1.1rem" }}>{strategy.name}</div>
                <div style={{ fontWeight: "700", fontSize: "1.25rem", color: color }}>{strategy.overall_score}</div>
            </div>
            <div style={{ fontSize: "0.85rem", color: "#64748b", marginBottom: "0.5rem" }}>{strategy.description}</div>
            <div style={{ fontSize: "0.75rem", fontWeight: "600", marginBottom: "0.25rem", color: isBaseline ? "#1e40af" : "#334155" }}>
                {isBaseline ? "Baseline — " : "Alternative — "}{strategy.strategy_id}
            </div>
            <div style={{ height: "140px", width: "100%" }}>
                <ResponsiveContainer width="100%" height={140}>
                    <RadarChart data={radarData}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="name" tick={{ fontSize: 10 }} />
                        <PolarRadiusAxis tick={{ fontSize: 10 }} />
                        <Radar name="value" stroke={color} fill={color} fillOpacity={0.3} points={{ r: 2 }} />
                        <Tooltip content={({ active, payload }: any) => {
                            if (active && payload && payload.length) {
                                const item = payload[0].payload;
                                return (
                                    <div style={{ padding: "4px 8px", background: "#fff", border: "1px solid #ccc" }}>
                                        <div style={{ fontWeight: "600" }}>{item.name}</div>
                                        <div>{item.value.toFixed(0)}</div>
                                    </div>
                                );
                            }
                            return null;
                        }} />
                    </RadarChart>
                </ResponsiveContainer>
            </div>
            <div style={{ marginTop: "0.5rem", fontSize: "0.8rem", color: "#475569" }}>{strategy.why_suggested}</div>
            <div style={{ marginTop: "0.25rem", fontSize: "0.75rem", color: "#64748b" }}>
                <strong>Evidence:</strong> {strategy.nasa_evidence}
            </div>
        </div>
    );
};