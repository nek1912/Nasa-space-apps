/* Visible scope label: County-level vs Selected AOI. */
import React from "react";

interface Props {
    scope: "county" | "aoi";
}

export const ScopeLabel: React.FC<Props> = ({ scope }) => {
    return (
        <div style={{ padding: "0.5rem 1rem", background: "#e7f3fe", border: "1px solid #b3d9ff", borderRadius: "4px", marginBottom: "1rem", fontSize: "0.85rem", color: "#005a9e" }}>
            <span style={{ fontWeight: "600" }}>Data scope:</span>{" "}
            {scope === "aoi" ? "Selected AOI" : "County-level"} — {scope === "aoi" ? "user-selected area" : "Story County, Iowa (regional, not parcel-level)"}
        </div>
    );
};