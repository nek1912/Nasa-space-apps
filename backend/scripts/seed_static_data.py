#!/usr/bin/env python3
"""Deterministic generator for data/*.json files used in FieldShift."""

import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def generate_crops_catalog():
    crops = [
        {"name": "Wheat", "family": "Poaceae", "nfix": False},
        {"name": "Corn", "family": "Poaceae", "nfix": False},
        {"name": "Soybean", "family": "Fabaceae", "nfix": True},
        {"name": "Alfalfa", "family": "Fabaceae", "nfix": True},
        {"name": "Rice", "family": "Poaceae", "nfix": False},
        {"name": "Cotton", "family": "Malvaceae", "nfix": False},
        {"name": "Barley", "family": "Poaceae", "nfix": False},
        {"name": "Oats", "family": "Poaceae", "nfix": False},
        {"name": "Sunflower", "family": "Asteraceae", "nfix": False},
        {"name": "Potato", "family": "Solanaceae", "nfix": False},
        {"name": "Tomato", "family": "Solanaceae", "nfix": False},
        {"name": "Cucumber", "family": "Cucurbitaceae", "nfix": False},
        {"name": "Bean", "family": "Fabaceae", "nfix": True},
        {"name": "Pea", "family": "Fabaceae", "nfix": True},
        {"name": "Lentil", "family": "Fabaceae", "nfix": True},
        {"name": "Canola", "family": "Brassicaceae", "nfix": False},
        {"name": "Safflower", "family": "Asteraceae", "nfix": False},
        {"name": "Sorghum", "family": "Poaceae", "nfix": False},
        {"name": "Millet", "family": "Poaceae", "nfix": False},
    ]
    with open(DATA_DIR / "crops_catalog.json", "w") as f:
        json.dump({"crops": crops}, f, indent=2)


def generate_hero_farms():
    farms = [
        {"id": "ks_finney", "location": "Kansas, Finney County", "crop": "Wheat", "area_hectares": 120, "soil_type": "Loam", "yield_last_year": 3.5},
        {"id": "ia_story", "location": "Iowa, Story County", "crop": "Corn", "area_hectares": 85, "soil_type": "Clay Loam", "yield_last_year": 9.2},
        {"id": "ca_fresno", "location": "California, Fresno County", "crop": "Cotton", "area_hectares": 200, "soil_type": "Sandy Loam", "yield_last_year": 1.8},
    ]
    with open(DATA_DIR / "hero_farms.json", "w") as f:
        json.dump({"farms": farms}, f, indent=2)


def generate_nass_baselines():
    # USDA NASS county baselines (simplified)
    data = [
        ("Finney County, KS", 3.5),
        ("Story County, IA", 9.2),
        ("Fresno County, CA", 1.8),
        ("Maricopa County, AZ", 2.1),
        ("Middlesex County, MA", 1.2),
    ]
    with open(DATA_DIR / "nass_county_baselines.csv", "w") as f:
        f.write("county,yield_per_acre\n")
        for county, yield_val in data:
            f.write(f"{county},{yield_val}\n")


def main():
    generate_crops_catalog()
    generate_hero_farms()
    generate_nass_baselines()
    print("Static data seeded successfully.")


if __name__ == "__main__":
    main()