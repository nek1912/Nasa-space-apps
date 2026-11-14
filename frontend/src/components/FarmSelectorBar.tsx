/* Single-region label (replaces the three-farm selector for Phase 1). */
import React from "react";

export const FarmSelectorBar: React.FC = () => {
    return (
        <div style={{ padding: "1rem", background: "#f8f9fa", marginBottom: "1rem" }}>
            <h3>Region</h3>
            <span style={{ fontWeight: "600" }}>Story County, Iowa</span>
            <span style={{ marginLeft: "0.5rem", color: "#666", fontSize: "0.9rem" }}>
                — county/regional data only
            </span>
        </div>
    );
};