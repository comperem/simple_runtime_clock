# websocket client and server without asyncio
#
# run with steps:
# (0) create a virtual environment: uv venv
# (1) start venv: source .venv/bin/activate
# (2) install python packages:
#       uv pip install simple_websocket_server websocket-client
# (3) start server first:
#       python websocket_server_threads_b.py
# (4) start client:
#       python websocket_client_threads_b.py

import websocket
import threading

ip='localhost'
#ip='10.12.249.231'  # websocket server
#ip="simple-runtime-clock-with-websocket-d.streamlit.app"
port=8765           # websocket port
port=8081


def on_message(ws, message):
    print(f"Debug: on_message called with message: {message}")
    print(f"Server message received: {message}")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    print("### opened ###")

def connect():
    print(f'attempting websocket connection on [{ip}:{port}]')
    ws = websocket.WebSocketApp("ws://{0}:{1}".format(ip,port),
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    return ws

def websocket_thread(ws):
    ws.run_forever()

def main():
    websocket.enableTrace(False)
    ws = connect()
    
    # Start WebSocket in a separate thread
    ws_thread = threading.Thread(target=websocket_thread, args=(ws,))
    ws_thread.daemon = True  # Thread stops if main thread stops
    ws_thread.start()
    
    try:
        while True:
            message = input("Enter message to send (or 'exit' to quit): ")
            if message.lower() == 'exit':
                print("Exiting...")
                ws.close()
                break
            ws.send(message)
    except KeyboardInterrupt:
        print("Interrupted by user")
        if ws:
            ws.close()
    except Exception as e:
        print(f"An error occurred: {e}")
        if ws:
            ws.close()

if __name__ == "__main__":
    main()