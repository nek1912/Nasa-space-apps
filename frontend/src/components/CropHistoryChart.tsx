/* Annual CDL crop statistics for Story County. */
import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { CropYear } from "../types/fieldshift";

interface Props {
    crops: CropYear[];
}

export const CropHistoryChart: React.FC<Props> = ({ crops }) => {
    if (!crops.length) {
        return (
            <div style={{ padding: "1rem", background: "#f8f9fa", marginBottom: "1rem" }}>
                <h3>Crop history</h3>
                <p>No CDL crop statistics available.</p>
            </div>
        );
    }

    const series = crops.map((y) => ({
        name: String(y.year),
        value: y.classified_acres ?? 0,
    }));

    return (
        <div style={{ padding: "1rem", background: "#f8f9fa", marginBottom: "1rem" }}>
            <h3>Crop history — USDA NASS CDL county statistics</h3>
            <p style={{ margin: "0 0 0.5rem 0", fontSize: "0.85rem", color: "#666" }}>
                Classified acres per crop year as reported by USDA NASS Cropland Data Layer.
            </p>
            <ResponsiveContainer width="100%" height={260}>
                <BarChart data={series}>
                    <XAxis dataKey="name" label={{ value: "Crop year", position: "insideBottom" }} />
                    <YAxis label={{ value: "Classified acres", angle: -90, position: "insideLeft" }} />
                    <Tooltip />
                    <Bar dataKey="value" fill="#4ade80" />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
};