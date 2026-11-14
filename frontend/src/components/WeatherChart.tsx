/* Monthly NASA POWER weather aggregates. */
import React from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { WeatherMonth } from "../types/fieldshift";

interface Props {
    monthly: WeatherMonth[];
}

export const WeatherChart: React.FC<Props> = ({ monthly }) => {
    if (!monthly.length) {
        return (
            <div style={{ padding: "1rem", background: "#f8f9fa", marginBottom: "1rem" }}>
                <h3>Weather</h3>
                <p>No NASA POWER weather data available.</p>
            </div>
        );
    }

    const chartData = monthly.map((m) => ({
        ...m,
        label: `${m.year}-${String(m.month).padStart(2, "0")}`,
    }));

    return (
        <div style={{ padding: "1rem", background: "#f8f9fa", marginBottom: "1rem" }}>
            <h3>Weather — NASA POWER monthly aggregates</h3>
            <p style={{ margin: "0 0 0.5rem 0", fontSize: "0.85rem", color: "#666" }}>
                Derived from daily POWER values at the Story County reference point. Days with missing
                source values are excluded from each month's count.
            </p>
            <ResponsiveContainer width="100%" height={260}>
                <LineChart data={chartData}>
                    <XAxis dataKey="label" />
                    <YAxis label={{ value: "mm / °C", angle: -90, position: "insideLeft" }} />
                    <Tooltip />
                    <Line dataKey="precip_mm_total" stroke="#3b82f6" dot={false} />
                    <Line dataKey="tmax_c_mean" stroke="#ef4444" dot={false} />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};