import requests

proxies = {"http": "socks5h://127.0.0.1:9150",
           "https": "socks5h://127.0.0.1:9150"}

r = requests.get("https://httpbin.org/ip", proxies=proxies)
print(r.json())   # Should show a Tor IP, not your Indian IP
