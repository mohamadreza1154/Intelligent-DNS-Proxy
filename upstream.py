
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

domains = {
    "example.com": ("93.184.216.34", 60),
    "google.com": ("142.250.190.14", 120),
    "github.com": ("140.82.112.4", 90),
    "notads.example.com": ("198.51.100.7", 5),
    "normal.example.net": ("198.51.100.7", 5),
    "other.example.net": ("198.51.100.7", 5)
}

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server.bind((HOST, PORT))

print("Upstream Simulator is running...")

request_count = 0

while True:
    data, address = server.recvfrom(1024)

    request_count += 1

    message = data.decode().strip()

    parts = message.split()

    if len(parts) == 2 and parts[0] == "QUERY":
        domain = parts[1].lower()

        if domain in domains:
            ip, ttl = domains[domain]
            response = f"OK {ip} {ttl}"
        else:
            response = "NOT_FOUND"
    else:
        response = "NOT_FOUND"

    shown_domain = parts[1] if len(parts) == 2 and parts[0] == "QUERY" else message

    print(f"Request #{request_count}: {shown_domain} -> {response}")

    server.sendto(response.encode(), address)
