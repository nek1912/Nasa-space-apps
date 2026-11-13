/* Uncertainty badge component */
import React from "react";

export const UncertaintyBadge: React.FC = ({severity = 0.5}) => {
    const getClass = () => {
        if (severity < 0.3) return "low";
        if (severity < 0.7) return "medium";
        return "high";
    };

    return (
        <span style={{padding: "0.25rem 0.5rem", background: getClass() === "low" ? "#d4edda" : getClass() === "medium" ? "#fff3cd" : "#f8d7da", color: "#000", borderRadius: "3px", fontSize: "0.75rem"}}>
            Uncertainty: {Math.round(severity * 100)}%
        </span>
    );
};