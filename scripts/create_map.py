# -*- coding: utf-8 -*-
"""
Mapping Climate Change Impact in Egypt: Interactive Visualization
Author: Noury Hazem
Contact: NouryHazem17@gmail.com

Description:
This script creates an interactive map visualizing climate change impacts in Egypt.
It integrates shapefile data with climate statistics, generating a user-friendly folium map.
"""

# Import necessary libraries
import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import Search
import matplotlib.pyplot as plt
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# Paths to the shapefile and climate data
SHAPEFILE_PATH = "data/egypt_shapefile.zip"  # Shapefile path
CLIMATE_DATA_PATH = "data/egypt_climate_data.csv"  # CSV file path

# Load the shapefile and climate data
geo_df = gpd.read_file(SHAPEFILE_PATH)
climate_data = pd.read_csv(CLIMATE_DATA_PATH)

# Standardize governorate names in both datasets
geo_df['Governorate'] = geo_df['ADM1_EN'].str.strip().str.lower()
climate_data['Governorate'] = climate_data['Governorate'].str.strip().str.lower()

# Merge the shapefile with the climate data on the 'Governorate' column
merged_df = geo_df.merge(climate_data, on="Governorate", how="left")

# Fill missing values with specific data for each governorate
MANUAL_REPLACEMENTS = {
    "behera": {"Avg Temp Increase (°C)": 1.2, "Coastal Erosion (%)": 8.0, "Desertification Risk": "medium", "Annual Precipitation (mm)": 30.0},
    "kafr el-shikh": {"Avg Temp Increase (°C)": 1.3, "Coastal Erosion (%)": 12.0, "Desertification Risk": "medium", "Annual Precipitation (mm)": 25.0},
    "kalyoubia": {"Avg Temp Increase (°C)": 1.4, "Coastal Erosion (%)": 5.0, "Desertification Risk": "low", "Annual Precipitation (mm)": 20.0},
    "matrouh": {"Avg Temp Increase (°C)": 1.1, "Coastal Erosion (%)": 15.0, "Desertification Risk": "high", "Annual Precipitation (mm)": 10.0},
    "menia": {"Avg Temp Increase (°C)": 1.5, "Coastal Erosion (%)": 0.0, "Desertification Risk": "high", "Annual Precipitation (mm)": 5.0},
    "menoufia": {"Avg Temp Increase (°C)": 1.3, "Coastal Erosion (%)": 3.0, "Desertification Risk": "low", "Annual Precipitation (mm)": 22.0},
    "suhag": {"Avg Temp Increase (°C)": 1.6, "Coastal Erosion (%)": 0.0, "Desertification Risk": "high", "Annual Precipitation (mm)": 8.0}
}

# Apply manual replacements
for governorate, values in MANUAL_REPLACEMENTS.items():
    for column, value in values.items():
        merged_df.loc[merged_df['Governorate'] == governorate, column] = value

# Handle 'Desertification Risk' column by mapping categorical values to numeric
DESERTIFICATION_MAP = {
    'low': 1,
    'medium': 2,
    'high': 3,
    'unknown': 0
}
merged_df["Desertification Risk Numeric"] = merged_df["Desertification Risk"].map(DESERTIFICATION_MAP)

# Ensure all datetime columns are converted to strings (if any)
for col in merged_df.select_dtypes(include=['datetime64', 'datetime64[ns]']).columns:
    merged_df[col] = merged_df[col].astype(str)

# Create the folium map centered on Egypt
m = folium.Map(location=[26.8206, 30.8025], zoom_start=6, control_scale=True)

# Function to generate and return a chart as a base64 string
def create_bar_chart(data, title):
    """Generates a bar chart and returns it as a base64-encoded string."""
    fig, ax = plt.subplots()
    ax.bar(data.keys(), data.values())
    ax.set_title(title)
    ax.set_ylabel('Values')
    canvas = FigureCanvas(fig)
    img = io.BytesIO()
    canvas.print_png(img)
    img.seek(0)
    return base64.b64encode(img.read()).decode('utf-8')

# Create a LayerGroup to hold markers
marker_layer = folium.FeatureGroup(name="Governorate Markers").add_to(m)

# Add choropleth layers for temperature, coastal erosion, and desertification risk
folium.Choropleth(
    geo_data=merged_df,
    name="Rising Temperatures",
    data=merged_df,
    columns=["Governorate", "Avg Temp Increase (°C)"],
    key_on="feature.properties.Governorate",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Avg Temperature Increase (°C)",
    highlight=True
).add_to(m)

folium.GeoJson(
    merged_df,
    name="Coastal Erosion",
    style_function=lambda x: {
        "color": "blue" if x["properties"].get("Coastal Erosion (%)", 0) > 0 else "transparent",
        "weight": 2,
        "fillOpacity": 0.5
    },
    tooltip=folium.GeoJsonTooltip(fields=["Governorate", "Coastal Erosion (%)"])
).add_to(m)

folium.Choropleth(
    geo_data=merged_df,
    name="Desertification Risk",
    data=merged_df,
    columns=["Governorate", "Desertification Risk Numeric"],
    key_on="feature.properties.Governorate",
    fill_color="BuGn",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Desertification Risk Level",
    highlight=True
).add_to(m)

# Add markers with climate data and bar charts
for _, row in merged_df.iterrows():
    data = {
        "Avg Temp Increase (°C)": row["Avg Temp Increase (°C)"],
        "Coastal Erosion (%)": row["Coastal Erosion (%)"],
        "Annual Precipitation (mm)": row["Annual Precipitation (mm)"]
    }

    # Generate bar chart for the data
    bar_chart = create_bar_chart(data, f"{row['Governorate']} Climate Data")

    # Popup content
    popup_content = f"""
    <b>{row['Governorate']}</b><br>
    <img src='data:image/png;base64,{bar_chart}'><br>
    <b>Avg Temp Increase (°C):</b> {row["Avg Temp Increase (°C)"]} °C<br>
    <b>Coastal Erosion (%):</b> {row["Coastal Erosion (%)"]}%<br>
    <b>Precipitation (mm):</b> {row["Annual Precipitation (mm)"]} mm
    """

    # Add marker with popup for each region
    folium.Marker(
        [row['geometry'].centroid.y, row['geometry'].centroid.x],
        popup=folium.Popup(popup_content, max_width=400)
    ).add_to(marker_layer)

# Add Layer Control for interactivity
folium.LayerControl(collapsed=False).add_to(m)

# Add a search bar to locate regions by name
search = Search(layer=folium.GeoJson(merged_df), search_label="Governorate", placeholder="Search for a Governorate").add_to(m)

# Save the map to an HTML file
OUTPUT_PATH = "output/interactive_map.html"
m.save(OUTPUT_PATH)

print(f"Map saved to {OUTPUT_PATH}")
