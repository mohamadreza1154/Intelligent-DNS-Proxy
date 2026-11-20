import socket

def load_config():
    config = {}

    with open("config.txt", "r") as file:
        for line in file:
            key, value = line.strip().split("=")
            config[key] = value

    return config


settings = load_config()

HOST = settings["upstream_ip"]
PORT = int(settings["upstream_port"])

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

message = "QUERY example.com"

client.sendto(message.encode(), (HOST, PORT))

data, address = client.recvfrom(1024)

response = data.decode()

print("Response:", response)

client.close()