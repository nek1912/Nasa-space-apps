/* SSURGO soil map-unit summary. */
import React from "react";
import { SoilMapUnit } from "../types/fieldshift";

interface Props {
    soils: SoilMapUnit[];
}

export const SoilSummary: React.FC<Props> = ({ soils }) => {
    if (!soils.length) {
        return (
            <div style={{ padding: "1rem", background: "#f8f9fa", marginBottom: "1rem" }}>
                <h3>Soil profile</h3>
                <p>No SSURGO soil data available.</p>
            </div>
        );
    }

    return (
        <div style={{ padding: "1rem", background: "#f8f9fa", marginBottom: "1rem" }}>
            <h3>Soil profile — USDA NRCS SSURGO</h3>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
                <thead>
                    <tr style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
                        <th style={{ padding: "0.5rem" }}>Map unit</th>
                        <th style={{ padding: "0.5rem" }}>Name</th>
                        <th style={{ padding: "0.5rem" }}>Available water (0–25 cm)</th>
                        <th style={{ padding: "0.5rem" }}>Major components</th>
                    </tr>
                </thead>
                <tbody>
                    {soils.map((mu) => (
                        <tr key={mu.mukey} style={{ borderBottom: "1px solid #eee" }}>
                            <td style={{ padding: "0.4rem", fontFamily: "monospace" }}>{mu.musym ?? mu.mukey}</td>
                            <td style={{ padding: "0.4rem" }}>{mu.map_unit_name}</td>
                            <td style={{ padding: "0.4rem" }}>
                                {mu.available_water_storage_cm == null ? "n/a" : mu.available_water_storage_cm.toFixed(1) + " cm"}
                            </td>
                            <td style={{ padding: "0.4rem" }}>
                                {mu.components.slice(0, 3).map((c) => c.component_name).join(", ")}
                                {mu.components.length > 3 ? ` +${mu.components.length - 3}` : ""}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};