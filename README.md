# 🌱 SCAN Site Analyzer

A Streamlit web application for analyzing USDA SCAN (Soil Climate Analysis Network) site data. Find the closest soil and climate monitoring stations, analyze soil moisture, temperature data, and generate professional reports.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)

## 🚀 Live Demo

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-name.streamlit.app/)

## 📋 Overview

The SCAN Site Analyzer helps farmers, researchers, and environmental professionals quickly access and analyze data from the USDA's National Weather and Climate Center Soil Climate Analysis Network. The app provides:

- **Location-based SCAN site discovery**
- **Soil moisture analysis** at 20" and 40" depths
- **Soil temperature monitoring** at multiple depths
- **Ambient temperature data** in Celsius
- **Interactive visualizations with min/max callouts**
- **Clean data export without units for easy analysis**
- **Interactive maps with visible station labels**

## 🆕 Latest Features

### 🎯 Enhanced User Experience
- **One-click search** - Data loads only when requested
- **Smart caching** - Fast station switching with cached data
- **Clean data export** - CSV files contain only numerical values (no units)
- **Interactive maps** - Folium maps with permanently visible station labels
- **Professional styling** - Clean, consistent interface with RRC branding

### 📊 Advanced Analytics
- **Outlier detection** - Automatic filtering of anomalous data points
- **Min/Max callouts** - Visual annotations on plots
- **Multi-depth analysis** - Compare 20" and 40" depth data
- **Temperature conversion** - All temperatures displayed in Celsius
- **Time-series visualization** - Historical data trends

## 🎯 Features

### 🔍 Site Discovery
- Find the closest SCAN sites to any location in the US
- Customizable number of results (1-10 sites)
- Distance calculations with haversine formula
- Real-time API integration with USDA AWDB

### 📊 Data Analysis
- **Soil Moisture**: Minimum values at 20" and 40" depths with outlier removal
- **Soil Temperature**: Maximum values at 20" and 40" depths in Celsius
- **Ambient Temperature**: Maximum air temperature in Celsius
- **Automatic outlier detection** using IQR method
- **5-year historical data** analysis

### 📈 Professional Visualization
- Interactive time-series plots with min/max callouts
- Multi-depth comparisons (20" vs 40")
- Clean, export-ready high-resolution figures (300 DPI)
- Interactive Folium maps with permanent station labels

### 💾 Data Export
- Download station information as clean CSV (numerical values only)
- Export analysis results as CSV (no units in values)
- Download all plots as ZIP file (PNG format)
- Interactive map with screenshot instructions

## 🗂️ Project Structure

```
scan-site-analyzer/
│
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
└── .streamlit/           # Streamlit configuration (optional)
    └── config.toml
```

## 🎮 Usage

1. **Enter Coordinates**: Input latitude and longitude
2. **Configure Search**: Set the number of closest sites to find
3. **Click Search**: Press "Find SCAN Sites" to load data
4. **View Results**: Browse the table of nearby SCAN sites
5. **Analyze Data**: Check the overview table for key metrics
6. **Explore Details**: Select individual stations for:
   - Soil moisture plots with min callouts
   - Soil temperature plots with max callouts
   - Ambient temperature plots with max callouts
   - Interactive map with all station locations
7. **Export Data**: 
   - Download stations data as CSV (clean numbers)
   - Download overview data as CSV (clean numbers)
   - Download all plots as ZIP (high-quality PNGs)
   - Screenshot the interactive map

### Performance Optimizations
- **Smart caching** prevents redundant API calls
- **Session state management** for fast navigation
- **Data persistence** during user session
- **Efficient plotting** with cached figure generation

### Data Export Notes
- **CSV files contain only numerical values** for easy analysis
- **Column names indicate units** (Elevation, Soil Moisture Minimum 20in, etc.)
- **Temperatures are in Celsius** (converted from Fahrenheit API data)
- **Distance is in miles** (calculated from coordinates)

## 🔧 API Integration

This app integrates with the [USDA AWDB REST API](https://wcc.sc.egov.usda.gov/awdbRestApi/) to fetch real-time SCAN site data. The application handles:

- Station metadata retrieval
- Sensor data processing (soil moisture, temperature)
- Data cleaning and outlier detection
- Fahrenheit to Celsius conversion
- Error handling and timeouts
- Efficient caching to reduce API calls

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [USDA Natural Resources Conservation Service](https://www.nrcs.usda.gov/) for providing the SCAN data
- [National Weather and Climate Center](https://www.wcc.nrcs.usda.gov/) for data access
- [Streamlit](https://streamlit.io/) for the amazing web framework

## 👥 Created By

**[Cassidy Exum]**  
*BESS Engineering*  
*RRC International*
