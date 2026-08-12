import ipaddress
from urllib.parse import urlparse


MULTI_SUFFIX = {"co", "com", "net", "org", "gov", "ac", "edu"}


def extract_host(url):
    url = url.strip()
    if not url:
        return None
    if "://" not in url:
        url = "http://" + url
    netloc = urlparse(url).netloc         
    if ":" in netloc:
        netloc = netloc.split(":")[0]      
    return netloc


def get_root_domain(host):
    if not host:
        return None
    try:
        ipaddress.ip_address(host)        
        return host
    except ValueError:
        pass
    parts = host.split(".")
    if len(parts) > 2:
        if parts[-2] in MULTI_SUFFIX:      
            return ".".join(parts[-3:])
        return ".".join(parts[-2:])
    return host


def normalize_target(url):
    host = extract_host(url)
    if not host:
        return None, None
    try:
        ipaddress.ip_address(host)         
        return host, None
    except ValueError:
        pass
    root = get_root_domain(host)
    if host == root:                       
        scan_host = "www." + host
    else:
        scan_host = host
    return scan_host, root
