/* Simple legend for CDL and SSURGO map layers. */
import React from "react";
import { LayerInfoResponse } from "../types/fieldshift";

interface Props {
    layerInfo: LayerInfoResponse | null;
    showSsurgo: boolean;
}

export const Legend: React.FC<Props> = ({ layerInfo, showSsurgo }) => {
    if (!layerInfo) return null;

    return (
        <div style={{ padding: "1rem", background: "#f8f9fa", marginBottom: "1rem", border: "1px solid #dee2e6", borderRadius: "4px", fontSize: "0.85rem" }}>
            <h4 style={{ margin: "0 0 0.5rem 0", color: "#333" }}>Map layers</h4>
            <ul style={{ margin: "0 0 0.5rem 0", paddingLeft: "1.2rem" }}>
                <li style={{ marginBottom: "0.25rem" }}>
                    <span style={{ display: "inline-block", width: "12px", height: "12px", background: "#4ade80", marginRight: "0.5rem", border: "1px solid #333" }} />
                    {layerInfo.cdl_years.find((y) => y.year === layerInfo.cdl_years[0]?.year)?.layer_name ?? "CDL"} — CDL crop classification (county-wide)
                </li>
                {showSsurgo && layerInfo.ssurgo_layer && (
                    <li style={{ marginBottom: "0.25rem" }}>
                        <span style={{ display: "inline-block", width: "12px", height: "12px", background: "#3b82f6", opacity: 0.5, marginRight: "0.5rem", border: "1px solid #333" }} />
                        SSURGO map units (soil survey)
                    </li>
                )}
            </ul>
            <p style={{ margin: 0, fontSize: "0.75rem", color: "#666" }}>
                CDL: USDA NASS Cropland Data Layer — annual crop classification at 30 m.&nbsp;
                SSURGO: USDA NRCS Soil Survey Geographic database — mapped soil map units.
            </p>
        </div>
    );
};