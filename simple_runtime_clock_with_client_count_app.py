# run with steps:
# (1) start venv: source .venv/bin/activate
# (2) install python packages: uv pip install -r requirements.txt
# (3) streamlit run simple_runtime_clock_with_client_count_app.py


import streamlit as st
import time
from datetime import datetime, timedelta
import socket
import psutil
from multiprocessing import Manager

# Cache shared manager to persist across sessions
@st.cache_resource
def get_shared_manager():
    manager = Manager()
    return manager.dict()  # Shared dictionary to store client heartbeats

# Initialize shared state
shared_state = get_shared_manager()

# Get the unique client ID
client_id = f"{time.time()}-{socket.gethostname()}"

# Add or update the client's heartbeat
shared_state[client_id] = time.time()

# Function to clean up stale clients
def cleanup_clients(timeout=10):
    """Remove clients that haven't sent heartbeats within the timeout."""
    now = time.time()
    stale_clients = [
        client for client, last_heartbeat in shared_state.items()
        if now - last_heartbeat > timeout
    ]
    for client in stale_clients:
        del shared_state[client]

# Function to count active clients
def get_active_clients_count():
    cleanup_clients()  # Remove stale clients
    return len(shared_state)

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

# Function to calculate runtime
def format_runtime(seconds):
    days, seconds = divmod(seconds, 24 * 3600)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{int(days)} days, {int(hours):02}:{int(minutes):02}:{int(seconds):02}"

# Periodic update of timers and active clients
st.title("Streamlit App with Accurate Active Client Tracking")

# Style the bars
st.markdown("""
<style>
    .current-time-bar { background-color: #d0f0ff; padding: 10px; border-radius: 5px; margin-bottom: 10px; text-align: center; }
    .total-runtime-bar { background-color: #fffacd; padding: 10px; border-radius: 5px; margin-bottom: 10px; text-align: center; }
    .restart-runtime-bar { background-color: #d4edda; padding: 10px; border-radius: 5px; margin-bottom: 10px; text-align: center; }
    .active-clients-bar { background-color: #ffddcc; padding: 10px; border-radius: 5px; margin-bottom: 10px; text-align: center; }
    .legend { font-size: 14px; font-style: italic; color: #666; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# Initialize timers
if "total_start_time" not in st.session_state:
    st.session_state.total_start_time = time.time()
if "restart_start_time" not in st.session_state:
    st.session_state.restart_start_time = time.time()

# Display containers
current_time_container = st.empty()
total_runtime_container = st.empty()
restart_runtime_container = st.empty()
active_clients_container = st.empty()

# Display IPv4 addresses
st.subheader("Host Machine IPv4 Addresses")
ipv4_addresses = get_ipv4_addresses()
st.table([{"Interface": iface, "IP Address": ip} for iface, ip in ipv4_addresses])

# Legend for timers
st.markdown('<div class="legend">Time format: Days, HH:MM:SS</div>', unsafe_allow_html=True)

# Main loop
while True:
    # Update time information
    current_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    total_runtime = format_runtime(time.time() - st.session_state.total_start_time)
    restart_runtime = format_runtime(time.time() - st.session_state.restart_start_time)
    active_clients = get_active_clients_count()

    # Display current time
    current_time_container.markdown(
        f'<div class="current-time-bar">Current Time: {current_time} (Timezone: {current_timezone})</div>',
        unsafe_allow_html=True,
    )
    # Display total runtime
    total_runtime_container.markdown(
        f'<div class="total-runtime-bar">Total Runtime: {total_runtime}</div>',
        unsafe_allow_html=True,
    )
    # Display restart runtime
    restart_runtime_container.markdown(
        f'<div class="restart-runtime-bar">Restart Runtime: {restart_runtime}</div>',
        unsafe_allow_html=True,
    )
    # Display active clients
    active_clients_container.markdown(
        f'<div class="active-clients-bar">Active Clients: {active_clients}</div>',
        unsafe_allow_html=True,
    )

    # Update the client's heartbeat
    shared_state[client_id] = time.time()

    time.sleep(1)
