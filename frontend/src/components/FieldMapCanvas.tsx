/* Field map canvas component */
import React from "react";

export const FieldMapCanvas: React.FC = () => {
    return (
        <div style={{height: "400px", width: "100%", background: "#ccc", marginBottom: "1rem"}}>
            <h3>Field Map</h3>
            <span>Map will render here using MapLibre GL JS</span>
        </div>
    );
};