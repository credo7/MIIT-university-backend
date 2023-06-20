import socket


def test_socket_connection():
    host = 'localhost'  # Replace with the target host IP or hostname
    port = 5000  # Replace with the target port number

    try:
        # Create a socket object
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to the server
        sock.connect((host, port))

        # Send data to the server
        message = "Hello, server!"
        sock.sendall(message.encode())

        # Receive data from the server
        data = sock.recv(1024)
        response = data.decode()
        print(f"Server response: {response}")

        # Close the socket
        sock.close()

    except ConnectionRefusedError:
        print("Connection refused. Make sure the server is running.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Run the socket test
test_socket_connection()
