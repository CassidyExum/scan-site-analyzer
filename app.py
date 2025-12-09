import streamlit as st
import pandas as pd
import requests
from math import radians, sin, cos, sqrt, atan2
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import io
import zipfile
import folium
from streamlit_folium import st_folium

# Set page configuration
st.set_page_config(
    page_title="SCAN Site Analyzer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add clean, professional CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2e86ab;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .logo-container {
        text-align: center;
        margin-bottom: 1rem;
    }
    .logo-img {
        max-height: 80px;
    }
</style>
""", unsafe_allow_html=True)

# Import the functions we created earlier
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c * 0.621371

def create_static_map_always_visible_tooltips(center_coord, coordinates_list, marker_names=None, 
                                             zoom_level=12, map_size=(800, 600)):
    """
    Create a static map with tooltips that are permanently visible.
    """
    
    m = folium.Map(
        location=center_coord,
        zoom_start=zoom_level,
        width=map_size[0],
        height=map_size[1],
        zoom_control=False,
        scroll_wheel_zoom=False,
        dragging=False,
        tiles='OpenStreetMap'
    )
    
    # Add center marker
    folium.Marker(
        center_coord,
        popup="Center Location",
        tooltip="Center",
        icon=folium.Icon(color='red', icon='star')
    ).add_to(m)
    
    # Add all other markers with permanent tooltips
    for i, coord in enumerate(coordinates_list):
        lat, lon = coord
        
        if marker_names and i < len(marker_names):
            name = marker_names[i]
        else:
            name = f"Location {i+1}"
        
        folium.Marker(
            [lat, lon],
            popup=name,
            tooltip=folium.Tooltip(
                name,
                permanent=True,  # This makes the tooltip always visible
                direction='top',  # Position above marker
                offset=(0, -10),  # Adjust position
                className='permanent-label'  # Custom class for styling
            ),
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
    
    # Auto-fit bounds
    if coordinates_list:
        all_coords = [center_coord] + coordinates_list
        min_lat = min(coord[0] for coord in all_coords)
        max_lat = max(coord[0] for coord in all_coords)
        min_lon = min(coord[1] for coord in all_coords)
        max_lon = max(coord[1] for coord in all_coords)
        
        lat_padding = (max_lat - min_lat) * 0.075
        lon_padding = (max_lon - min_lon) * 0.075
        
        m.fit_bounds([
            [min_lat - lat_padding, min_lon - lon_padding],
            [max_lat + lat_padding, max_lon + lon_padding]
        ])
    
    # Add CSS to style the permanent labels
    m.get_root().html.add_child(folium.Element("""
    <style>
        .folium-map {
            cursor: default !important;
        }
        
        .leaflet-container {
            pointer-events: none !important;
        }
        
        /* Style the permanent labels */
        .permanent-label {
            background-color: white;
            border: 2px solid blue;
            border-radius: 8px;
            padding: 4px 8px;
            font-weight: bold;
            font-family: Arial, sans-serif;
            font-size: 12px;
            color: #333;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
            white-space: nowrap;
            pointer-events: auto !important;
        }
        
        .leaflet-tooltip-top:before {
            border-top-color: blue !important;
        }
    </style>
    
    <script>
        // Make tooltips permanently visible on load
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(function() {
                var tooltips = document.querySelectorAll('.leaflet-tooltip');
                tooltips.forEach(function(tooltip) {
                    tooltip.style.opacity = '1';
                    tooltip.style.display = 'block';
                });
            }, 1000);
        });
    </script>
    """))
    
    return m

def get_closest_scan_sites(latitude: float, longitude: float, num_sites: int = 5):
    STATIONS_URL = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations"
    
    df_columns = [
        'SCAN Site',
        'Station Triplet', 
        'Elevation', 
        'Distance to Installation',
        'Latitude',
        'Longitude'
    ]
    
    try:
        params = {'format': 'json'}
        response = requests.get(STATIONS_URL, params=params, timeout=120)
        response.raise_for_status()
        all_stations = response.json()
        
        df_all = pd.DataFrame(all_stations)
        df_scan = df_all[df_all['networkCode'] == 'SCAN'].copy()
        
        if len(df_scan) == 0:
            return pd.DataFrame(columns=df_columns)
        
        distances = []
        for _, station in df_scan.iterrows():
            try:
                station_lat = station.get('latitude', 0)
                station_lon = station.get('longitude', 0)
                if station_lat and station_lon:
                    distance = haversine_distance(latitude, longitude, station_lat, station_lon)
                    distances.append(distance)
                else:
                    distances.append(float('inf'))
            except:
                distances.append(float('inf'))
        
        df_scan['Distance to Installation'] = distances
        df_scan = df_scan[df_scan['Distance to Installation'] != float('inf')]
        df_scan = df_scan.sort_values('Distance to Installation').head(num_sites)
        
        result_df = pd.DataFrame({
            'SCAN Site': df_scan['name'].values,
            'Station Triplet': df_scan['stationTriplet'].values,
            'Elevation': df_scan['elevation'].apply(lambda x: f"{x}" if pd.notna(x) else 'N/A'),  # Remove ' ft'
            'Distance to Installation (Miles)': df_scan['Distance to Installation'].round(2),
            'Latitude': df_scan['latitude'].values,
            'Longitude': df_scan['longitude'].values
        })
        
        return result_df.reset_index(drop=True)
        
    except requests.RequestException as e:
        st.error(f"Error fetching stations data: {e}")
        return pd.DataFrame(columns=df_columns)

def get_station_sensor_data(station_triplet: str):
    DATA_URL = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data"
    
    sensors = {
        'soil_moisture_20': 'SMN:-20',
        'soil_moisture_40': 'SMN:-40',
        'soil_temp_20': 'STX:-20',
        'soil_temp_40': 'STX:-40',
        'air_temp_max': 'TMAX'
    }
    
    sensor_dataframes = {}
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    begin_date = (datetime.now() - timedelta(days=15*365)).strftime('%Y-%m-%d')
    
    for sensor_key, element_code in sensors.items():
        encoded_station = station_triplet.replace(':', '%3A')
        
        url = (f"{DATA_URL}?stationTriplets={encoded_station}"
               f"&elements={element_code}"
               f"&duration=DAILY"
               f"&beginDate={begin_date}"
               f"&endDate={end_date}"
               f"&periodRef=END"
               f"&centralTendencyType=NONE"
               f"&returnFlags=false"
               f"&returnOriginalValues=false"
               f"&returnSuspectData=false"
               f"&format=json")
        
        try:
            response = requests.get(url, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response has expected structure
                if isinstance(data, list) and len(data) > 0:
                    if 'data' in data[0] and isinstance(data[0]['data'], list) and len(data[0]['data']) > 0:
                        if 'values' in data[0]['data'][0]:
                            values = data[0]['data'][0]['values']
                            df = pd.DataFrame(values)
                            sensor_dataframes[sensor_key] = df
                        else:
                            # No values in response
                            sensor_dataframes[sensor_key] = pd.DataFrame()
                    else:
                        # No data array in response
                        sensor_dataframes[sensor_key] = pd.DataFrame()
                else:
                    # Empty or invalid response
                    sensor_dataframes[sensor_key] = pd.DataFrame()
            else:
                # API returned error status
                sensor_dataframes[sensor_key] = pd.DataFrame()
                
        except (requests.RequestException, KeyError, IndexError, ValueError) as e:
            # Handle any exceptions gracefully
            sensor_dataframes[sensor_key] = pd.DataFrame()
    
    return sensor_dataframes

def remove_outliers(series):
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    filtered_values = series[(series >= lower_bound) & (series <= upper_bound)]
    if len(filtered_values) >= len(series) * 0.5:
        return filtered_values
    else:
        return series

def create_station_overview(nearby_stations_df):
    overview_data = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    if 'sensor_data_cache' not in st.session_state:
        st.session_state.sensor_data_cache = {}
    
    for i, (_, station) in enumerate(nearby_stations_df.iterrows()):
        station_triplet = station['Station Triplet']
        station_name = station['SCAN Site']
        
        status_text.text(f"Fetching data for {station_name}... ({i+1}/{len(nearby_stations_df)})")
        
        if station_triplet not in st.session_state.sensor_data_cache:
            sensor_dfs = get_station_sensor_data(station_triplet)
            st.session_state.sensor_data_cache[station_triplet] = sensor_dfs
        else:
            sensor_dfs = st.session_state.sensor_data_cache[station_triplet]
        
        soil_moisture_min_20 = 'N/A'
        soil_moisture_min_40 = 'N/A'
        soil_temp_max_20 = 'N/A'
        soil_temp_max_40 = 'N/A'
        ambient_temp_max = 'N/A'
        
        for sensor_key, df in sensor_dfs.items():
            if not df.empty:
                values = pd.to_numeric(df['value'], errors='coerce').dropna()
                if not values.empty:
                    clean_values = remove_outliers(values)
                    if not clean_values.empty:
                        if sensor_key == 'soil_moisture_20':
                            soil_moisture_min_20 = f"{clean_values.min():.1f}"  # Remove % symbol
                        elif sensor_key == 'soil_moisture_40':
                            soil_moisture_min_40 = f"{clean_values.min():.1f}"  # Remove % symbol
                        elif sensor_key == 'soil_temp_20':
                            temp_f = clean_values.max()
                            temp_c = (temp_f - 32) * 5/9
                            soil_temp_max_20 = f"{temp_c:.1f}"  # Remove °C symbol
                        elif sensor_key == 'soil_temp_40':
                            temp_f = clean_values.max()
                            temp_c = (temp_f - 32) * 5/9
                            soil_temp_max_40 = f"{temp_c:.1f}"  # Remove °C symbol
                        elif sensor_key == 'air_temp_max':
                            temp_f = clean_values.max()
                            temp_c = (temp_f - 32) * 5/9
                            ambient_temp_max = f"{temp_c:.1f}"  # Remove °C symbol
        
        overview_data.append({
            'SCAN Site': station_name,
            'Elevation': station['Elevation'].replace(' ft', '') if station['Elevation'] != 'N/A' else 'N/A',  # Remove ' ft'
            'Distance to Installation (Miles)': station['Distance to Installation (Miles)'],
            'Soil Moisture Minimum 20in': soil_moisture_min_20,
            'Soil Moisture Minimum 40in': soil_moisture_min_40,
            'Soil Temp Maximum 20in': soil_temp_max_20,
            'Soil Temp Maximum 40in': soil_temp_max_40,
            'Ambient Temp Maximum': ambient_temp_max
        })
        
        progress_bar.progress((i + 1) / len(nearby_stations_df))
    
    status_text.text("Complete!")
    progress_bar.empty()
    
    return pd.DataFrame(overview_data)

# Enhanced plotting functions with min/max callouts
def plot_soil_moisture(soil_moisture_20_df, soil_moisture_40_df, station_name):
    fig, ax = plt.subplots(figsize=(12, 6))
    
    soil_moisture_20_df['date'] = pd.to_datetime(soil_moisture_20_df['date'])
    soil_moisture_40_df['date'] = pd.to_datetime(soil_moisture_40_df['date'])
    
    values_20 = pd.to_numeric(soil_moisture_20_df['value'], errors='coerce').dropna()
    values_40 = pd.to_numeric(soil_moisture_40_df['value'], errors='coerce').dropna()
    
    clean_20 = remove_outliers(values_20)
    clean_40 = remove_outliers(values_40)
    
    min_20 = clean_20.min() if not clean_20.empty else None
    min_40 = clean_40.min() if not clean_40.empty else None
    
    ax.plot(soil_moisture_20_df['date'], values_20, 'b-', linewidth=1, alpha=0.7, label='Soil Moisture -20"')
    ax.plot(soil_moisture_40_df['date'], values_40, 'r-', linewidth=1, alpha=0.7, label='Soil Moisture -40"')
    
    if min_20 is not None:
        min_date_20 = soil_moisture_20_df.loc[values_20.idxmin(), 'date']
        ax.annotate(f'Min: {min_20:.1f}%', 
                   xy=(min_date_20, min_20), 
                   xytext=(10, 10), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='blue', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', color='blue'))
    
    if min_40 is not None:
        min_date_40 = soil_moisture_40_df.loc[values_40.idxmin(), 'date']
        ax.annotate(f'Min: {min_40:.1f}%', 
                   xy=(min_date_40, min_40), 
                   xytext=(10, -20), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', color='red'))
    
    ax.set_title(f'{station_name} - Soil Moisture Percent Minimum', fontsize=14, fontweight='bold')
    ax.set_ylabel('Soil Moisture (%)', fontsize=12)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig

def plot_soil_temp(soil_temp_20_df, soil_temp_40_df, station_name):
    fig, ax = plt.subplots(figsize=(12, 6))
    
    soil_temp_20_df['date'] = pd.to_datetime(soil_temp_20_df['date'])
    soil_temp_40_df['date'] = pd.to_datetime(soil_temp_40_df['date'])
    
    values_20 = pd.to_numeric(soil_temp_20_df['value'], errors='coerce').dropna()
    values_40 = pd.to_numeric(soil_temp_40_df['value'], errors='coerce').dropna()
    
    # Convert Fahrenheit to Celsius
    values_20_c = (values_20 - 32) * 5/9
    values_40_c = (values_40 - 32) * 5/9
    
    clean_20 = remove_outliers(values_20_c)
    clean_40 = remove_outliers(values_40_c)
    
    max_20 = clean_20.max() if not clean_20.empty else None
    max_40 = clean_40.max() if not clean_40.empty else None
    
    ax.plot(soil_temp_20_df['date'], values_20_c, 'b-', linewidth=1, alpha=0.7, label='Soil Temp -20"')
    ax.plot(soil_temp_40_df['date'], values_40_c, 'r-', linewidth=1, alpha=0.7, label='Soil Temp -40"')
    
    if max_20 is not None:
        max_date_20 = soil_temp_20_df.loc[values_20_c.idxmax(), 'date']
        ax.annotate(f'Max: {max_20:.1f}°C', 
                   xy=(max_date_20, max_20), 
                   xytext=(10, 10), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='blue', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', color='blue'))
    
    if max_40 is not None:
        max_date_40 = soil_temp_40_df.loc[values_40_c.idxmax(), 'date']
        ax.annotate(f'Max: {max_40:.1f}°C', 
                   xy=(max_date_40, max_40), 
                   xytext=(10, -20), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', color='red'))
    
    ax.set_title(f'{station_name} - Soil Temperature Maximum', fontsize=14, fontweight='bold')
    ax.set_ylabel('Soil Temperature (°C)', fontsize=12)  # Updated to °C
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig

def plot_ambient_temp(air_temp_max_df, station_name):
    fig, ax = plt.subplots(figsize=(12, 6))
    
    air_temp_max_df['date'] = pd.to_datetime(air_temp_max_df['date'])
    values = pd.to_numeric(air_temp_max_df['value'], errors='coerce').dropna()
    
    # Convert Fahrenheit to Celsius
    values_c = (values - 32) * 5/9
    
    clean_values = remove_outliers(values_c)
    max_temp = clean_values.max() if not clean_values.empty else None
    
    ax.plot(air_temp_max_df['date'], values_c, 'b-', linewidth=1, alpha=0.7, label='Air Temperature Max')
    
    if max_temp is not None:
        max_date = air_temp_max_df.loc[values_c.idxmax(), 'date']
        ax.annotate(f'Max: {max_temp:.1f}°C', 
                   xy=(max_date, max_temp), 
                   xytext=(10, 10), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='blue', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', color='blue'))
    
    ax.set_title(f'{station_name} - Ambient Air Temperature Maximum', fontsize=14, fontweight='bold')
    ax.set_ylabel('Air Temperature (°C)', fontsize=12)  # Updated to °C
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig

def create_zip_buffer(figures_dict, station_name, map_fig=None):
    """Create a zip file containing all plots and optionally the map"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        # Add all plots
        for plot_name, fig in figures_dict.items():
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            filename = f"{station_name}_{plot_name.lower().replace(' ', '_')}.png"
            zip_file.writestr(filename, buf.getvalue())
        
        # Add map if provided
        if map_fig:
            map_buf = io.BytesIO()
            map_fig.save(map_buf, format='png', dpi=300, bbox_inches='tight')
            map_buf.seek(0)
            map_filename = f"{station_name}_location_map.png"
            zip_file.writestr(map_filename, map_buf.getvalue())
    
    zip_buffer.seek(0)
    return zip_buffer

# Main app
def main():
    # Add RRC logo
    st.markdown("""
    <div class="logo-container">
        <img src="https://cdn.theorg.com/0f8b4de9-d8c5-4a5a-bfb7-dfe6a539b1f7_medium.jpg" class="logo-img">
    </div>
    """, unsafe_allow_html=True)

     # Add Created by section here
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1rem; color: #666; font-style: italic;">
        Created by Cassidy Exum - BESS Engineer
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">SCAN Site Analyzer</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    This app helps you find the closest National Weather and Climate Center SCAN (Soil Climate Analysis Network) sites 
    and analyze soil moisture, soil temperature, and ambient temperature data.

    [Visit the SCAN site](https://nwcc-apps.sc.egov.usda.gov/imap/#version=170&elements=M&networks=!&states=!&counties=!&hucs=&minElevation=&maxElevation=&elementSelectType=any&activeOnly=true&activeForecastPointsOnly=false&hucLabels=false&hucIdLabels=false&hucParameterLabels=true&stationLabels=&overlays=&hucOverlays=2&basinOpacity=75&basinNoDataOpacity=25&basemapOpacity=100&maskOpacity=0&mode=stations&openSections=dataElement,parameter,date,basin,options,elements,location,networks&controlsOpen=true&popup=&popupMulti=&popupBasin=&base=esriNgwm&displayType=inventory&basinType=6&dataElement=WTEQ&depth=-8&parameter=PCTMED&frequency=DAILY&duration=I&customDuration=&dayPart=E&year=2023&month=11&day=14&monthPart=E&forecastPubMonth=6&forecastPubDay=1&forecastExceedance=50&useMixedPast=true&seqColor=1&divColor=7&scaleType=D&scaleMin=&scaleMax=&referencePeriodType=POR&referenceBegin=1991&referenceEnd=2020&minimumYears=20&hucAssociations=true&lat=32.499&lon=-94.950&zoom=4.5)
    
    [Visit the GitHub](https://github.com/CassidyExum/scan-site-analyzer)
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for input
    with st.sidebar:
        st.header("Location Input")
        st.write("Enter coordinates to find nearby SCAN sites:")
        
        col1, col2 = st.columns(2)
        with col1:
            latitude = st.number_input("Latitude", value=00.0000, format="%.6f")
        with col2:
            longitude = st.number_input("Longitude", value=-00.0000, format="%.6f")
        
        num_sites = st.slider("Number of closest sites to show", 1, 10, 5)
        
        if st.button("Find SCAN Sites", type="primary"):
            # Clear previous cache when doing a new search
            if 'sensor_data_cache' in st.session_state:
                del st.session_state.sensor_data_cache
            if 'nearby_stations' in st.session_state:
                del st.session_state.nearby_stations
            if 'overview_table' in st.session_state:
                del st.session_state.overview_table
            
            st.session_state.latitude = latitude
            st.session_state.longitude = longitude
            st.session_state.num_sites = num_sites
            st.session_state.search_triggered = True
    
    # Main content - only show results after button click
    if hasattr(st.session_state, 'search_triggered') and st.session_state.search_triggered:
        latitude = st.session_state.latitude
        longitude = st.session_state.longitude
        num_sites = st.session_state.num_sites
        
        st.markdown(f'<h2 class="sub-header">SCAN Sites near ({latitude}, {longitude})</h2>', unsafe_allow_html=True)
        
        # Get nearby stations (cache if not already loaded)
        if 'nearby_stations' not in st.session_state:
            with st.spinner("Finding nearby SCAN sites..."):
                st.session_state.nearby_stations = get_closest_scan_sites(latitude, longitude, num_sites)
        
        nearby_stations = st.session_state.nearby_stations
        
        if not nearby_stations.empty:
            # Display stations
            st.dataframe(nearby_stations, use_container_width=True, hide_index=True)
            
            # Create overview table (cache if not already loaded)
            if 'overview_table' not in st.session_state:
                st.markdown('<h3 class="sub-header">Site Overview</h3>', unsafe_allow_html=True)
                st.session_state.overview_table = create_station_overview(nearby_stations)
            
            overview_table = st.session_state.overview_table
            st.dataframe(overview_table, use_container_width=True, hide_index=True)
            
            # Download buttons for data
            col1, col2 = st.columns(2)
            with col1:
                csv_stations = nearby_stations.to_csv(index=False)
                st.download_button(
                    label="Download Stations Data (CSV)",
                    data=csv_stations,
                    file_name="scan_sites.csv",
                    mime="text/csv"
                )
            with col2:
                csv_overview = overview_table.to_csv(index=False)
                st.download_button(
                    label="Download Overview Data (CSV)",
                    data=csv_overview,
                    file_name="scan_overview.csv",
                    mime="text/csv"
                )
            
            # Station details with all 5 plots (uses cached data)
            st.markdown('<h3 class="sub-header">Detailed Analysis</h3>', unsafe_allow_html=True)
            selected_station = st.selectbox(
                "Select a station for detailed analysis:",
                nearby_stations['SCAN Site'].tolist()
            )
            
            if selected_station:
                station_data = nearby_stations[nearby_stations['SCAN Site'] == selected_station].iloc[0]
                station_triplet = station_data['Station Triplet']
                
                # Use cached sensor data - no API calls here!
                if 'sensor_data_cache' in st.session_state and station_triplet in st.session_state.sensor_data_cache:
                    sensor_dfs = st.session_state.sensor_data_cache[station_triplet]
                    
                    # Create all 5 plots
                    if all(key in sensor_dfs for key in ['soil_moisture_20', 'soil_moisture_40', 'soil_temp_20', 'soil_temp_40', 'air_temp_max']):
                        
                        # Soil Moisture Plot
                        st.markdown("#### Soil Moisture Analysis")
                        fig_moisture = plot_soil_moisture(
                            sensor_dfs['soil_moisture_20'],
                            sensor_dfs['soil_moisture_40'],
                            selected_station
                        )
                        st.pyplot(fig_moisture)
                        
                        # Soil Temperature Plot
                        st.markdown("#### Soil Temperature Analysis")
                        fig_soil_temp = plot_soil_temp(
                            sensor_dfs['soil_temp_20'],
                            sensor_dfs['soil_temp_40'],
                            selected_station
                        )
                        st.pyplot(fig_soil_temp)
                        
                        # Ambient Temperature Plot
                        st.markdown("#### Ambient Temperature Analysis")
                        fig_ambient_temp = plot_ambient_temp(
                            sensor_dfs['air_temp_max'],
                            selected_station
                        )
                        st.pyplot(fig_ambient_temp)

                        # Add map under the plots
                        st.markdown("#### Location Map")
                        if selected_station:
                            station_data = nearby_stations[nearby_stations['SCAN Site'] == selected_station].iloc[0]
                            station_lat = station_data['Latitude']
                            station_lon = station_data['Longitude']
                            
                            # Prepare data for the map
                            center_coord = [st.session_state.latitude, st.session_state.longitude]  # User's search location
                            # Get coordinates and names of all nearby stations
                            station_coords = []
                            station_names = []
                            for _, station in nearby_stations.iterrows():
                                station_coords.append([station['Latitude'], station['Longitude']])
                                station_names.append(station['SCAN Site'])
    
                            # Create and display the static map with permanent tooltips
                            station_map = create_static_map_always_visible_tooltips(
                                center_coord=center_coord,
                                coordinates_list=station_coords,
                                marker_names=station_names,
                                zoom_level=10,
                                map_size=(700, 400)
                            )
    
                            # Display the interactive Folium map
                            st_folium(station_map, width=700, height=400)
                        
                        # Single download button for all plots
                        st.markdown("#### Download All Plots")
                        figures_dict = {
                            "Soil Moisture": fig_moisture,
                            "Soil Temperature": fig_soil_temp,
                            "Ambient Temperature": fig_ambient_temp,
                        }

                        zip_buffer = create_zip_buffer(figures_dict, selected_station)
                        st.download_button(
                            label="Download All Plots (ZIP)",
                            data=zip_buffer,
                            file_name=f"{selected_station}_analysis_package.zip",
                            mime="application/zip"
                        )
                    
                    else:
                        st.warning("Some sensor data is missing for this station.")
                else:
                    st.warning("Sensor data not available for this station. Please perform a new search.")
        
        else:
            st.error("No SCAN sites found near the specified location.")
    
    else:
        # Welcome screen - only shown before search
        st.info("Enter coordinates in the sidebar and click 'Find SCAN Sites' to get started!")
        
        # About section
        st.markdown('<h3 class="sub-header">About This Application</h3>', unsafe_allow_html=True)
        st.write("""
        Enter the latitude and longitude of your project site into the left sidebar, select the number
        of SCAN stations you want data for (the more stations you select the longer it will take to run,
        I recommend 5 stations to start).

        **For report usage:** 
        - All tables can exported to CSV
        - All plots can be exported as .png files in a ZIP folder
        - Please screenshot the map using your snipping tool to get a png image

        **Inputs:**
        - Latitude of Project Site
        - Longitude of Project Site

        **Outputs**
        - Elevation of each SCAN site
        - Soil moisture at 20" and 40" depths
        - Soil temperature at 20" and 40" depths  
        - Ambient air temperature
        - Tables and Plots of the above values
        """)

if __name__ == "__main__":
    main()








