import streamlit as st
import psychrolib as psy
import pandas as pd
from psychrochart import PsychroChart
import matplotlib.pyplot as plt
import json
import distinctipy

# number of colours to generate
N = 30
# generate N visually distinct colours
colours = distinctipy.get_colors(N)


# Set the unit system to SI
psy.SetUnitSystem(psy.SI)

# Initialize session state for points and connectors
if 'points_data' not in st.session_state:
    st.session_state.points_data = []  # List of dicts with point info
if 'point_counter' not in st.session_state:
    st.session_state.point_counter = 1
#st.set_page_config(layout="wide")
st.title("🌡️ Psychrometric Calculator")
st.write("Calculate and plot psychrometric properties of moist air using SI units.")

# Main page - Input Parameters Section
st.header("Add New Condition")
# Main content area - calculations happen automatically
if True:
    try:
        
        #st.divider()
        
        # Point Management Section - Now includes name input
        #st.header("💾 Save Point to Chart")
        
        tab1, tab2 = st.tabs(["➕ Add Condition", "🔀 Add Mixed Condition"])
        
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                pressure_method = st.radio(
                    "Barometric Pressure Based on:",
                    ["Actual Pressure (kPa)", "Elevation (meters)"]
                )

            with col2:
                if pressure_method == "Actual Pressure (kPa)":
                    pressure = st.number_input(
                        "Barometric Pressure (kPa)",
                        min_value=50.0,
                        max_value=110.0,
                        value=101.325,
                        step=0.1,
                        format="%.3f"
                    )
                else:
                    elevation = st.number_input(
                        "Elevation (meters)",
                        min_value=-500.0,
                        max_value=5000.0,
                        value=0.0,
                        step=10.0
                    )
                    # Calculate pressure from elevation using standard atmosphere
                    pressure = 101.325 * (1 - 2.25577e-5 * elevation) ** 5.2559
                
                #st.metric("Calculated Pressure", f"{pressure:.3f} kPa")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                new_point_name = st.text_input("Point Name", value=f"Point_{st.session_state.point_counter}", key=f"new_point_name_{st.session_state.point_counter}")
            
            with col2:
                new_point_color = st.color_picker("Color", value=distinctipy.get_hex(colours[st.session_state.point_counter - 1]), key=f"new_point_color_{st.session_state.point_counter}")
            
            # Temperature and Humidity Parameters
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                dry_bulb = st.number_input(
                    "Dry Bulb Temperature (°C)",
                    min_value=-50.0,
                    max_value=100.0,
                    value=25.0,
                    step=0.1,
                    format="%.1f"
                )

            with col2:
                humidity_method = st.selectbox(
                    "Humidity measured as:",
                    ["Relative Humidity (%)", "Wet Bulb (°C)", "Dew Point (°C)"]
                )

            with col3:
                if humidity_method == "Relative Humidity (%)":
                    humidity_value = st.number_input(
                        "Relative Humidity (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=50.0,
                        step=1.0,
                        format="%.1f"
                    )
                    rel_hum = humidity_value / 100.0
                elif humidity_method == "Wet Bulb (°C)":
                    humidity_value = st.number_input(
                        "Wet Bulb Temperature (°C)",
                        min_value=-50.0,
                        max_value=100.0,
                        value=20.0,
                        step=0.1,
                        format="%.1f"
                    )
                    wet_bulb = humidity_value
                elif humidity_method == "Dew Point (°C)":
                    humidity_value = st.number_input(
                        "Dew Point Temperature (°C)",
                        min_value=-50.0,
                        max_value=100.0,
                        value=15.0,
                        step=0.1,
                        format="%.1f"
                    )
                    dew_point = humidity_value

            with col4:
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
                enthalpy = psy.GetMoistAirEnthalpy(dry_bulb, hum_ratio) / 1000  # Convert to kJ/kg
                specific_volume = psy.GetMoistAirVolume(dry_bulb, hum_ratio, pressure_pa)
                density = psy.GetMoistAirDensity(dry_bulb, hum_ratio, pressure_pa)
                
                # Additional properties
                sat_hum_ratio = psy.GetSatHumRatio(dry_bulb, pressure_pa)
                degree_of_saturation = psy.GetDegreeOfSaturation(dry_bulb, hum_ratio, pressure_pa)
                vapor_pressure = psy.GetVapPresFromHumRatio(hum_ratio, pressure_pa)

                st.write("")  # Spacing
                st.write("")  # Spacing
                if st.button("➕ Add Point", type="primary", key="add_input_point", use_container_width=True):
                    # Check for duplicate names
                    existing_names = [p['name'] for p in st.session_state.points_data]
                    if new_point_name in existing_names:
                        st.error(f"❌ Point name '{new_point_name}' already exists. Please use a unique name.")
                    else:
                        # Add the new point
                        new_point = {
                            'name': new_point_name,
                            'type': 'input',
                            'dry_bulb': round(dry_bulb, 2),
                            'rel_hum': round(rel_hum * 100, 2),
                            'wet_bulb': round(wet_bulb, 2),
                            'color': new_point_color,
                            'connects_to': None if len(st.session_state.points_data) == 0 else st.session_state.points_data[-1]['name'],
                            'pressure': pressure
                        }
                        st.session_state.points_data.append(new_point)
                        st.session_state.point_counter += 1
                        st.success(f"✅ Added {new_point_name}")
                        st.rerun()
                        

            
            
        
        with tab2:
            # Get list of input points only (not mixed points)
            input_points = [p['name'] for p in st.session_state.points_data if p.get('type', 'input') == 'input']
            
            if len(input_points) < 2:
                st.info("You need at least 2 input points to create a mixed condition.")
            else:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    mixed_point_name = st.text_input("Mixed Point Name", value=f"Mixed_{st.session_state.point_counter}", key=f"mixed_point_name_{st.session_state.point_counter}")
                
                with col2:
                    mixed_point_color = st.color_picker("Color", value=distinctipy.get_hex(colours[st.session_state.point_counter - 1]), key=f"mixed_point_color_{st.session_state.point_counter}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    source_point1 = st.selectbox("Source Point 1", options=input_points, key="source1")
                
                with col2:
                    source_point2 = st.selectbox("Source Point 2", options=input_points, index=min(1, len(input_points)-1), key="source2")
                
                with col3:
                    mix_ratio1 = st.number_input("Flow Ratio 1", min_value=0.0, max_value=100.0, value=50.0, step=1.0, key="ratio1",
                                                help="Percentage of Source Point 1 in the mix")
                
                mix_ratio2 = 100.0 - mix_ratio1
                st.write(f"Flow Ratio 2: {mix_ratio2:.1f}%")
                
                if st.button("🔀 Add Mixed Condition", type="primary", key="add_mixed_point"):
                    # Check for duplicate names
                    existing_names = [p['name'] for p in st.session_state.points_data]
                    if mixed_point_name in existing_names:
                        st.error(f"❌ Point name '{mixed_point_name}' already exists. Please use a unique name.")
                    elif source_point1 == source_point2:
                        st.error(f"❌ Source points must be different.")
                    else:
                        # Add the mixed point
                        new_mixed_point = {
                            'name': mixed_point_name,
                            'type': 'mixed',
                            'source1': source_point1,
                            'source2': source_point2,
                            'ratio1': mix_ratio1,
                            'ratio2': mix_ratio2,
                            'color': mixed_point_color,
                            'connects_to': None
                        }
                        st.session_state.points_data.append(new_mixed_point)
                        st.session_state.point_counter += 1
                        st.success(f"✅ Added mixed condition {mixed_point_name}")
                        st.rerun()
        
        # Display and edit existing points
        if st.session_state.points_data:
            st.subheader("Plotted Conditions")
            
            # Get list of all point names for connection dropdown
            all_point_names = [p['name'] for p in st.session_state.points_data]
            input_point_names = [p['name'] for p in st.session_state.points_data if p.get('type', 'input') == 'input']
            
            for idx, point in enumerate(st.session_state.points_data):
                point_type = point.get('type', 'input')
                
                # Calculate properties for mixed points dynamically
                if point_type == 'mixed':
                    # Find source points
                    source1_data = next((p for p in st.session_state.points_data if p['name'] == point['source1']), None)
                    source2_data = next((p for p in st.session_state.points_data if p['name'] == point['source2']), None)
                    
                    if source1_data and source2_data:
                        # Calculate humidity ratios for both source points
                        try:
                            hr1 = psy.GetHumRatioFromRelHum(source1_data['dry_bulb'], source1_data['rel_hum']/100, pressure_pa)
                            hr2 = psy.GetHumRatioFromRelHum(source2_data['dry_bulb'], source2_data['rel_hum']/100, pressure_pa)
                            
                            # Calculate mixed properties
                            r1 = point['ratio1'] / 100
                            r2 = point['ratio2'] / 100
                            
                            mixed_db = source1_data['dry_bulb'] * r1 + source2_data['dry_bulb'] * r2
                            mixed_hr = hr1 * r1 + hr2 * r2
                            mixed_rh = psy.GetRelHumFromHumRatio(mixed_db, mixed_hr, pressure_pa) * 100
                            mixed_wb = psy.GetTWetBulbFromHumRatio(mixed_db, mixed_hr, pressure_pa)
                            
                            # Update point data
                            point['dry_bulb'] = round(mixed_db, 1)
                            point['rel_hum'] = round(mixed_rh, 1)
                            point['wet_bulb'] = round(mixed_wb, 1)
                        except:
                            pass
                
                # Display point based on type
                if point_type == 'input':
                    expander_title = f"📍 {point['name']}"
                else:
                    expander_title = f"🔀 {point['name']} (Mixed)"
                
                with st.expander(expander_title, expanded=False):
                    if point_type == 'input':
                        # Input point - fully editable
                        cols = st.columns([2, 2, 2, 2, 1])
                        
                        with cols[0]:
                            new_name = st.text_input(
                                "Point Name",
                                value=point['name'],
                                key=f"name_{idx}"
                            )
                            # Check for duplicates when name changes
                            if new_name != point['name']:
                                other_names = [p['name'] for i, p in enumerate(st.session_state.points_data) if i != idx]
                                if new_name in other_names:
                                    st.error("Duplicate name!")
                                else:
                                    point['name'] = new_name
                        
                        with cols[1]:
                            point['dry_bulb'] = round(st.number_input(
                                "Dry Bulb (°C)",
                                value=float(point['dry_bulb']),
                                step=0.1,
                                format="%.1f",
                                key=f"db_{idx}"
                            ), 2)
                        
                        with cols[2]:
                            point['wet_bulb'] = st.number_input(
                                "Wet Bulb (°C)",
                                value=float(point['wet_bulb']),
                                step=0.1,
                                format="%.1f",
                                key=f"wb_{idx}"
                            )
                        
                        # Recalculate wet bulb based on dry bulb and RH
                        try:
                            point_pressure_pa = point.get('pressure', pressure) * 1000
                            calculated_rh = psy.GetRelHumFromTWetBulb(
                                point['dry_bulb'], 
                                point['wet_bulb'], 
                                point_pressure_pa
                            ) * 100
                            point['rel_hum'] = round(calculated_rh, 1)
                        except:
                            pass
                        
                        with cols[3]:
                            # Connection dropdown - allow None or any other point
                            connection_options = ['None'] + [p for p in all_point_names if p != point['name']]
                            current_connection = point['connects_to'] if point['connects_to'] else 'None'
                            if current_connection not in connection_options:
                                current_connection = 'None'
                            
                            selected_connection = st.selectbox(
                                "Next State",
                                options=connection_options,
                                index=connection_options.index(current_connection),
                                key=f"conn_{idx}"
                            )
                            point['connects_to'] = None if selected_connection == 'None' else selected_connection
                        
                        with cols[4]:
                            point['color'] = st.color_picker(
                                "Color",
                                value=point['color'],
                                key=f"color_{idx}"
                            )
                        
                        # Display calculated wet bulb (read-only)
                        # st.info(f"{point['rel_hum']}% RH")
                    
                    else:  # Mixed point
                        cols = st.columns([2, 2, 2, 2, 2, 1])
                        
                        with cols[0]:
                            new_name = st.text_input(
                                "Point Name",
                                value=point['name'],
                                key=f"name_{idx}"
                            )
                            if new_name != point['name']:
                                other_names = [p['name'] for i, p in enumerate(st.session_state.points_data) if i != idx]
                                if new_name in other_names:
                                    st.error("Duplicate name!")
                                else:
                                    point['name'] = new_name
                        
                        with cols[1]:
                            point['source1'] = st.selectbox(
                                "Source 1",
                                options=input_point_names,
                                index=input_point_names.index(point['source1']) if point['source1'] in input_point_names else 0,
                                key=f"src1_{idx}"
                            )
                        
                        with cols[2]:
                            point['source2'] = st.selectbox(
                                "Source 2",
                                options=input_point_names,
                                index=input_point_names.index(point['source2']) if point['source2'] in input_point_names else 0,
                                key=f"src2_{idx}"
                            )
                        
                        with cols[3]:
                            point['ratio1'] = st.number_input(
                                "Ratio 1 (%)",
                                value=float(point['ratio1']),
                                min_value=0.0,
                                max_value=100.0,
                                step=1.0,
                                key=f"ratio1_{idx}"
                            )
                            point['ratio2'] = 100.0 - point['ratio1']
                            st.caption(f"Ratio 2: {point['ratio2']:.1f}%")
                        
                        with cols[4]:
                            # Connection dropdown
                            connection_options = ['None'] + [p for p in all_point_names if p != point['name']]
                            current_connection = point['connects_to'] if point['connects_to'] else 'None'
                            if current_connection not in connection_options:
                                current_connection = 'None'
                            
                            selected_connection = st.selectbox(
                                "Next State",
                                options=connection_options,
                                index=connection_options.index(current_connection),
                                key=f"conn_{idx}"
                            )
                            point['connects_to'] = None if selected_connection == 'None' else selected_connection
                        
                        with cols[5]:
                            point['color'] = st.color_picker(
                                "Color",
                                value=point['color'],
                                key=f"color_{idx}"
                            )

                        # Display calculated properties (read-only)
                        #st.info(f"**Calculated:** {point['dry_bulb']:.1f}°C DB, {point['wet_bulb']:.1f}°C WB, {point['rel_hum']:.1f}% RH")
                    
                    # Calculate and display full properties table for this point
                    try:
                        point_pressure_pa = point.get('pressure', pressure) * 1000
                        point_db = point['dry_bulb']
                        point_rh = point['rel_hum'] / 100
                        
                        # Calculate all properties
                        point_hr = psy.GetHumRatioFromRelHum(point_db, point_rh, point_pressure_pa)
                        point_wb = psy.GetTWetBulbFromRelHum(point_db, point_rh, point_pressure_pa)
                        point_dp = psy.GetTDewPointFromRelHum(point_db, point_rh)
                        point_enthalpy = psy.GetMoistAirEnthalpy(point_db, point_hr) / 1000
                        point_vol = psy.GetMoistAirVolume(point_db, point_hr, point_pressure_pa)
                        point_density = psy.GetMoistAirDensity(point_db, point_hr, point_pressure_pa)
                        point_vp = psy.GetVapPresFromHumRatio(point_hr, point_pressure_pa) / 1000
                        point_sat_vp = psy.GetSatVapPres(point_db) / 1000
                        point_deg_sat = psy.GetDegreeOfSaturation(point_db, point_hr, point_pressure_pa)
                        
                        # Combined properties table
                        st.subheader("Properties")
                        combined_data = {
                            "Property": [
                                "Barometric Pressure",
                                "Dry Bulb",
                                "Wet Bulb",
                                "Dew Point",
                                "Relative Humidity",
                                "Humidity Ratio",
                                "Enthalpy",
                                "Specific Volume",
                                "Density",
                                "Degree of Saturation",
                                "Absolute Humidity",
                                "Partial Pressure of Water Vapor",
                                "Saturation Vapor Pressure"
                            ],
                            "Value": [
                                f"{point.get('pressure', pressure):.3f}",
                                f"{point_db:.2f}",
                                f"{point_wb:.2f}",
                                f"{point_dp:.2f}",
                                f"{point_rh * 100:.2f}",
                                f"{point_hr:.6f}",
                                f"{point_enthalpy:.2f}",
                                f"{point_vol:.4f}",
                                f"{point_density:.4f}",
                                f"{point_deg_sat * 100:.2f}",
                                f"{point_hr * point_density:.6f}",
                                f"{point_vp:.3f}",
                                f"{point_sat_vp:.3f}"
                            ],
                            "Units": [
                                "kPa",
                                "°C",
                                "°C",
                                "°C",
                                "%",
                                "kg_v/kg_a",
                                "kJ/kg",
                                "m³/kg_a",
                                "kg/m³",
                                "%",
                                "kg_v/m³",
                                "kPa",
                                "kPa"
                            ]
                        }
                        combined_df = pd.DataFrame(combined_data)
                        st.table(combined_df)
                    except Exception as e:
                        st.error(f"Error calculating properties: {str(e)}")
                    
                    # Delete button
                    if st.button(f"🗑️ Delete", key=f"del_{idx}"):
                        st.session_state.points_data.pop(idx)
                        st.rerun()
            
            # Export/Import and Clear buttons
            col1, col2 = st.columns(2)
            
            with col1:
                # Export points to JSON
                export_data = {
                    'points_data': st.session_state.points_data,
                    'point_counter': st.session_state.point_counter
                }
                json_str = json.dumps(export_data, indent=2)
                st.download_button(
                    label="📥 Export Points",
                    data=json_str,
                    file_name="psychrometric_points.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col2:
                if st.button("🗑️ Clear All Points", use_container_width=True):
                    st.session_state.points_data = []
                    st.session_state.point_counter = 1
                    st.rerun()
        else:
            # Show import option even when no points exist
            st.info("No saved points yet. Add points above or import existing data.")
            uploaded_file = st.file_uploader("📤 Import Points", type=['json'], key="import_points_empty")
            if uploaded_file is not None:
                try:
                    import_data = json.loads(uploaded_file.getvalue().decode('utf-8'))
                    st.session_state.points_data = import_data.get('points_data', [])
                    st.session_state.point_counter = import_data.get('point_counter', 1)
                    st.success(f"✅ Imported {len(st.session_state.points_data)} points")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error importing file: {str(e)}")
        
        # Psychrometric Chart
        st.subheader("Psychrometric Chart")
        
        try:
            # Create psychrometric chart
            chart = PsychroChart.create('ashrae')
            ax = chart.plot()
            
            # Convert points_data to psychrochart format
            if st.session_state.points_data:
                points_dict = {}
                connectors_list = []
                arrows_dict = {}
                
                for point in st.session_state.points_data:
                    # Convert hex color to RGBA
                    hex_color = point['color'].lstrip('#')
                    r, g, b = tuple(int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4))
                    
                    points_dict[point['name']] = {
                        'label': point['name'],
                        'style': {
                            'color': [r, g, b, 0.8],
                            'marker': 'o',
                            'markersize': 15
                        },
                        'xy': (point['dry_bulb'], point['rel_hum'])
                    }
                    
                    # Add connector if this point connects to another
                    if point['connects_to']:
                        connectors_list.append({
                            'start': point['name'],
                            'end': point['connects_to'],
                            'label': f"{point['name']} → {point['connects_to']}",
                            'style': {
                                'color': [r, g, b, 0.7],
                                'linewidth': 5,
                                'linestyle': '--'
                            }
                        })
                
                chart.plot_points_dbt_rh(points_dict, connectors_list)

                
                chart.plot_legend(markerscale=.7, frameon=False, fontsize=10, labelspacing=1.2)
            
            # Display the chart
            fig = ax.figure
            st.pyplot(fig)
            plt.close()
        except Exception as chart_error:
            st.warning(f"Could not generate psychrometric chart: {str(chart_error)}")
        
        
    except Exception as e:
        st.error(f"❌ Error in calculation: {str(e)}")
        st.info("Please check your input values and try again. Ensure wet bulb temperature is not higher than dry bulb temperature.")