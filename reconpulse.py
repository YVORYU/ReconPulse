import argparse
import sys

from modules.input import normalize_target
from modules.logger import info, warn, critical
from modules.portscan import run_port
from modules.subdomain import run_subdomain

VERSION = "1.0.0"

BANNER = r"""
    ____                        ____        __
   / __ \___  _________  ____  / __ \__  __/ /_______
  / /_/ / _ \/ ___/ __ \/ __ \/ /_/ / / / / / ___/ _ \
 / _, _/  __/ /__/ /_/ / / / / ____/ /_/ / (__  )  __/
/_/ |_|\___/\___/\____/_/ /_/_/    \__,_/_/____/\___/
"""


def print_banner():
    print(BANNER)
    print(f"ReconPulse v{VERSION} - Automated Recon Tool")
    print("-" * 56)


def build_parser():
    parser = argparse.ArgumentParser(description="ReconPulse - Automated Recon Tool")
    parser.add_argument("-u", "--url", help="Target URL or domain, e.g. example.com", required=True)
    parser.add_argument("-m", "--modules", choices=["subdomain", "port", "all"], default="all",
                        help="Modules to run: subdomain / port / all")
    parser.add_argument("-d", "--directory", default="data/subnames.txt",
                        help="Subdomain dictionary file")
    parser.add_argument("-t", "--threads", type=int, default=50,
                        help="Number of concurrent threads")
    parser.add_argument("-p", "--ports", default=None,
                        help="Port range, e.g. 80,443,8000-9000")
    parser.add_argument("-T", "--timeout", type=float, default=1,
                        help="Network timeout in seconds")
    return parser.parse_args()


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print_banner()

    args = build_parser()
    scan_host, root_domain = normalize_target(args.url)
    if not scan_host:
        critical(f"Failed to parse target: {args.url}")
        return

    info(f"ReconPulse start scanning: {args.url} (host: {scan_host})")

    if args.modules in ("subdomain", "all"):
        info("========== Subdomain mining ==========")
        scan_host, subdomains = run_subdomain(args.url, args.directory, args.threads, args.timeout)
        info(f"Subdomain mining finished: {len(subdomains)} subdomains found")

    if args.modules in ("port", "all"):
        info("========== Port scanning ==========")
        ip, open_ports = run_port(args.url, args.threads, args.timeout, args.ports)
        info(f"Port scanning finished: {len(open_ports)} open ports")

    info("Scan completed")


if __name__ == "__main__":
    main()
