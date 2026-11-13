/* WMS/WMTS tile templates (NASA GIBS, CDL, NAIP, Sentinel-2) */
export const MAP_LAYERS = {
    // NASA GIBS true color
    gibs_true_color: {
        name: "NASA GIBS True Color",
        type: "wms",
        url: "https://gibs.earthdata.nasa.gov/wms/services/modis-truecolor/WMSC",
        layers: "MODIS_Terra_TrueColor",
        format: "image/png",
    },
    // USDA CDL crop type
    cdl_crop: {
        name: "USDA CDL Crop Type",
        type: "wms",
        url: "https://services.nationalmap.gov/arcgis/services/USDA_NASS_CDL/WMTS",
        layers: "USDA_NASS_CDL",
        format: "image/png",
    },
    // Sentinel-2 vegetation index
    sentinel_vi: {
        name: "Sentinel-2 Vegetation Index",
        type: "wmts",
        url: "https://geo.sentinel2.eu/tiles/v2",
        layers: "BOA",
        format: "image/tiff;profile=rgb",
    },
}