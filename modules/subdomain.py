from modules.input import extract_host, get_root_domain, normalize_target
from modules.logger import info, warn, critical
import requests
import dns.resolver
from concurrent.futures import ThreadPoolExecutor, as_completed
import os


def collect_from_hackertarget(domain, timeout=10):
    results = set()
    info("Collecting subdomains from hackertarget")
    api_url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
    for i in range(1, 4):
        try:
            response = requests.get(api_url, headers=headers, timeout=timeout)
            if response.status_code != 200:
                warn(f"hackertarget returned status {response.status_code}, retry {i}/3")
                continue
            text = response.text.strip()
            if not text:
                info("hackertarget returned empty result")
                break
            for line in text.splitlines():
                name = line.split(",")[0].strip().lower()
                if name == domain or name.endswith("." + domain):
                    results.add(name)
            info(f"hackertarget collection done, found {len(results)} subdomains")
            break                                         
        except requests.exceptions.RequestException as e:
            warn(f"hackertarget request failed: {e}, retry {i}/3")
    return results


def brute_force(domain, directory_file, threads, timeout):
    results = set()
    info("Brute force attack started")
    try:
        with open(directory_file, mode="r", encoding="utf-8") as f:
            words = [line.strip() for line in f
                     if line.strip() and not line.startswith("#")]
    except OSError as e:
        critical(f"Failed to open the dictionary file: {e}")
        return results

    resolver = dns.resolver.Resolver()
    resolver.lifetime = timeout          

    def check_subdomain(word):
        qname = f"{word}.{domain}"
        try:
            resolver.resolve(qname, "A")
            return qname
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
                dns.resolver.Timeout, dns.resolver.NoNameservers):
            return None                    

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(check_subdomain, word) for word in words]
        for future in as_completed(futures):
            qname = future.result()
            if qname:
                results.add(qname)
                info(f"Found subdomain: {qname}")
    info(f"Brute force attack completed, found {len(results)} subdomains")
    return results


def run_subdomain(url, directory_file, threads, timeout):
    info("Start subdomain mining")
    scan_host, domain = normalize_target(url)   # 统一整理用户输入
    if not scan_host:
        critical("Failed to obtain the host name. Please enter a legal form")
        return None, []
    if not domain:
        warn("IP address input detected, subdomain mining skipped")
        return scan_host, []
    info(f"Target host: {scan_host}, brute force on root domain: {domain}")

    results_brute = brute_force(domain, directory_file, threads, timeout)
    results_passive = collect_from_hackertarget(domain)
    results = sorted(results_brute | results_passive)   

    if results:
        for r in results:
            info(f"Subdomain: {r}")
    else:
        info("No subdomains found")

    os.makedirs("output", exist_ok=True)
    output_file = f"./output/subdomains_{domain}.txt"
    with open(output_file, mode="w", encoding="utf-8") as f:
        f.write("\n".join(results) + "\n")
    info(f"Subdomain mining completed! Saved to {output_file}")
    return scan_host, results

