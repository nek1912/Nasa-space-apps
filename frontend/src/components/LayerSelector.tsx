/* CDL year selector and SSURGO layer toggle. */
import React from "react";
import { CdLYearInfo } from "../types/fieldshift";

interface Props {
    cdlYear: number;
    availableYears: CdLYearInfo[];
    showSsurgo: boolean;
    ssurgoAvailable: boolean;
    onCdlYearChange: (year: number) => void;
    onSsurgoToggle: (show: boolean) => void;
}

export const LayerSelector: React.FC<Props> = ({
    cdlYear,
    availableYears,
    showSsurgo,
    ssurgoAvailable,
    onCdlYearChange,
    onSsurgoToggle,
}) => {
    return (
        <div style={{ padding: "1rem", background: "#f8f9fa", marginBottom: "1rem", border: "1px solid #dee2e6", borderRadius: "4px" }}>
            <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "center" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <label style={{ fontSize: "0.85rem", fontWeight: "600", color: "#333" }}>CDL Year:</label>
                    <select
                        value={cdlYear}
                        onChange={(e) => onCdlYearChange(Number(e.target.value))}
                        style={{ fontSize: "0.85rem", padding: "0.25rem 0.5rem" }}
                    >
                        {availableYears.map((y) => (
                            <option key={y.year} value={y.year} disabled={!y.available}>
                                {y.year} {y.available ? "" : " (unavailable)"}
                            </option>
                        ))}
                    </select>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <input
                        type="checkbox"
                        checked={showSsurgo}
                        onChange={(e) => onSsurgoToggle(e.target.checked)}
                        disabled={!ssurgoAvailable}
                    />
                    <label style={{ fontSize: "0.85rem", fontWeight: "600", color: "#333", cursor: ssurgoAvailable ? "pointer" : "not-allowed" }}>
                        Show SSURGO soil map units
                    </label>
                    {!ssurgoAvailable && (
                        <span style={{ fontSize: "0.75rem", color: "#b00020" }}>(SSURGO layer unavailable)</span>
                    )}
                </div>
            </div>
        </div>
    );
};