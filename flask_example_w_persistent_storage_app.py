# flask example with persistent storage across sessions using
# a local .json file to record the latest get requests, values, and timestamp
#
# run with: streamlit run flask_example_w_persistent_storage_app.py
#
# send in get requests on 8502 with: curl "http://localhost:8502/?param1=test&param2=example"
#
# browser in streamlit on 8501 displays parameters passed in via command line
# WORKS LOCALLY BUT FLASK IS NOT SUPPORTED ON STREAMLIT COMMUNITY CLOUD
# mdc, 15 Dec 2024

import threading
import streamlit as st
from flask import Flask, request, jsonify
import time
import json
from datetime import datetime
import os

# Flask app
flask_app = Flask(__name__)

# File to store GET request data
DATA_FILE = "received_requests.json"

# Load saved data if it exists
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as file:
        saved_data = json.load(file)
else:
    saved_data = []

# Shared data dictionary to store the latest GET request
shared_data = {}

@flask_app.route('/', methods=['GET'])
def handle_get_request():
    global shared_data
    # Get query parameters as a dictionary
    shared_data = request.args.to_dict()
    
    # Add a timestamp to the received data
    timestamp = datetime.now().isoformat()
    entry = {"timestamp": timestamp, "data": shared_data, 'buttonCleared': False}
    
    # Save the new entry to the file
    saved_data.append(entry)
    with open(DATA_FILE, "w") as file:
        json.dump(saved_data, file, indent=4)
    
    return jsonify({"message": "GET request received", "data": shared_data}), 200

# Function to run Flask in a separate thread
def run_flask():
    flask_app.run(host="0.0.0.0", port=8502, debug=False, use_reloader=False)

# Start Flask in a background thread
flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# Streamlit interface
st.title("Streamlit and Flask GET Request Example")

st.write("Use the following curl command to send a GET request:")
st.code('curl "http://localhost:8502/?param1=value1&param2=value2"', language="bash")

st.markdown(
    """
    <style>
    .blue-box {
        background-color: #e0f7ff;
        padding: 10px;
        border-radius: 5px;
        margin-top: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Button to clear data
if st.button("Clear Data"):
    # Reset the data and write to the file
    saved_data = []
    shared_data = {'buttonCleared': True}

    # Add a timestamp to the button press and cleared data
    timestamp = datetime.now().isoformat()
    entry = {"timestamp": timestamp, "data": shared_data}
    
    # Save the new entry to the file
    saved_data.append(entry)

    with open(DATA_FILE, "w") as file:
        json.dump(saved_data, file, indent=4)
    st.success(f"Data cleared at {timestamp}")

# Display received requests
st.write("Most Recent GET Requests (updates every second):")
data_container = st.empty()

# Continuously update the displayed data
while True:
    # Load the saved data to ensure persistence across sessions
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            saved_data = json.load(file)
    
    # Display the latest 5 entries
    with data_container.container():
        st.markdown(
            f"""
            <div class="blue-box">
            <pre>{json.dumps(saved_data[-5:], indent=4)}</pre>
            </div>
            """,
            unsafe_allow_html=True,
        )
    time.sleep(1)



