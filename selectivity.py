import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import io

# Setup the web page layout
st.set_page_config(page_title="Relay Coordination", layout="wide")

def calculate_curve(i_vector, curve_type, i_set, tms, t_pickup, i_dt, t_dt, i_inst):
    times = []
    for i in i_vector:
        if i <= i_set:
            times.append(np.nan)
        elif i >= i_inst:
            times.append(0.02) # Instantaneous step (20ms physical delay)
        elif i >= i_dt:
            times.append(t_dt) # Definite time short-circuit step
        elif curve_type == "DT":
            times.append(t_pickup) # Definite Time constant delay
        else:
            # IEC Normal Inverse calculation
            t = (0.14 * tms) / ((i / i_set)**0.02 - 1)
            times.append(t)
    return times

# --- SIDEBAR: USER INPUTS ---
st.sidebar.title("System Parameters")

# Base system settings
base_voltage = st.sidebar.number_input("Base System Voltage (kV)", value=20.0, step=1.0)
num_relays = st.sidebar.number_input("How many relays do you want to plot?", min_value=1, max_value=10, value=2, step=1)

st.sidebar.markdown("---")

relays_data = []

# Dynamically generate sliders for the number of relays chosen
for index in range(int(num_relays)):
    st.sidebar.markdown(f"### Relay {index + 1}")
    name = st.sidebar.text_input(f"Relay {index + 1} Name", value=f"Relay {index + 1}", key=f"name_{index}")
    
    # Voltage level check
    diff_voltage = st.sidebar.checkbox(f"Is this relay on a different voltage level?", key=f"volt_check_{index}")
    if diff_voltage:
        relay_voltage = st.sidebar.number_input(f"Voltage of {name} (kV)", value=60.0, step=1.0, key=f"volt_{index}")
        ratio = relay_voltage / base_voltage
    else:
        ratio = 1.0

    # Curve Type Selection
    curve_type = st.sidebar.selectbox("Curve Type", ["NI (Normal Inverse)", "DT (Definite Time)"], key=f"curve_{index}")
    curve_code = "NI" if "NI" in curve_type else "DT"

    # Current & Time settings using SLIDERS
    i_set = st.sidebar.slider(f"I> Pickup Current (A)", min_value=10.0, max_value=3000.0, value=600.0, step=10.0, key=f"iset_{index}")
    
    # Show TMS for NI, or Fixed Time for DT
    if curve_code == "NI":
        tms = st.sidebar.slider(f"TMS (Time Multiplier)", min_value=0.01, max_value=1.00, value=0.05, step=0.01, key=f"tms_{index}")
        t_pickup = None
    else:
        tms = None
        t_pickup = st.sidebar.slider(f"T> Delay (s)", min_value=0.05, max_value=5.00, value=1.00, step=0.05, key=f"tpick_{index}")

    i_dt = st.sidebar.slider(f"I>> Short Circuit (A)", min_value=50.0, max_value=10000.0, value=1500.0, step=50.0, key=f"idt_{index}")
    t_dt = st.sidebar.slider(f"T>> Delay (s)", min_value=0.05, max_value=2.00, value=0.20, step=0.01, key=f"tdt_{index}")
    i_inst = st.sidebar.slider(f"I>>> Instantaneous (A)", min_value=100.0, max_value=20000.0, value=4000.0, step=100.0, key=f"iinst_{index}")
    
    # Store the calculated (referred) values
    relays_data.append({
        "name": name,
        "curve_code": curve_code,
        "i_set": i_set * ratio,
        "tms": tms,
        "t_pickup": t_pickup,
        "i_dt": i_dt * ratio,
        "t_dt": t_dt,
        "i_inst": i_inst * ratio,
        "ratio": ratio,
        "original_i_set": i_set # Stored for the PDF table
    })
    st.sidebar.markdown("---")


# --- MAIN PAGE: GRAPH & EXPORT ---
st.title("Protection Relay Coordination Simulator")

# Two columns for layout (Title and Export Button)
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"**Note:** All currents displayed on the graph are referred to the base voltage of **{base_voltage} kV**.")

# Generate X-axis points (100 to 50000 Amps)
curenti_x = np.logspace(2, 4.7, 3000) 

# Create the main plot
fig_graph, ax = plt.subplots(figsize=(12, 7)) 

# Plot each relay curve
for relay in relays_data:
    timpi_y = calculate_curve(
        curenti_x, 
        relay["curve_code"],
        relay["i_set"], 
        relay["tms"], 
        relay["t_pickup"],
        relay["i_dt"], 
        relay["t_dt"], 
        relay["i_inst"]
    )
    
    legend_label = relay["name"]
    if relay["ratio"] != 1.0:
        legend_label += f" (Ref {base_voltage}kV)"
        
    ax.plot(curenti_x, timpi_y, label=legend_label, linewidth=2.5)

# Graph formatting
ax.set_xscale('log')
ax.set_yscale('log')
ax.grid(True, which="both", ls="-", color="lightgray", alpha=0.7)
ax.grid(True, which="minor", ls=":", color="lightgray", alpha=0.5)

ax.set_ylim(0.01, 100)
ax.set_xlim(100, 50000)
ax.set_xlabel("Current (A)")
ax.set_ylabel("Operating Time (s)")
ax.set_title("Selectivity Graph")
ax.legend(fontsize=11)

# Display the plot in the web app
st.pyplot(fig_graph)

# --- PDF GENERATION LOGIC ---
pdf_buffer = io.BytesIO()
with PdfPages(pdf_buffer) as pdf:
    # Page 1: The Graph
    pdf.savefig(fig_graph, bbox_inches='tight')
    
    # Page 2: The Settings Table
    fig_table, ax_table = plt.subplots(figsize=(12, 7))
    ax_table.axis('tight')
    ax_table.axis('off')
    
    # Define table headers
    table_data = [["Relay Name", "Curve Type", "Ratio", "I> Pickup", "TMS / T> Delay", "I>> Step", "T>> Delay", "I>>> Inst."]]
    
    # Populate table rows
    for r in relays_data:
        delay_val = f"TMS = {r['tms']}" if r['curve_code'] == "NI" else f"{r['t_pickup']} s"
        table_data.append([
            r['name'], 
            r['curve_code'], 
            f"{r['ratio']:.2f}",
            f"{r['original_i_set']:.1f} A", 
            delay_val, 
            f"{r['i_dt'] / r['ratio']:.1f} A", 
            f"{r['t_dt']} s", 
            f"{r['i_inst'] / r['ratio']:.1f} A"
        ])
        
    # Create the table visually
    table = ax_table.table(cellText=table_data, loc='center', cellLoc='center')
    table.scale(1, 2) # Adjust row height
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    plt.title(f"Relay Settings Summary (Base Voltage: {base_voltage} kV)", fontsize=14, fontweight='bold', pad=20)
    
    pdf.savefig(fig_table, bbox_inches='tight')

# Add the Download Button to the top right column
with col2:
    st.download_button(
        label="📄 Export Graph & Settings (PDF)",
        data=pdf_buffer.getvalue(),
        file_name="Relay_Coordination_Report.pdf",
        mime="application/pdf",
        use_container_width=True
    )
