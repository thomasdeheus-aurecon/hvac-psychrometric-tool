import streamlit as st
import psychrolib as psy
import pandas as pd

# Set the unit system to SI
psy.SetUnitSystem(psy.SI)

st.title("🌡️ Psychrometric Calculator")
st.write("Calculate psychrometric properties of moist air using SI units")

# Sidebar for inputs
st.sidebar.header("Input Parameters")

# 1. Barometric Pressure Input
st.sidebar.subheader("1. Barometric Pressure")
pressure_method = st.sidebar.radio(
    "Based on:",
    ["Actual Pressure (kPa)", "Elevation (meters)"]
)

if pressure_method == "Actual Pressure (kPa)":
    pressure = st.sidebar.number_input(
        "Barometric Pressure (kPa)",
        min_value=50.0,
        max_value=110.0,
        value=101.325,
        step=0.1,
        format="%.3f"
    )
else:
    elevation = st.sidebar.number_input(
        "Elevation (meters)",
        min_value=-500.0,
        max_value=5000.0,
        value=0.0,
        step=10.0
    )
    # Calculate pressure from elevation using standard atmosphere
    pressure = 101.325 * (1 - 2.25577e-5 * elevation) ** 5.2559

st.sidebar.write(f"**Pressure: {pressure:.3f} kPa**")

# 2. Dry Bulb Temperature
st.sidebar.subheader("2. Dry Bulb Temperature")
dry_bulb = st.sidebar.number_input(
    "Dry Bulb Temperature (°C)",
    min_value=-50.0,
    max_value=100.0,
    value=25.0,
    step=0.1,
    format="%.1f"
)

# 3. Humidity Parameter
st.sidebar.subheader("3. Humidity Measurement")
humidity_method = st.sidebar.selectbox(
    "Humidity measured as:",
    ["Relative Humidity (%)", "Wet Bulb (°C)", "Dew Point (°C)"]
)

if humidity_method == "Relative Humidity (%)":
    humidity_value = st.sidebar.number_input(
        "Relative Humidity (%)",
        min_value=0.0,
        max_value=100.0,
        value=50.0,
        step=1.0,
        format="%.1f"
    )
    rel_hum = humidity_value / 100.0
elif humidity_method == "Wet Bulb (°C)":
    humidity_value = st.sidebar.number_input(
        "Wet Bulb Temperature (°C)",
        min_value=-50.0,
        max_value=100.0,
        value=20.0,
        step=0.1,
        format="%.1f"
    )
    wet_bulb = humidity_value
elif humidity_method == "Dew Point (°C)":
    humidity_value = st.sidebar.number_input(
        "Dew Point Temperature (°C)",
        min_value=-50.0,
        max_value=100.0,
        value=15.0,
        step=0.1,
        format="%.1f"
    )
    dew_point = humidity_value

# Optional: Wind Chill
st.sidebar.subheader("Optional: Wind Chill")
calculate_wind_chill = st.sidebar.checkbox("Calculate Wind Chill")
if calculate_wind_chill:
    wind_speed = st.sidebar.number_input(
        "Wind Speed (m/s)",
        min_value=0.0,
        max_value=50.0,
        value=5.0,
        step=0.5
    )

# Calculate button
calculate = st.sidebar.button("Calculate Psychrometric Properties", type="primary")

# Main content area
if calculate:
    try:
        # Convert pressure from kPa to Pa for PsychroLib
        pressure_pa = pressure * 1000
        
        # Calculate based on the humidity input method
        if humidity_method == "Relative Humidity (%)":
            # Already have rel_hum
            hum_ratio = psy.GetHumRatioFromRelHum(dry_bulb, rel_hum, pressure_pa)
            wet_bulb = psy.GetTWetBulbFromRelHum(dry_bulb, rel_hum, pressure_pa)
            dew_point = psy.GetTDewPointFromRelHum(dry_bulb, rel_hum)
        elif humidity_method == "Wet Bulb (°C)":
            hum_ratio = psy.GetHumRatioFromTWetBulb(dry_bulb, wet_bulb, pressure_pa)
            rel_hum = psy.GetRelHumFromHumRatio(dry_bulb, hum_ratio, pressure_pa)
            dew_point = psy.GetTDewPointFromHumRatio(dry_bulb, hum_ratio, pressure_pa)
        else:  # Dew Point
            hum_ratio = psy.GetHumRatioFromTDewPoint(dew_point, pressure_pa)
            rel_hum = psy.GetRelHumFromHumRatio(dry_bulb, hum_ratio, pressure_pa)
            wet_bulb = psy.GetTWetBulbFromHumRatio(dry_bulb, hum_ratio, pressure_pa)
        
        # Calculate all other properties
        enthalpy = psy.GetMoistAirEnthalpy(dry_bulb, hum_ratio)
        specific_volume = psy.GetMoistAirVolume(dry_bulb, hum_ratio, pressure_pa)
        density = psy.GetMoistAirDensity(dry_bulb, hum_ratio, pressure_pa)
        
        # Additional properties
        sat_hum_ratio = psy.GetSatHumRatio(dry_bulb, pressure_pa)
        degree_of_saturation = psy.GetDegreeOfSaturation(dry_bulb, hum_ratio, pressure_pa)
        vapor_pressure = psy.GetVapPresFromHumRatio(hum_ratio, pressure_pa)
        
        # Display results
        st.header("📊 Calculated Psychrometric Properties")
        
        # Chart Properties Table
        st.subheader("Chart Properties")
        chart_data = {
            "Property": [
                "Barometric Pressure",
                "Dry Bulb",
                "Wet Bulb",
                "Dew Point",
                "Enthalpy",
                "Relative Humidity",
                "Humidity Ratio",
                "Moist Air Specific Volume"
            ],
            "Value": [
                f"{pressure:.3f}",
                f"{dry_bulb:.2f}",
                f"{wet_bulb:.2f}",
                f"{dew_point:.2f}",
                f"{enthalpy:.2f}",
                f"{rel_hum * 100:.2f}",
                f"{hum_ratio:.6f}",
                f"{specific_volume:.4f}"
            ],
            "Units": [
                "kPa",
                "°C",
                "°C",
                "°C",
                "kJ/kg",
                "%",
                "kg_v/kg_a",
                "m³/kg_a"
            ]
        }
        chart_df = pd.DataFrame(chart_data)
        st.table(chart_df)
        
        # Other Thermodynamic Properties
        st.subheader("Other Thermodynamic Properties")
        
        # Calculate additional properties
        partial_press_water = vapor_pressure / 1000  # Convert to kPa
        sat_vapor_pressure = psy.GetSatVapPres(dry_bulb) / 1000  # kPa
        
        other_data = {
            "Property": [
                "Specific Humidity",
                "Absolute Humidity",
                "Degree of Saturation",
                "Density",
                "Partial Pressure of Water Vapor",
                "Saturation Vapor Pressure"
            ],
            "Value": [
                f"{hum_ratio:.6f}",
                f"{hum_ratio * density:.6f}",
                f"{degree_of_saturation * 100:.2f}",
                f"{density:.4f}",
                f"{partial_press_water:.3f}",
                f"{sat_vapor_pressure:.3f}"
            ],
            "Units": [
                "kg_v/kg",
                "kg_v/m³",
                "%",
                "kg/m³",
                "kPa",
                "kPa"
            ]
        }
        other_df = pd.DataFrame(other_data)
        st.table(other_df)
        
        # Wind Chill (if requested)
        if calculate_wind_chill:
            # Wind chill formula (Environment Canada/US NWS)
            if dry_bulb <= 10 and wind_speed > 1.34:
                wind_chill = 13.12 + 0.6215 * dry_bulb - 11.37 * (wind_speed * 3.6) ** 0.16 + 0.3965 * dry_bulb * (wind_speed * 3.6) ** 0.16
                st.subheader("🌬️ Wind Chill")
                st.metric("Wind Chill Temperature", f"{wind_chill:.1f} °C")
            else:
                st.info("Wind chill is only calculated for temperatures ≤ 10°C and wind speeds > 1.34 m/s")
        
        # Success message
        st.success("✅ Calculations completed successfully!")
        
    except Exception as e:
        st.error(f"❌ Error in calculation: {str(e)}")
        st.info("Please check your input values and try again. Ensure wet bulb temperature is not higher than dry bulb temperature.")

else:
    st.info("👈 Enter your parameters in the sidebar and click 'Calculate' to see results")
    
    # Display instructions
    st.markdown("""
    ### How to Use
    1. **Select Barometric Pressure**: Choose between entering actual pressure or elevation
    2. **Enter Dry Bulb Temperature**: The air temperature measured by a standard thermometer
    3. **Choose Humidity Method**: Select one of:
       - Relative Humidity (%)
       - Wet Bulb Temperature (°C)
       - Dew Point Temperature (°C)
    4. **Optional**: Enable wind chill calculation and enter wind speed
    5. Click **Calculate** to see all psychrometric properties
    
    ### About Psychrometric Properties
    - **Dry Bulb**: Air temperature measured by standard thermometer
    - **Wet Bulb**: Temperature measured with a wet cloth over thermometer bulb
    - **Dew Point**: Temperature at which water vapor condenses
    - **Relative Humidity**: Ratio of actual to saturated vapor pressure
    - **Humidity Ratio**: Mass of water vapor per mass of dry air
    - **Enthalpy**: Total heat content of moist air
    - **Specific Volume**: Volume per unit mass of dry air
    """)