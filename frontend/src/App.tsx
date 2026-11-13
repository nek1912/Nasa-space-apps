/* Main App component */
import React from "react";
{FarmSelectorBar}
{FieldMapCanvas}
{PhenologyTimeline}
{PrioritySliders}
{ClimateStressBar}
{RotationMatrix}
{UncertaintyBadge}

const App: React.FC = () => {
    return (
        <div style={{fontFamily: "system-ui, sans-serif", maxWidth: "1200px", margin: "0 auto"}}>
            <h1>FieldShift: Farm Vulnerability & Rotation Optimization</h1>
            <FarmSelectorBar />
            <FieldMapCanvas />
            <PhenologyTimeline />
            <PrioritySliders />
            <ClimateStressBar />
            <RotationMatrix />
            <UncertaintyBadge severity={0.45} />
        </div>
    );
};

export default App;