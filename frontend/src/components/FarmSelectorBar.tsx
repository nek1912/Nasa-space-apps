/* Farm selector bar component */
import React from "react";

export const FarmSelectorBar: React.FC = () => {
    return (
        <div style={{padding: "1rem", background: "#f8f9fa", marginBottom: "1rem"}}>
            <h3>Select Farm</h3>
            <select style={{marginRight: "1rem"}}>
                <option value="ks_finney">Kansas Finney County</option>
                <option value="ia_story">Iowa Story County</option>
                <option value="ca_fresno">California Fresno County</option>
            </select>
        </div>
    );
};