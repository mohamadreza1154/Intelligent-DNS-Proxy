
<div align="center">

# Intelligent DNS Proxy

**A Python-based DNS Proxy with Caching, Domain Filtering, Statistics, and Real DNS Support**

![Python](https://img.shields.io/badge/Python-3.14-blue)
![Protocol](https://img.shields.io/badge/Protocol-UDP-orange)
![DNS](https://img.shields.io/badge/DNS-Proxy-green)
![Status](https://img.shields.io/badge/Project-Completed-success)

</div>

---

## 1. Project Overview

This project implements an Intelligent DNS Proxy using Python and UDP sockets.

The proxy receives DNS requests from clients, validates domain names, checks filtering lists, manages a local DNS cache, and forwards valid requests to an upstream DNS server.

The project also supports real DNS resolution through public DNS servers using the `dnspython` library.

## 2. Features

| Feature | Description |
|---|---|
| DNS Proxy | Receives and processes DNS requests |
| UDP Communication | Communicates with clients and upstream servers using UDP |
| Domain Validation | Validates domain names before processing |
| Ad Filtering | Blocks domains listed in `ad_list.txt` |
| Sanction Filtering | Blocks domains listed in `sanction_list.txt` |
| DNS Cache | Stores DNS responses temporarily |
| TTL Management | Removes expired cache entries |
| Cache Size Limit | Controls the maximum number of cache entries |
| Upstream Simulator | Provides a local simulated DNS server |
| Real DNS Resolution | Supports real DNS queries using `dnspython` |
| Logging | Records DNS requests and their results |
| Statistics | Displays request statistics and frequently requested domains |
| Health Check | Checks upstream server availability |
| Configuration | Loads settings from `config.txt` |

## 3. Project Architecture

```text
                 DNS Client
                     |
                     | UDP Request
                     v
              +-------------+
              |  DNS Proxy  |
              +-------------+
                     |
                     v
              Domain Validation
                     |
                     v
              Filtering System
                /          \
               /            \
          Ad List         Sanction List
               \            /
                \          /
                     |
                     v
                 DNS Cache
                /         \
             HIT           MISS
              |              |
              v              v
          Response      Upstream Server
                             |
                             v
                       DNS Response
                             |
                             v
                         Cache Store
                             |
                             v
                         DNS Client
```

## 4. Project Structure

```text
DNS-Proxy/
│
├── dns_proxy.py
├── upstream.py
├── client.py
├── cache_test.py
│
├── config.txt
├── ad_list.txt
├── sanction_list.txt
│
├── log.txt
├── requirements.txt
└── README.md
```

### File Description

- `dns_proxy.py`: Main DNS Proxy application.
- `upstream.py`: Local UDP upstream DNS simulator.
- `client.py`: UDP client for sending DNS requests.
- `cache_test.py`: Script for testing cache behavior.
- `config.txt`: Application configuration.
- `ad_list.txt`: List of advertising domains.
- `sanction_list.txt`: List of blocked domains.
- `log.txt`: Stores request logs.
- `requirements.txt`: Python dependencies.

## 5. Requirements

- Python 3.14
- `dnspython` library

Install the required dependency:

```bash
pip install -r requirements.txt
```

The `requirements.txt` file contains:

```text
dnspython==2.9.2
```

## 6. Configuration

The application uses `config.txt` to configure its behavior.

Example:

```ini
upstream_ip=127.0.0.1
upstream_port=5354
timeout=2

ad_list_file=ad_list.txt
sanction_list_file=sanction_list.txt

sinkhole_ip=0.0.0.0
proxy_ip=192.0.2.10

local_ttl=60

cache_enabled=true
cache_max_entries=2

real_dns_enabled=false
```

### Configuration Parameters

| Parameter | Description |
|---|---|
| upstream_ip | Upstream server IP address |
| upstream_port | Upstream server UDP port |
| timeout | Maximum response waiting time |
| ad_list_file | Advertising domain list |
| sanction_list_file | Blocked domain list |
| sinkhole_ip | IP returned for blocked domains |
| proxy_ip | Proxy IP configuration |
| local_ttl | TTL for local responses |
| cache_enabled | Enables or disables caching |
| cache_max_entries | Maximum number of cache entries |
| real_dns_enabled | Enables real DNS resolution |

## 7. Running the Project

The application supports two operating modes.

### Mode 1: Local Upstream Simulator

Set the following values in `config.txt`:

```ini
upstream_ip=127.0.0.1
upstream_port=5354
real_dns_enabled=false
```

Open two terminal windows.

**Terminal 1 — Start the upstream simulator:**

```bash
python upstream.py
```

**Terminal 2 — Start the DNS proxy:**

```bash
python dns_proxy.py
```

The proxy will communicate with the local upstream simulator.

### Mode 2: Real DNS Resolution (B6)

To enable real DNS resolution, update `config.txt`:

```ini
upstream_ip=8.8.8.8
upstream_port=53
real_dns_enabled=true
```

You can also use another public DNS server, such as `1.1.1.1`.

Run only the DNS proxy:

```bash
python dns_proxy.py
```

**Important:** When real DNS mode is enabled, do not run `upstream.py`.

## 8. Available Commands

The DNS Proxy provides several interactive commands.

| Command | Description |
|---|---|
| `help` | Displays available commands |
| `?` | Displays help information |
| `health` | Checks upstream server availability |
| `cache` | Displays current cache entries |
| `stats` | Displays request statistics |
| `reload` | Reloads configuration and domain lists |
| `exit` | Terminates the application |

## 9. DNS Request Processing

When a client sends a domain name, the proxy follows these steps:

1. Receives the domain request.
2. Normalizes and validates the domain name.
3. Checks the advertising domain list.
4. Checks the sanction domain list.
5. Searches the DNS cache.
6. If the cache contains a valid entry, returns the cached response.
7. Otherwise, forwards the request to the upstream server.
8. Processes the upstream response.
9. Stores successful responses in the cache when caching is enabled.
10. Returns the result to the client.

## 10. Cache Management

The DNS Proxy implements an in-memory cache.

Each cache entry contains:

- Domain name
- IP address
- TTL
- Expiration information

The cache supports:

- TTL-based expiration.
- Maximum cache capacity.
- Cache hit and miss detection.
- Removal of expired entries.
- Replacement of older entries when the cache is full.

Example:

```text
Enter domain: example.com

Domain : example.com
Source : UPSTREAM
Status : OK
IP     : 93.184.216.34
TTL    : 60
```

Requesting the same domain again may return:

```text
Enter domain: example.com

Domain : example.com
Source : CACHE
Status : OK
IP     : 93.184.216.34
TTL    : 45
```

The remaining TTL depends on the time elapsed since the response was cached.

## 11. Logging and Statistics

The application records DNS request information in `log.txt`.

The statistics command provides information such as:

- Total requests
- Successful requests
- Not-found responses
- Error responses
- Most frequently requested domains

Example:

```text
Enter domain: stats
```

The application displays the available statistics.

## 12. Testing

The following scenarios can be used to evaluate the project.

| Test | Expected Behavior |
|---|---|
| Valid domain | Returns an IP address |
| Repeated domain | Returns a cached response |
| Invalid domain | Rejects the domain |
| Advertising domain | Blocks the request |
| Sanctioned domain | Blocks the request |
| Unknown domain | Returns NOT_FOUND |
| Cache expiration | Requests the upstream server again |
| Cache capacity | Removes an older entry when full |
| Upstream unavailable | Handles timeout or server error |
| Configuration reload | Reloads configuration and domain lists |
| Health check | Reports upstream availability |
| Real DNS mode | Resolves domains through a public DNS server |

Actual test inputs and outputs should be documented separately in a test results file.

## 13. Error Handling

The application handles different error conditions, including:

- Invalid domain names.
- Domains not found.
- Upstream server timeouts.
- Invalid upstream responses.
- DNS resolution errors.
- Socket communication errors.

The proxy is designed to handle these conditions without unexpectedly terminating during normal request processing.

## 14. Technologies Used

- Python
- UDP Sockets
- DNS Protocol
- `dnspython`
- File Handling
- In-Memory Data Structures
- TTL-Based Caching

---

<div align="center">

**Intelligent DNS Proxy — Computer Networks Project**

</div>
