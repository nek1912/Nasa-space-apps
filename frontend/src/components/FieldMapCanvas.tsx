/* Story County map canvas — real MapLibre GL map with verified WMS overlays. */

import React, { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import {
    CDL_WMS,
    SSURGO_WMS,
    OSM_BASE_LAYER,
    STORY_COUNTY_BBOX,
    STORY_COUNTY_CENTER,
    STORY_COUNTY_ZOOM,
} from "../config/mapLayers";

interface Props {
    cdlYear: number;
    showSsurgo: boolean;
    onCdlYearChange: (year: number) => void;
    onSsurgoToggle: (show: boolean) => void;
    layerInfoLoaded: boolean;
    layerError: string | null;
}

const [minx, miny, maxx, maxy] = STORY_COUNTY_BBOX;
const IMAGE_COORDINATES = [
    [minx, maxy],
    [maxx, maxy],
    [maxx, miny],
    [minx, miny],
];

export const FieldMapCanvas: React.FC<Props> = ({
    cdlYear,
    showSsurgo,
    onCdlYearChange,
    onSsurgoToggle,
    layerInfoLoaded,
    layerError,
}) => {
    const mapRef = useRef<maplibregl.Map | null>(null);
    const [mapLoaded, setMapLoaded] = useState(false);

    useEffect(() => {
        if (mapRef.current) return;

        const map = new maplibregl.Map({
            container: "field-map",
            style: {
                version: 8,
                sources: {
                    osm: {
                        type: "raster",
                        tiles: [OSM_BASE_LAYER.url],
                        tileSize: 256,
                        attribution: OSM_BASE_LAYER.attribution,
                    },
                },
                layers: [{ id: "osm-layer", type: "raster", source: "osm" }],
            },
            center: STORY_COUNTY_CENTER,
            zoom: STORY_COUNTY_ZOOM,
        });

        map.on("load", () => {
            setMapLoaded(true);
            addCdlLayer(map, cdlYear);
            if (showSsurgo) addSsurgoLayer(map);
        });

        mapRef.current = map;
        return () => {
            map.remove();
            mapRef.current = null;
            setMapLoaded(false);
        };
    }, []);

    useEffect(() => {
        if (!mapRef.current || !mapLoaded) return;
        updateCdlLayer(mapRef.current, cdlYear);
    }, [cdlYear, mapLoaded]);

    useEffect(() => {
        if (!mapRef.current || !mapLoaded) return;
        if (showSsurgo) {
            addSsurgoLayer(mapRef.current);
        } else {
            removeLayer(mapRef.current, "ssurgo-layer");
            removeSource(mapRef.current, "ssurgo");
        }
    }, [showSsurgo, mapLoaded]);

    return (
        <div style={{ height: "400px", width: "100%", marginBottom: "1rem", position: "relative" }}>
            <h3 style={{ margin: 0, marginBottom: "0.5rem" }}>Story County, Iowa</h3>
            <div id="field-map" style={{ height: "320px", width: "100%" }}></div>
            {!mapLoaded && (
                <div style={{ position: "absolute", bottom: "0.5rem", left: "0.5rem", fontSize: "0.8rem", color: "#666" }}>
                    Loading map…
                </div>
            )}
            {layerError && (
                <div style={{ position: "absolute", bottom: "0.5rem", left: "0.5rem", fontSize: "0.8rem", color: "#b00020", background: "#fffde7", padding: "0.25rem 0.5rem", borderRadius: "3px" }}>
                    {layerError}
                </div>
            )}
        </div>
    );

    function addCdlLayer(map: maplibregl.Map, year: number) {
        const layerName = CDL_WMS.layerForYear(year);
        const wmsUrl = buildWmsUrl(CDL_WMS.baseUrl, [layerName], STORY_COUNTY_BBOX);
        try {
            map.addSource("cdl", {
                type: "image",
                url: wmsUrl,
                coordinates: IMAGE_COORDINATES,
            });
            map.addLayer({
                id: "cdl-layer",
                type: "raster",
                source: "cdl",
                paint: { "raster-opacity": 0.7 },
            });
        } catch {
            updateCdlLayer(map, year);
        }
    }

    function updateCdlLayer(map: maplibregl.Map, year: number) {
        const layerName = CDL_WMS.layerForYear(year);
        const wmsUrl = buildWmsUrl(CDL_WMS.baseUrl, [layerName], STORY_COUNTY_BBOX);
        try {
            const source = map.getSource("cdl") as maplibregl.ImageSource;
            source.setUrl(wmsUrl);
        } catch {
            removeLayer(map, "cdl-layer");
            removeSource(map, "cdl");
            addCdlLayer(map, year);
        }
    }

    function addSsurgoLayer(map: maplibregl.Map) {
        const wmsUrl = buildWmsUrl(SSURGO_WMS.baseUrl, [SSURGO_WMS.layerName], STORY_COUNTY_BBOX);
        try {
            map.addSource("ssurgo", {
                type: "image",
                url: wmsUrl,
                coordinates: IMAGE_COORDINATES,
            });
            map.addLayer({
                id: "ssurgo-layer",
                type: "raster",
                source: "ssurgo",
                paint: { "raster-opacity": 0.5 },
            });
        } catch {
            // Layer may already exist.
        }
    }

    function removeLayer(map: maplibregl.Map, id: string) {
        try { map.removeLayer(id); } catch { /* ignore */ }
    }

    function removeSource(map: maplibregl.Map, id: string) {
        try { map.removeSource(id); } catch { /* ignore */ }
    }
};

function buildWmsUrl(baseUrl: string, layers: string[], bbox: number[]): string {
    const params: Record<string, string> = {
        SERVICE: "WMS",
        VERSION: "1.1.1",
        REQUEST: "GetMap",
        LAYERS: layers.join(","),
        STYLES: "",
        SRS: "EPSG:4326",
        BBOX: bbox.join(","),
        WIDTH: "256",
        HEIGHT: "256",
        FORMAT: "image/png",
        TRANSPARENT: "TRUE",
    };
    return baseUrl + Object.entries(params).map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join("&");
}