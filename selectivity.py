import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import FormatStrFormatter
import io

st.set_page_config(page_title="Relay Coordination", layout="wide")

def calculate_curve(i_vector, curve_type, i_set, tms, t_pickup, i_dt, t_dt, i_inst):
    times = []
    for i in i_vector:
        if i <= i_set:
            times.append(np.nan)
        elif i >= i_inst:
            # Curba cade direct la 0.001 secunde (limita de jos a graficului)
            times.append(0.001) 
        elif i >= i_dt:
            times.append(t_dt)
        elif curve_type == "DT":
            times.append(t_pickup)
        else:
            # IEC Normal Inverse
            t = (0.14 * tms) / ((i / i_set)**0.02 - 1)
            times.append(t)
    return times

# --- SIDEBAR ---
st.sidebar.title("System Parameters")

ref_voltage = st.sidebar.number_input("Graph Reference Voltage (kV)", value=20.0, step=1.0)
num_relays = st.sidebar.number_input("Number of relays to plot", min_value=1, max_value=10, value=5, step=1)

st.sidebar.markdown("---")

relays_data = []

# Culori predefinite
default_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

for index in range(int(num_relays)):
    st.sidebar.markdown(f"### Relay {index + 1}")
    name = st.sidebar.text_input(f"Name", value=f"Relay {index + 1}", key=f"name_{index}")
    
    hex_color = default_colors[index % len(default_colors)]
    color = st.sidebar.color_picker("Curve Color", value=hex_color, key=f"color_{index}")

    relay_voltage = st.sidebar.number_input(f"Relay Actual Voltage (kV)", value=20.0, step=1.0, key=f"volt_{index}")
    ratio = relay_voltage / ref_voltage

    curve_type = st.sidebar.selectbox("Curve Type", ["NI (Normal Inverse)", "DT (Definite Time)"], key=f"curve_{index}")
    curve_code = "NI" if "NI" in curve_type else "DT"

    i_set = st.sidebar.number_input(f"I> Pickup Current (A)", min_value=10.0, max_value=3000.0, value=600.0, step=10.0, key=f"iset_{index}")
    
    if curve_code == "NI":
        tms = st.sidebar.number_input(f"TMS (Time Multiplier)", min_value=0.01, max_value=1.00, value=0.05, step=0.01, key=f"tms_{index}")
        t_pickup = None
    else:
        tms = None
        t_pickup = st.sidebar.number_input(f"T> Delay (s)", min_value=0.001, max_value=5.000, value=1.000, step=0.01, format="%.3f", key=f"tpick_{index}")

    i_dt = st.sidebar.number_input(f"I>> Short Circuit (A)", min_value=50.0, max_value=15000.0, value=1500.0, step=10.0, key=f"idt_{index}")
    t_dt = st.sidebar.number_input(f"T>> Delay (s)", min_value=0.01, max_value=5.00, value=0.20, step=0.01, key=f"tdt_{index}")
    i_inst = st.sidebar.number_input(f"I>>> Instantaneous (A)", min_value=100.0, max_value=50000.0, value=4000.0, step=50.0, key=f"iinst_{index}")
    
    relays_data.append({
        "name": name,
        "color": color,
        "curve_code": curve_code,
        "relay_voltage": relay_voltage,
        "ratio": ratio,
        "i_set_graph": i_set * ratio,
        "i_dt_graph": i_dt * ratio,
        "i_inst_graph": i_inst * ratio,
        "i_set_real": i_set,
        "i_dt_real": i_dt,
        "i_inst_real": i_inst,
        "tms": tms,
        "t_pickup": t_pickup,
        "t_dt": t_dt,
    })
    st.sidebar.markdown("---")

# --- MAIN PAGE & GRAPH ---
st.title("Protection Relay Selectivity")

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"**Note:** Currents on the graph are mapped to the reference voltage of **{ref_voltage} kV**.")

curenti_x = np.logspace(1, 5, 4000) 

fig_graph, ax = plt.subplots(figsize=(10, 5.5)) 

for r in relays_data:
    timpi_y = calculate_curve(
        curenti_x, 
        r["curve_code"],
        r["i_set_graph"], 
        r["tms"], 
        r["t_pickup"],
        r["i_dt_graph"], 
        r["t_dt"], 
        r["i_inst_graph"]
    )
    
    label = r["name"]
    if r["ratio"] != 1.0:
        label += f" ({r['relay_voltage']}kV → {ref_voltage}kV)"
        
    ax.plot(curenti_x, timpi_y, label=label, color=r["color"], linewidth=2.0)

ax.set_xscale('log')
ax.set_yscale('log')

# --- Eliminarea notației științifice și afișarea exactă a zecimalelor ---
ax.xaxis.set_major_formatter(FormatStrFormatter('%g'))
ax.yaxis.set_major_formatter(FormatStrFormatter('%g'))
# ------------------------------------------------------------------------

ax.grid(True, which="major", ls="-", color="gray", alpha=0.8, linewidth=0.8)
ax.grid(True, which="minor", ls="--", color="gray", alpha=0.5, linewidth=0.5)

# Limitele graficului identice cu Excel
ax.set_ylim(0.001, 1000)
ax.set_xlim(50, 100000)
ax.set_xlabel(f"Current (A) at {ref_voltage} kV level")
ax.set_ylabel("Operating Time (s)")
ax.legend(fontsize=10)

st.pyplot(fig_graph, use_container_width=False)

# --- PDF EXPORT ---
pdf_buffer = io.BytesIO()
with PdfPages(pdf_buffer) as pdf:
    pdf.savefig(fig_graph, bbox_inches='tight')
    
    fig_table, ax_table = plt.subplots(figsize=(10, 5))
    ax_table.axis('tight')
    ax_table.axis('off')
    
    table_data = [["Relay Name", "Type", "Voltage", "I> Set", "Time (TMS/DT)", "I>> Set", "T>>", "I>>> Inst."]]
    
    for r in relays_data:
        delay_val = f"TMS = {r['tms']}" if r['curve_code'] == "NI" else f"{r['t_pickup']} s"
        table_data.append([
            r['name'], 
            r['curve_code'], 
            f"{r['relay_voltage']} kV",
            f"{r['i_set_real']:.1f} A", 
            delay_val, 
            f"{r['i_dt_real']:.1f} A", 
            f"{r['t_dt']} s", 
            f"{r['i_inst_real']:.1f} A"
        ])
        
    table = ax_table.table(cellText=table_data, loc='center', cellLoc='center')
    table.scale(1, 1.8)
    table.set_fontsize(9)
    plt.title("Relay Settings Summary", fontsize=12, fontweight='bold', pad=15)
    
    pdf.savefig(fig_table, bbox_inches='tight')

with col2:
    st.download_button(
        label="📄 Export Graph & Settings",
        data=pdf_buffer.getvalue(),
        file_name="Selectivity_Report.pdf",
        mime="application/pdf",
        use_container_width=True
    )
