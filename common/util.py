from collections import Counter

def count_ip(ips: dict[str, str]) -> Counter[str]:
  counter = Counter()
  for ip in ips.values():
    counter[ip] = counter.get(ip, 0) + 1
  return counter