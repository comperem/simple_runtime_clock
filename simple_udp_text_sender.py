import socket
import sys

# Define the server and port
UDP_IP = "127.0.0.1"  # Use the IP of your Streamlit server if not running locally
UDP_PORT = 5000


def send_udp_message(message, target_ip='127.0.0.1', target_port=5000):
    """Send a UDP message to the specified IP and port."""
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    nBytes=udp_socket.sendto(message.encode('utf-8'), (target_ip, target_port))
    print(f"Sent {nBytes} bytes to {target_ip}:{target_port} with: {message}")

if __name__ == "__main__":
    # Ensure a message argument is provided
    if len(sys.argv) < 2:
        print("Usage: python udp_sender.py <message>")
        sys.exit(1)

    # The message to send is the first argument
    message = sys.argv[1]
    
    # Call the function to send the UDP message
    send_udp_message(message)

    

