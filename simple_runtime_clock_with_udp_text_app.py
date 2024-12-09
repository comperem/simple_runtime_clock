# run with steps:
# (1) start venv: source .venv/bin/activate
# (2) install python packages: uv pip install -r requirements.txt
# (3) streamlit run simple_runtime_clock_with_udp_text_app.py

import streamlit as st
import time
from datetime import datetime
import socket
import psutil
import threading

# Set the total runtime start time if not already set
if "total_start_time" not in st.session_state:
    st.session_state.total_start_time = time.time()

# Set the restart start time (resets every time the app starts)
st.session_state.restart_start_time = time.time()

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

# Function to set up the UDP socket for non-blocking reception with SO_REUSEADDR
def setup_udp_socket():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow address reuse
    udp_socket.bind(('0.0.0.0', 5000))  # Listen on port 5000
    udp_socket.setblocking(False)  # Set socket to non-blocking
    return udp_socket

# Set up the UDP socket once
udp_socket = setup_udp_socket()

# Set the title and other visual elements
st.title("Streamlit Periodic Clock Updates with UDP Messages")

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
    .total-runtime-bar {
        background-color: #fffacd;
        color: #000;
        font-size: 20px;
        text-align: center;
        padding: 5px 0;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .restart-runtime-bar {
        background-color: #d4edda;
        color: #000;
        font-size: 20px;
        text-align: center;
        padding: 5px 0;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .message-bar {
        background-color: #fce4b7;
        color: #000;
        font-size: 18px;
        text-align: center;
        padding: 10px 0;
        border-radius: 5px;
        margin-top: 20px;
    }
    .legend {
        font-size: 14px;
        font-style: italic;
        color: #666;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Containers for the clocks and messages
current_time_container = st.empty()
total_runtime_container = st.empty()
restart_runtime_container = st.empty()
message_container = st.empty()
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

# Set up variables for the last message and timestamp
last_message = ""
last_timestamp = ""

# Main loop to update clocks and display messages
while True:
    # Check if a new UDP message is available
    try:
        message, _ = udp_socket.recvfrom(1024)  # Try to receive the message
        last_message = message.decode('utf-8')  # Update message
        last_timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")  # Timestamp of reception
    except BlockingIOError:
        pass  # No message, continue looping

    total_elapsed_seconds = time.time() - st.session_state.total_start_time
    restart_elapsed_seconds = time.time() - st.session_state.restart_start_time
    st.session_state.total_runtime = format_runtime(total_elapsed_seconds)
    st.session_state.restart_runtime = format_runtime(restart_elapsed_seconds)

    # Display current date and time with description and timezone
    current_time_container.markdown(
        f'''
        <div class="current-time-bar">
            Current Date: {datetime.now().strftime("%Y-%m-%d")} <br>
            Current Time: {datetime.now().strftime("%I:%M:%S %p")} <br>
            Timezone: {current_timezone}
        </div>
        ''',
        unsafe_allow_html=True,
    )
    # Display total runtime clock with description
    total_runtime_container.markdown(
        f'<div class="total-runtime-bar">Total Runtime: {st.session_state.total_runtime}</div>',
        unsafe_allow_html=True,
    )
    # Display restart runtime clock with description
    restart_runtime_container.markdown(
        f'<div class="restart-runtime-bar">Restart Runtime: {st.session_state.restart_runtime}</div>',
        unsafe_allow_html=True,
    )

    # If a message is received, display it
    if last_message:
        message_container.markdown(
            f'<div class="message-bar">Latest Message: {last_message} <br>Received at: {last_timestamp}</div>',
            unsafe_allow_html=True,
        )

    time.sleep(1)
