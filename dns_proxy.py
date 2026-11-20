import dns.resolver
import dns.exception
import time
import socket
import ipaddress
from datetime import datetime
from collections import Counter

def load_config():
    config = {}

    with open("config.txt", "r") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            key, value = line.split("=", 1)
            config[key.strip()] = value.strip()

    return config


def load_domain_list(path):
    domains = set()

    with open(path, "r") as file:
        for line in file:
            domain = line.strip().lower()

            if domain and not domain.startswith("#"):
                domains.add(domain.rstrip("."))

    return domains


def normalize_domain(domain):
    return domain.strip().lower().rstrip(".")


def is_valid_domain(domain):

    if not domain or len(domain) > 253:
        return False

    labels = domain.split(".")

    for label in labels:

        if not label or len(label) > 63:
            return False

        if label[0] == "-" or label[-1] == "-":
            return False

        for char in label:
            if not (char.isalnum() or char == "-"):
                return False

    return True


def matches_domain(domain, domain_list):

    for item in domain_list:

        if domain == item or domain.endswith("." + item):
            return True

    return False

cache = {}

stats = {
    "Total": 0,
    "AD_BLOCK": 0,
    "SANCTION": 0,
    "CACHE": 0,
    "UPSTREAM": 0,
    "ERRORS": 0,
    "SUCCESSFUL": 0,
    "NOT_FOUND": 0
}

domain_counter = Counter()
def store_cache(domain, ip, ttl, max_entries):

    if ttl <= 0 or max_entries <= 0:
        return

    if domain not in cache and len(cache) >= max_entries:
        oldest_domain = next(iter(cache))
        del cache[oldest_domain]

    cache[domain] = {
        "ip": ip,
        "ttl": ttl,
        "stored_at": time.monotonic()
    }


def get_cache(domain):
    if domain not in cache:
        return None

    entry = cache[domain]

    elapsed = time.monotonic() - entry["stored_at"]
    remaining = entry["ttl"] - elapsed
    remaining_ttl = int(remaining)

    if remaining_ttl <= 0:
        del cache[domain]
        return None

    return entry["ip"], remaining_ttl


def show_cache():
    expired_domains = []
    entries = []

    for domain, entry in cache.items():
        elapsed = time.monotonic() - entry["stored_at"]
        remaining = int(entry["ttl"] - elapsed)

        if remaining <= 0:
            expired_domains.append(domain)
        else:
            entries.append(
                f"{domain} | {entry['ip']} | {remaining}"
            )

    for domain in expired_domains:
        del cache[domain]

    if not entries:
        print("Cache is empty.")
        return

    for item in entries:
        print(item)
def query_real_dns(domain, settings):
    host = settings["upstream_ip"]
    port = int(settings["upstream_port"])
    timeout = float(
        settings.get("upstream_timeout_sec", settings.get("timeout", "2"))
    )

    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [host]
    resolver.port = port
    resolver.timeout = timeout
    resolver.lifetime = timeout

    try:
        answer = resolver.resolve(
            domain,
            "A",
            raise_on_no_answer=False
        )

        if answer.rrset is None or len(answer) == 0:
            return "NOT_FOUND", None, None

        ip = answer[0].address
        ttl = answer.rrset.ttl

        return "OK", ip, ttl

    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return "NOT_FOUND", None, None

    except (dns.exception.DNSException, OSError, ValueError):
        return "SERVER_ERROR", None, None

def show_help():
    print("\n========== DNS PROXY HELP ==========")
    print("This program works as a DNS Proxy.")
    print()
    print("Available commands:")
    print("  help  or  ?       Show this help message")
    print("  health            Check upstream DNS server status")
    print("  stats             Show DNS statistics")
    print()
    print("How to use:")
    print("  Enter a valid domain name to resolve its IP address.")
    print()
    print("Examples:")
    print("  google.com")
    print("  example.com")
    print("  www.wikipedia.org")
    print()
    print("Program features:")
    print("  - Domain validation")
    print("  - Ad blocking")
    print("  - Sanctioned domain blocking")
    print("  - DNS caching")
    print("  - Upstream DNS queries")
    print("  - Real DNS server support (B6)")
    print("====================================\n")

def query_upstream(domain, settings):
    if settings.get("real_dns_enabled", "false").lower() == "true":
        return query_real_dns(domain, settings)
    host = settings["upstream_ip"]
    port = int(settings["upstream_port"])
    timeout = float(settings["timeout"])

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.settimeout(timeout)

            message = f"QUERY {domain}"
            client.sendto(message.encode(), (host, port))

            data, address = client.recvfrom(1024)
            response = data.decode().strip()

        if response == "NOT_FOUND":
            return "NOT_FOUND", None, None

        parts = response.split()

        if len(parts) != 3 or parts[0] != "OK":
            return "SERVER_ERROR", None, None

        ip = parts[1]
        ttl = int(parts[2])

        ipaddress.ip_address(ip)

        if ttl <= 0:
            return "SERVER_ERROR", None, None

        return "OK", ip, ttl

    except (socket.timeout, OSError, ValueError):
        return "SERVER_ERROR", None, None


def check_upstream_health(settings):
    host = settings["upstream_ip"]
    port = int(settings["upstream_port"])

    print("\n========== DNS SERVER HEALTH ==========")
    print(f"Upstream Server : {host}:{port}")

    start_time = time.perf_counter()

    status, ip, ttl = query_upstream("example.com", settings)

    end_time = time.perf_counter()

    response_time_ms = (end_time - start_time) * 1000

    if status in ("OK", "NOT_FOUND"):
        print("Status          : ONLINE")
    else:
        print("Status          : OFFLINE")

    print(f"Response Time   : {response_time_ms:.2f} ms")
    print("=======================================\n")


def print_result(domain, source, status, ip=None, ttl=None,
                 response_time_ms=None):
    stats["Total"] += 1
    if source != "NONE" and status != "INVALID_INPUT":
      domain_counter[domain] += 1
    if source in stats and source != "Total":
        stats[source] += 1

    if status != "OK":
        stats["ERRORS"] += 1
        stats.setdefault("SUCCESSFUL", 0)
        stats.setdefault("NOT_FOUND", 0)

    if status == "OK":
        stats["SUCCESSFUL"] += 1
    elif status == "NOT_FOUND":
        stats["NOT_FOUND"] += 1

    ip_value = ip if ip is not None else "-"
    ttl_value = ttl if ttl is not None else "-"

    print(f"Domain : {domain}")
    print(f"Source : {source}")
    print(f"Status : {status}")
    print(f"IP : {ip_value}")
    print(f"TTL : {ttl_value}")

    if response_time_ms is not None:
        print(f"Response Time : {response_time_ms:.2f} ms")

    print()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_entry = (
        f"{timestamp} | {domain} | {source} | "
        f"{status} | {ip_value} | {ttl_value}\n"
    )

    with open("log.txt", "a") as file:
        file.write(log_entry)

def main():
    try:
        settings = load_config()

        ad_domains = load_domain_list(settings["ad_list_file"])
        sanction_domains = load_domain_list(settings["sanction_list_file"])

        sinkhole_ip = settings["sinkhole_ip"]
        proxy_ip = settings["proxy_ip"]
        local_ttl = int(settings["local_ttl"])
        cache_max_entries = int(settings.get("cache_max_entries", "2"))
    except (OSError, KeyError, ValueError) as error:
        print("Configuration Error:", error)
        return

    while True:
        try:
            raw_domain = input("Enter domain (or exit): ")

            if raw_domain.strip().lower() == "exit":
                print("Bye.")
                break
            if raw_domain.strip().lower() == "health":
                check_upstream_health(settings)
                continue
            if raw_domain.strip().lower() in ("help", "?"):
                show_help()
                continue
            if raw_domain.strip().lower() == "cache":
                show_cache()
                continue
            if raw_domain.strip().lower() == "stats":
                print("\n========== DNS STATISTICS ==========")
                print(f"Total Requests      : {stats['Total']}")
                print(f"Successful Requests : {stats['SUCCESSFUL']}")
                print(f"Not Found Requests  : {stats['NOT_FOUND']}")
                print(f"Total Errors        : {stats['ERRORS']}")

                print("\nMost Requested Domains:")
                if domain_counter:
                 for domain, count in domain_counter.most_common(5):
                  print(f"{domain} : {count} times")
                else:
                  print("No requests yet.")

                print("====================================\n")
                continue
            if raw_domain.strip().lower() == "reload":
                try:
                    ad_domains = load_domain_list(settings["ad_list_file"])
                    sanction_domains = load_domain_list(settings["sanction_list_file"])

                    print("Lists reloaded.")

                except OSError as error:
                    print("Reload Error:", error)

                continue
            domain = normalize_domain(raw_domain)

            if not is_valid_domain(domain):
                print_result(domain or "(empty)", "NONE", "INVALID_INPUT")
                continue

            if matches_domain(domain, ad_domains):
                print_result(
                    domain, "AD_BLOCK", "OK",
                    sinkhole_ip, local_ttl
                )

            elif matches_domain(domain, sanction_domains):
                print_result(
                    domain, "SANCTION", "OK",
                    proxy_ip, local_ttl
                )

            else:
                result = None

                if settings["cache_enabled"].lower() == "true":
                    result = get_cache(domain)

                if result is not None:
                    ip, ttl = result
                    print_result(domain, "CACHE", "OK", ip, ttl)

                else:
                  start_time = time.perf_counter()

                  status, ip, ttl = query_upstream(domain, settings)

                  end_time = time.perf_counter()

                  response_time_ms = (end_time - start_time) * 1000
                  if status == "OK":
                        if settings["cache_enabled"].lower() == "true":
                         store_cache(domain, ip, ttl, cache_max_entries)
                         print_result(
                         domain, "UPSTREAM", "OK",
                          ip, ttl, response_time_ms
                        )

                  elif status == "NOT_FOUND":
                       print_result(
                           domain, "UPSTREAM", "NOT_FOUND",
                            response_time_ms=response_time_ms
                        )

                  else:
                       print_result(
                            domain, "UPSTREAM", "SERVER_ERROR",
                            response_time_ms=response_time_ms
                        )

        except (KeyboardInterrupt, EOFError):
            print("\nDNS Proxy stopped.")
            break


if __name__ == "__main__":
    main()
