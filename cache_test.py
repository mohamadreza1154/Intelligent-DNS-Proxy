import time

from dns_proxy import store_cache, get_cache


store_cache("example.com", "93.184.216.34", 10)

print("First request:", get_cache("example.com"))

time.sleep(3)

print("Second request:", get_cache("example.com"))

time.sleep(8)

print("Third request:", get_cache("example.com"))