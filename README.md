# 🌱 SCAN Site Analyzer

A Streamlit web application for analyzing USDA SCAN (Soil Climate Analysis Network) site data. Find the closest soil and climate monitoring stations, analyze soil moisture, temperature data, and generate professional reports.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)

## 🚀 Live Demo

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://rrc-scan-site-analyzer.streamlit.app/#about-scan-sites)

## 📋 Overview

The SCAN Site Analyzer helps farmers, researchers, and environmental professionals quickly access and analyze data from the USDA's National Weather and Climate Center Soil Climate Analysis Network. The app provides:

- **Location-based SCAN site discovery**
- **Soil moisture analysis** at 20" and 40" depths
- **Soil temperature monitoring** at multiple depths
- **Ambient temperature data**
- **Interactive visualizations with min/max callouts**
- **Data export capabilities**
- **Professional reporting**

## 🆕 Latest Features

### 🎯 Enhanced User Experience
- **One-click search** - No automatic reloading, data loads only when requested
- **Smart caching** - All data cached for fast station switching
- **Single download** - Download all plots as a ZIP file
- **Professional styling** - Clean, consistent interface

### 📊 Advanced Analytics
- **Outlier detection** - Automatic filtering of anomalous data points
- **Min/Max callouts** - Visual annotations on plots
- **Multi-depth analysis** - Compare 20" and 40" depth data
- **Time-series visualization** - Historical data trends

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/scan-site-analyzer.git
   cd scan-site-analyzer
