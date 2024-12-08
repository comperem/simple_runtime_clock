# run with steps:
# (1) start venv: source .venv/bin/activate
# (2) install python packages: uv pip install -r requirements.txt
# (3) streamlit run simple_runtime_clock_app.py

import streamlit as st
import time
from datetime import datetime, timedelta
import socket
import psutil

# Reset the start time each time the app runs
st.session_state.start_time = time.time()

# Get current timezone
current_timezone = datetime.now().astimezone().tzinfo

# Function to get all IPv4 addresses
def get_ipv4_addresses():
    addresses = []
    for interface, snics in psutil.net_if_addrs().items():
        for snic in snics:
            if snic.family == socket.AF_INET:
                addresses.append((interface, snic.address))
    return addresses

# Function to calculate runtime with years, months, days, hours, minutes, and seconds
def format_runtime(seconds):
    years, seconds = divmod(seconds, 365 * 24 * 3600)  # Approximate year as 365 days
    months, seconds = divmod(seconds, 30 * 24 * 3600)  # Approximate month as 30 days
    days, seconds = divmod(seconds, 24 * 3600)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{int(years)} years, {int(months)} months, {int(days)} days, {int(hours):02}:{int(minutes):02}:{int(seconds):02}"

# Function to update clocks
def update_clocks():
    elapsed_seconds = time.time() - st.session_state.start_time
    st.session_state.runtime = format_runtime(elapsed_seconds)
    st.session_state.current_time = datetime.now().strftime("%I:%M:%S %p")  # Current time in AM/PM format

# Periodically update clocks
update_interval = 1  # seconds
st.title("Streamlit Periodic Clock Updates")

# Style for the bars
st.markdown("""
<style>
    .current-time-bar {
        background-color: #d0f0ff;
        color: #000;
        font-size: 20px;
        text-align: center;
        padding: 5px 0;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .runtime-clock-bar {
        background-color: #fffacd;
        color: #000;
        font-size: 20px;
        text-align: center;
        padding: 5px 0;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .legend {
        font-size: 14px;
        font-style: italic;
        color: #666;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Containers for the clocks
current_time_container = st.empty()
runtime_clock_container = st.empty()
ipv4_table_container = st.empty()

# Display IPv4 addresses in a table
ipv4_addresses = get_ipv4_addresses()
st.subheader("Host Machine IPv4 Addresses")
ipv4_table_container.table(
    [{"Interface": iface, "IP Address": ip} for iface, ip in ipv4_addresses]
)

# Display legend
st.markdown(
    '<div class="legend">Current time format: HH:MM:SS AM/PM<br>Runtime format: Years, Months, Days, HH:MM:SS</div>',
    unsafe_allow_html=True,
)

# Main loop to update clocks
while True:
    update_clocks()
    # Display current time with description and timezone
    current_time_container.markdown(
        f'''
        <div class="current-time-bar">
            Current Time: {st.session_state.current_time} <br>
            Timezone: {current_timezone}
        </div>
        ''',
        unsafe_allow_html=True,
    )
    # Display runtime clock with description in a styled bar
    runtime_clock_container.markdown(
        f'<div class="runtime-clock-bar">Runtime: {st.session_state.runtime}</div>',
        unsafe_allow_html=True,
    )
    time.sleep(update_interval)
