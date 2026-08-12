import argparse
import sys

from modules.input import normalize_target
from modules.logger import info, warn, critical
from modules.portscan import run_port, run_port_multi
from modules.subdomain import run_subdomain
from modules.poc import choose_scan_mode, run_poc
from modules.report import build_report_data, generate_html_report

VERSION = "1.2.0"

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
    parser.add_argument("-m", "--modules", choices=["subdomain", "port", "poc", "all"], default="all",
                        help="Modules to run: subdomain / port / poc / all")
    parser.add_argument("-d", "--directory", default="data/subnames.txt",
                        help="Subdomain dictionary file")
    parser.add_argument("-t", "--threads", type=int, default=50,
                        help="Number of concurrent threads")
    parser.add_argument("-p", "--ports", default=None,
                        help="Port range, e.g. 80,443,8000-9000")
    parser.add_argument("-T", "--timeout", type=float, default=1,
                        help="Network timeout in seconds")
    parser.add_argument("--poc-dir", default="pocs",
                        help="Directory containing POC files (default: pocs)")
    parser.add_argument("--report", default=None,
                        help="HTML report output path (default: output/report.html)")
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

    subdomains, open_ports = [], []
    host_port_map = {}

    if args.modules in ("subdomain", "all"):
        info("========== Subdomain mining ==========")
        scan_host, subdomains = run_subdomain(args.url, args.directory, args.threads, args.timeout)
        info(f"Subdomain mining finished: {len(subdomains)} subdomains found")

    if args.modules == "port":
        info("========== Port scanning ==========")
        ip, open_ports = run_port(args.url, args.threads, args.timeout, args.ports)
        info(f"Port scanning finished: {len(open_ports)} open ports")

    if args.modules == "all":
        info("========== Port scanning for all hosts ==========")
        hosts = [scan_host] + list(subdomains)
        host_port_map = run_port_multi(hosts, args.threads, args.timeout, args.ports)
        open_ports = sorted(host_port_map.get(scan_host, []))
        info(f"Port scanning finished: {sum(len(v) for v in host_port_map.values())} open ports across {len(hosts)} hosts")

    if args.modules in ("poc", "all"):
        info("========== POC verification ==========")
        if args.modules == "all":
            targets = choose_scan_mode(host_port_map, args.url)
        else:
            from modules.poc import build_target_urls
            targets = build_target_urls(args.url, subdomains or None, open_ports or None)
        poc_hits = run_poc(targets, args.poc_dir, timeout=600, threads=args.threads)
        info(f"POC verification finished: {len(poc_hits)} vulnerabilities found")


        report_data = build_report_data(args.url, host_port_map, subdomains, poc_hits)
        generate_html_report(report_data, args.report)

    info("Scan completed")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        info("Scan interrupted by user (Ctrl+C), exiting")
        sys.exit(130)
    except EOFError:
        print()
        info("Scan interrupted by user (Ctrl+Z), exiting")
        sys.exit(130)
