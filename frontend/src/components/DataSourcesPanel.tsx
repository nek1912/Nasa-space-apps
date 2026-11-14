/* Source provenance and availability panel. */
import React from "react";
import { SourceStatus } from "../types/fieldshift";

interface Props {
    sources: SourceStatus[];
}

const statusChip = (status: string) => {
    const style: React.CSSProperties = {
        fontSize: "0.75rem",
        padding: "0.15rem 0.5rem",
        borderRadius: "3px",
        color: "#fff",
        display: "inline-block",
        minWidth: "7rem",
        textAlign: "center",
    };
    if (status === "ok") style.background = "#16a34a";
    if (status === "stale") style.background = "#ca8a04";
    if (status === "unavailable") style.background = "#dc2626";
    return <span style={style}>{status}</span>;
};

export const DataSourcesPanel: React.FC<Props> = ({ sources }) => {
    if (!sources.length) {
        return (
            <div style={{ padding: "1rem", background: "#f8f9fa", marginBottom: "1rem" }}>
                <h3>Sources and coverage</h3>
                <p>No source metadata available.</p>
            </div>
        );
    }

    return (
        <div style={{ padding: "1rem", background: "#f8f9fa", marginBottom: "1rem" }}>
            <h3>Sources and coverage</h3>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
                <thead>
                    <tr style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>
                        <th style={{ padding: "0.4rem" }}>Provider / product</th>
                        <th style={{ padding: "0.4rem" }}>Status</th>
                        <th style={{ padding: "0.4rem" }}>Geographic scope</th>
                        <th style={{ padding: "0.4rem" }}>Period</th>
                        <th style={{ padding: "0.4rem" }}>Retrieved</th>
                    </tr>
                </thead>
                <tbody>
                    {sources.map((s) => (
                        <tr key={s.source_id} style={{ borderBottom: "1px solid #eee" }}>
                            <td style={{ padding: "0.4rem", fontSize: "0.85rem" }}>
                                {s.provider} — {s.product}
                                {s.detail && (
                                    <>
                                        <br />
                                        <span style={{ color: "#b00020", fontSize: "0.75rem" }}>{s.detail}</span>
                                    </>
                                )}
                            </td>
                            <td style={{ padding: "0.4rem" }}>{statusChip(s.status)}</td>
                            <td style={{ padding: "0.4rem" }}>{s.geographic_scope}</td>
                            <td style={{ padding: "0.4rem" }}>
                                {s.period_start ?? "n/a"} to {s.period_end ?? "n/a"}
                            </td>
                            <td style={{ padding: "0.4rem" }}>{s.retrieved_at ?? "n/a"}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};