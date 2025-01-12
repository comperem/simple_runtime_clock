# MULTIPROCESSING IS NOT GETTING MESSAGES SENT TO THE SUBPROCESS WITH STREAMLIT

# ABANDON MULTIPROCESSING AND TRY THREADS AGAIN IN THE NEXT INCREMENTED FILENAME, _d.py

# streamlit app with runtime clock and
# websocket-based inbound data transfer
# from a command line pythong application [that should work]
# when both machines are behind firewalls
#
# testing locally: WORKS, the streamlit 'stop' q is a little clunky on restart, but it gets it after a few seconds
# community cloud: [unknown]
#
# run with steps:
# (0) create a virtual environment: uv venv     (optionally add python version arg: --python 3.12.1 )
# (1) start venv: source .venv/bin/activate
# (2) install python packages: uv pip install -r requirements.txt
# (3) streamlit run simple_runtime_clock_with_websocket_d.py
#
# (4) run websocket client in another console (but same venv) to send messages:
#       python3 websocket_client_threads_b.py
#
# mdc
# created : 14 Dec 2024
# modified: 29 Dec 2024


import streamlit as st
import time
from datetime import datetime
import psutil
import socket
from simple_websocket_server import WebSocketServer, WebSocket
import code # drop into a python interpreter to debug using: code.interact(local=dict(globals(), **locals()))

import threading
import queue
import socket
import psutil
import os



# Set the total runtime start time if not already set
if "total_start_time" not in st.session_state:
    print('populating st.session_state.total_start_time')
    st.session_state.total_start_time = time.time()

if "stop_server" not in st.session_state:
    st.session_state.stop_server = threading.Event()

if "ws_thread" not in st.session_state:
    st.session_state.thread = []

if "thread_running" not in st.session_state:
    st.session_state.thread_running = False

if 'q' not in st.session_state:
    st.session_state.q     = queue.Queue()

if 'eStop' not in st.session_state:
    st.session_state.eStop = threading.Event()

if 'event' not in st.session_state:
    st.session_state.event = threading.Event()

if 'counter' not in st.session_state:
	st.session_state.counter = 0


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

# Set the title and other visual elements
st.title("Streamlit Periodic Clock Updates with Query Strings")

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

#q = queue.Queue() # for moving messages from websocket handle() method to streamlit main loop
# use multiprocessing queue() with multiprocessing and normal queue.Queue() with threads
#q     = multiprocessing.Queue() # for moving messages from websocket handle() method to streamlit main loop
#event = multiprocessing.Event() # for graceful exit
#eStop = multiprocessing.Event() # for graceful exit
q     = queue.Queue() # for moving messages from websocket handle() method to streamlit main loop
#event = threading.Event() # for graceful exit
#eStop = threading.Event() # for graceful exit

# ------------- websocket definitions -------------
class SimpleEcho(WebSocket):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("initializing WebSocket instance")  # This should print when a client attempts to connect

    def handle(self):
        try:
            print(f"Received from {self.address}: {self.data}")
            q.put(self.data) # put into the queue for main to .get()
            print(f"q.qsize()={q.qsize()}")
            # Echo the message back to the client
            self.send_message(f"Server Echo: {self.data}")
        except Exception as err:
            print(f"Error handling message from {self.address}: {err}")

    def connected(self):
        print("Entering connected() method")
        print(f"New client connected: {self.address}")
        self.server.custom_clients[self] = self

    def handle_close(self):
        print(f"Client disconnected: {self.address}")
        if self in self.server.custom_clients:
            del self.server.custom_clients[self]

class CustomWebSocketServer(WebSocketServer):
#class CustomWebSocketServer(SimpleWebSocketServer):
    def __init__(self, host, port, websocket_class):
        super().__init__(host, port, websocket_class)
        print("creating self.custom_clients dict to store client addr:port pairs")
        self.custom_clients = {}  # Custom dictionary to hold our clients



# ------------- websocket runtime -------------
# Detect if a port is in use.
# Kill the process holding the port (if any).
# Start a new WebSocket server in a thread.
# This ensures that the server can be restarted cleanly even if a previous instance is already running.
def is_port_in_use(host, port):
    """
    Check if the port is already in use.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def kill_process_on_port(port):
    """
    Kill the process using the specified port.
    """
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.net_connections(kind='inet'):
                if conn.laddr.port == port:
                    print(f"Killing websocket server process {proc.info['name']} (PID {proc.info['pid']}) using port {port}.")
                    os.kill(proc.info['pid'], 9)
                    return True
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    print(f"No process found using port {port}.")
    return False

def websocket_server_thread(eStop, host, port):
    """
    Function to start the WebSocket server. This will run in a separate process.
    """
    try:
        print(f"Starting WebSocket server on {host}:{port}...")
        #server = WebSocketServer(host, port, SimpleEcho)
        server = CustomWebSocketServer(host, port, SimpleEcho)
        print(f"websocket server listening on port: {port}")
        #server.serve_forever()
        while not eStop.is_set():
            #print("serve_forever() eStop.is_set()={0}".format( eStop.is_set() ))
            server.handle_request()
        server.close()

    except OSError as err:
        print(f"Failed to start server: {err}")

def start_websocket_server(eStop, host='localhost', port=8000):
    """
    Start the WebSocket server in a separate process, ensuring no previous server is running on the port.
    """
    if is_port_in_use(host, port):
        print(f"Port {port} is in use. Attempting to kill the existing process.")
        if kill_process_on_port(port):
            print(f"Process on port {port} terminated successfully.")
        else:
            print(f"Failed to terminate the process on port {port}. Exiting.")
            return

    print("Starting WebSocket server process...")

    st.session_state.ws_thread = threading.Thread(target=websocket_server_thread, args=(eStop, host, port,), daemon=True)
    st.session_state.ws_thread.start()
    st.session_state.thread_running = True # updates status field background

def stop_websocket_server(ws_thread):
    """
    Stop the WebSocket server thread.
    """
    if ws_thread.is_alive():
        print(f"Stopping WebSocket server thread with ID {ws_thread.ident}...", end='')
        st.session_state.eStop.set()  # Signal the thread to stop
        print(" waiting for thread to finish...")
        ws_thread.join()  # Wait for the thread to finish execution
        st.session_state.thread_running = False # updates status field background
        print("WebSocket server thread stopped.")
    else:
        print("No active WebSocket server thread to stop.")




# ------------- websocket runtime -------------

# Start WebSocket server in a separate thread
host = ''
port = 8765  # Explicitly define the port we want to use

col1, col2, col3 = st.columns(3)

ws_server_start = col1.button('start websocket server')
if ws_server_start:
    st.session_state.eStop.clear() # set false
    start_websocket_server(st.session_state.eStop, host, port) # START websocket interface
    print(f"websocket server thread started")


ws_server_stop = col2.button('stop websocket server')
if ws_server_stop:
    st.session_state.eStop.set() # set true
    print(f"eStop.is_set()={st.session_state.eStop.is_set()}")
    stop_websocket_server( st.session_state.ws_thread ) # STOP websocket interface





# Display websocket thread status
if st.session_state.thread_running:
    st.success("websocket server thread is running.")
else:
    st.warning("websocket server thread is not running.")




# Second row of buttons and textbox
col4, col5, col6 = st.columns(3)

# Increase counter button logic
if col4.button("Increase Counter"):
    st.session_state.counter += 1

# Decrease counter button logic
if col5.button("Decrease Counter"):
    st.session_state.counter -= 1

# Counter display textbox
col6.text_area("Counter Value", value=str(st.session_state.counter), height=68)



print('-------------------------')
for item in st.session_state.items():                
    print(item)
print('-------------------------')

#code.interact(local=dict(globals(), **locals()))

# ------------- main streamlit loop to update clocks and display messages -------------
try:
    print('try: top of loop at [{0}]'.format(datetime.now()))
    while not st.session_state.event.is_set():

        # Get the latest message from query parameters
        last_message = "" #get_message_from_query()
        #print(f"q.qsize()={q.qsize()}")
        if q.qsize()>0:
            last_message=q.get()
            last_timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")  # Timestamp of reception

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

except KeyboardInterrupt:
    print('caught KeyboardInterrupt (location a)')
    st.session_state.event.set() # gracefully exit main loop
    st.stop()
    stop_websocket_server(st.session_state.ws_thread)
    exit()

except RuntimeError:
    print('caught RuntimeError')

finally:
    print('--------- finally: ---------')
    #event.set() # gracefully exit main loop
    #stop_websocket_server(st.session_state.ws_thread)
    #print('done and exiting.')
    ##st.stop()
    #exit()











