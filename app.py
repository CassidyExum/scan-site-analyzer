import streamlit as st
import pandas as pd
import requests
from math import radians, sin, cos, sqrt, atan2
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import io

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
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2e86ab;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
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
        response = requests.get(STATIONS_URL, params=params, timeout=30)
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
            'Elevation': df_scan['elevation'].apply(lambda x: f"{x} ft" if pd.notna(x) else 'N/A'),
            'Distance to Installation': df_scan['Distance to Installation'].round(2),
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
    begin_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d')
    
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
        
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            values = data[0]['data'][0]['values']
            df = pd.DataFrame(values)
            sensor_dataframes[sensor_key] = df
    
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
    
    for i, (_, station) in enumerate(nearby_stations_df.iterrows()):
        station_triplet = station['Station Triplet']
        station_name = station['SCAN Site']
        
        status_text.text(f"Fetching data for {station_name}... ({i+1}/{len(nearby_stations_df)})")
        
        sensor_dfs = get_station_sensor_data(station_triplet)
        
        soil_moisture_min_20 = 'N/A'
        soil_moisture_min_40 = 'N/A'
        soil_temp_max_20 = 'N/A'
        soil_temp_max_40 = 'N/A'
        ambient_temp_max = 'N/A'
        
        # Process all sensors
        for sensor_key, df in sensor_dfs.items():
            if not df.empty:
                values = pd.to_numeric(df['value'], errors='coerce').dropna()
                if not values.empty:
                    clean_values = remove_outliers(values)
                    if not clean_values.empty:
                        if sensor_key == 'soil_moisture_20':
                            soil_moisture_min_20 = f"{clean_values.min():.1f}%"
                        elif sensor_key == 'soil_moisture_40':
                            soil_moisture_min_40 = f"{clean_values.min():.1f}%"
                        elif sensor_key == 'soil_temp_20':
                            soil_temp_max_20 = f"{clean_values.max():.1f}°F"
                        elif sensor_key == 'soil_temp_40':
                            soil_temp_max_40 = f"{clean_values.max():.1f}°F"
                        elif sensor_key == 'air_temp_max':
                            ambient_temp_max = f"{clean_values.max():.1f}°F"
        
        # Combine soil moisture
        if soil_moisture_min_20 != 'N/A' and soil_moisture_min_40 != 'N/A':
            min_20_val = float(soil_moisture_min_20.replace('%', ''))
            min_40_val = float(soil_moisture_min_40.replace('%', ''))
            soil_moisture_min = f"{min(min_20_val, min_40_val):.1f}%"
        elif soil_moisture_min_20 != 'N/A':
            soil_moisture_min = soil_moisture_min_20
        elif soil_moisture_min_40 != 'N/A':
            soil_moisture_min = soil_moisture_min_40
        else:
            soil_moisture_min = 'N/A'
        
        overview_data.append({
            'SCAN Site': station_name,
            'Elevation': station['Elevation'],
            'Distance to Installation': station['Distance to Installation'],
            'Soil Moisture Minimum': soil_moisture_min,
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
    
    clean_20 = remove_outliers(values_20)
    clean_40 = remove_outliers(values_40)
    
    max_20 = clean_20.max() if not clean_20.empty else None
    max_40 = clean_40.max() if not clean_40.empty else None
    
    ax.plot(soil_temp_20_df['date'], values_20, 'b-', linewidth=1, alpha=0.7, label='Soil Temp -20"')
    ax.plot(soil_temp_40_df['date'], values_40, 'r-', linewidth=1, alpha=0.7, label='Soil Temp -40"')
    
    if max_20 is not None:
        max_date_20 = soil_temp_20_df.loc[values_20.idxmax(), 'date']
        ax.annotate(f'Max: {max_20:.1f}°F', 
                   xy=(max_date_20, max_20), 
                   xytext=(10, 10), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='blue', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', color='blue'))
    
    if max_40 is not None:
        max_date_40 = soil_temp_40_df.loc[values_40.idxmax(), 'date']
        ax.annotate(f'Max: {max_40:.1f}°F', 
                   xy=(max_date_40, max_40), 
                   xytext=(10, -20), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', color='red'))
    
    ax.set_title(f'{station_name} - Soil Temperature Maximum', fontsize=14, fontweight='bold')
    ax.set_ylabel('Soil Temperature (°F)', fontsize=12)
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
    
    clean_values = remove_outliers(values)
    max_temp = clean_values.max() if not clean_values.empty else None
    
    ax.plot(air_temp_max_df['date'], values, 'b-', linewidth=1, alpha=0.7, label='Air Temperature Max')
    
    if max_temp is not None:
        max_date = air_temp_max_df.loc[values.idxmax(), 'date']
        ax.annotate(f'Max: {max_temp:.1f}°F', 
                   xy=(max_date, max_temp), 
                   xytext=(10, 10), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='blue', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', color='blue'))
    
    ax.set_title(f'{station_name} - Ambient Air Temperature Maximum', fontsize=14, fontweight='bold')
    ax.set_ylabel('Air Temperature (°F)', fontsize=12)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig

def fig_to_buffer(fig):
    """Convert matplotlib figure to bytes for download"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    return buf

# Main app
def main():
    st.markdown('<h1 class="main-header">SCAN Site Analyzer</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    This app helps you find the closest USDA SCAN (Soil Climate Analysis Network) sites 
    and analyze soil moisture, soil temperature, and ambient temperature data.
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for input
    with st.sidebar:
        st.header("Location Input")
        st.write("Enter coordinates to find nearby SCAN sites:")
        
        col1, col2 = st.columns(2)
        with col1:
            latitude = st.number_input("Latitude", value=45.6790, format="%.6f")
        with col2:
            longitude = st.number_input("Longitude", value=-111.0426, format="%.6f")
        
        num_sites = st.slider("Number of closest sites to show", 1, 10, 5)
        
        if st.button("Find SCAN Sites", type="primary"):
            st.session_state.latitude = latitude
            st.session_state.longitude = longitude
            st.session_state.num_sites = num_sites
            st.session_state.search_triggered = True
    
    # Main content
    if hasattr(st.session_state, 'search_triggered') and st.session_state.search_triggered:
        latitude = st.session_state.latitude
        longitude = st.session_state.longitude
        num_sites = st.session_state.num_sites
        
        st.markdown(f'<h2 class="sub-header">SCAN Sites near ({latitude}, {longitude})</h2>', unsafe_allow_html=True)
        
        # Get nearby stations
        with st.spinner("Finding nearby SCAN sites..."):
            nearby_stations = get_closest_scan_sites(latitude, longitude, num_sites)
        
        if not nearby_stations.empty:
            # Display stations
            st.dataframe(nearby_stations, use_container_width=True)
            
            # Create overview table
            st.markdown('<h3 class="sub-header">Site Overview</h3>', unsafe_allow_html=True)
            overview_table = create_station_overview(nearby_stations)
            st.dataframe(overview_table, use_container_width=True)
            
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
            
            # Station details with all 5 plots
            st.markdown('<h3 class="sub-header">Detailed Analysis</h3>', unsafe_allow_html=True)
            selected_station = st.selectbox(
                "Select a station for detailed analysis:",
                nearby_stations['SCAN Site'].tolist()
            )
            
            if selected_station:
                station_data = nearby_stations[nearby_stations['SCAN Site'] == selected_station].iloc[0]
                station_triplet = station_data['Station Triplet']
                
                with st.spinner(f"Loading detailed data for {selected_station}..."):
                    sensor_dfs = get_station_sensor_data(station_triplet)
                
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
                    
                    # Download all plots as PNG
                    st.markdown("#### Download Plots")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        moisture_buf = fig_to_buffer(fig_moisture)
                        st.download_button(
                            label="Download Soil Moisture Plot",
                            data=moisture_buf,
                            file_name=f"{selected_station}_soil_moisture.png",
                            mime="image/png"
                        )
                    
                    with col2:
                        soil_temp_buf = fig_to_buffer(fig_soil_temp)
                        st.download_button(
                            label="Download Soil Temp Plot",
                            data=soil_temp_buf,
                            file_name=f"{selected_station}_soil_temperature.png",
                            mime="image/png"
                        )
                    
                    with col3:
                        ambient_temp_buf = fig_to_buffer(fig_ambient_temp)
                        st.download_button(
                            label="Download Ambient Temp Plot",
                            data=ambient_temp_buf,
                            file_name=f"{selected_station}_ambient_temperature.png",
                            mime="image/png"
                        )
                
                else:
                    st.warning("Some sensor data is missing for this station.")
        
        else:
            st.error("No SCAN sites found near the specified location.")
    
    else:
        # Welcome screen
        st.info("Enter coordinates in the sidebar to get started!")
        
        # About section
        st.markdown('<h3 class="sub-header">About SCAN Sites</h3>', unsafe_allow_html=True)
        st.write("""
        The Soil Climate Analysis Network (SCAN) provides nationwide soil moisture and 
        climate data collected from over 200 stations across the United States.
        
        **Data available includes:**
        - Soil moisture at 20" and 40" depths
        - Soil temperature at 20" and 40" depths  
        - Ambient air temperature
        - Precipitation
        - And more...
        """)

if __name__ == "__main__":
    main()
