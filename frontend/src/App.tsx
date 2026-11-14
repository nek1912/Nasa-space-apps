/* Main App component — Phase 1 + Phase 2 single-region real-data dashboard. */
import React, { useEffect, useState } from "react";
import { LayerInfoResponse, RecommendRotationsResponse, RegionSummary } from "./types/fieldshift";
import { fetchLayerInfo, fetchRecommendations, fetchRegionSummary } from "./api/client";
import { FarmSelectorBar } from "./components/FarmSelectorBar";
import { FieldMapCanvas } from "./components/FieldMapCanvas";
import { LayerSelector } from "./components/LayerSelector";
import { Legend } from "./components/Legend";
import { RotationCards } from "./components/RotationCards";
import { ScopeLabel } from "./components/ScopeLabel";
import { CropHistoryChart } from "./components/CropHistoryChart";
import { SoilSummary } from "./components/SoilSummary";
import { WeatherChart } from "./components/WeatherChart";
import { DataSourcesPanel } from "./components/DataSourcesPanel";

const App: React.FC = () => {
    const [data, setData] = useState<RegionSummary | null>(null);
    const [layerInfo, setLayerInfo] = useState<LayerInfoResponse | null>(null);
    const [recommendations, setRecommendations] = useState<RecommendRotationsResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [cdlYear, setCdlYear] = useState<number>(2021);
    const [showSsurgo, setShowSsurgo] = useState(false);

    useEffect(() => {
        let cancelled = false;

        Promise.all([fetchRegionSummary(), fetchLayerInfo(), fetchRecommendations()])
            .then(([summary, info, recs]) => {
                if (!cancelled) {
                    setData(summary);
                    setLayerInfo(info);
                    setRecommendations(recs);
                }
            })
            .catch((err) => {
                if (!cancelled) setError(err instanceof Error ? err.message : String(err));
            })
            .finally(() => {
                if (!cancelled) setLoading(false);
            });

        return () => {
            cancelled = true;
        };
    }, []);

    const defaultYear = layerInfo?.cdl_years[0]?.year ?? 2021;

    useEffect(() => {
        if (layerInfo && cdlYear !== defaultYear) {
            setCdlYear(defaultYear);
        }
    }, [layerInfo, cdlYear, defaultYear]);

    if (loading) {
        return (
            <div style={{ fontFamily: "system-ui, sans-serif", maxWidth: "1200px", margin: "0 auto", padding: "1rem" }}>
                <h1>FieldShift</h1>
                <p>Loading Story County data…</p>
            </div>
        );
    }

    if (error) {
        return (
            <div style={{ fontFamily: "system-ui, sans-serif", maxWidth: "1200px", margin: "0 auto", padding: "1rem" }}>
                <h1>FieldShift</h1>
                <p style={{ color: "#b00020" }}>Failed to load data: {error}</p>
                <p>Start the backend at http://localhost:8000 and ingest data first.</p>
            </div>
        );
    }

    return (
        <div style={{ fontFamily: "system-ui, sans-serif", maxWidth: "1200px", margin: "0 auto", padding: "1rem" }}>
            <h1>FieldShift — Story County, Iowa</h1>
            <FarmSelectorBar />
            <ScopeLabel scope="county" />
            <LayerSelector
                cdlYear={cdlYear}
                availableYears={layerInfo.cdl_years}
                showSsurgo={showSsurgo}
                ssurgoAvailable={layerInfo.ssurgo_layer?.available ?? false}
                onCdlYearChange={setCdlYear}
                onSsurgoToggle={setShowSsurgo}
            />
            <FieldMapCanvas
                cdlYear={cdlYear}
                showSsurgo={showSsurgo}
                onCdlYearChange={setCdlYear}
                onSsurgoToggle={setShowSsurgo}
                layerInfoLoaded={layerInfo !== null}
                layerError={layerInfo?.aoi_statistics_blocker ?? null}
            />
            <Legend layerInfo={layerInfo} showSsurgo={showSsurgo} />
            <DataSourcesPanel sources={data.sources} />
            <CropHistoryChart crops={data.crops} />
            <SoilSummary soils={data.soils} />
            <WeatherChart monthly={data.weather_monthly} />
            <RotationCards strategies={recommendations.strategies} />
        </div>
    );
};

export default App;