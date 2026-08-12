import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from urllib.parse import urlparse

from modules.input import normalize_target
from modules.logger import info, warn, critical


DEFAULT_PORTS = [80, 443]


def extract_host_and_port(url):

    url = url.strip()
    if not url:
        return None, None
    if "://" not in url:
        url = "http://" + url
    try:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        try:
            port = parsed.port
        except ValueError:
            port = None
    except Exception:
        return None, None
    return host, port


def build_target_urls(url, subdomains=None, open_ports=None):
    host, input_port = extract_host_and_port(url)
    if not host:
        return []

    is_ip = False
    try:
        ipaddress.ip_address(host)
        is_ip = True
    except ValueError:
        pass

    if subdomains:
        hosts = list(subdomains)
    elif is_ip:
        hosts = [host]
    else:
        scan_host, _ = normalize_target(url)
        hosts = [scan_host] if scan_host else [host]

    if open_ports:
        ports = list(open_ports)
    elif input_port:
        ports = [input_port]
    else:
        ports = DEFAULT_PORTS

    urls = set()
    for h in hosts:
        for p in ports:
            scheme = "https" if p == 443 else "http"
            urls.add(f"{scheme}://{h}:{p}")
    return sorted(urls)


def build_full_targets(host_port_map):
    urls = set()
    for host, ports in host_port_map.items():
        for p in ports:
            scheme = "https" if p == 443 else "http"
            urls.add(f"{scheme}://{host}:{p}")
    return sorted(urls)


def choose_scan_mode(host_port_map, original_url):
    full_targets = build_full_targets(host_port_map)
    total = len(full_targets)

    print("\n" + "=" * 56)
    print("POC verification mode:")
    print("  [1] Full scan - verify ALL subdomains x open ports")
    print(f"      ({total} target(s), may take a long time)")
    print("  [2] Custom URL - verify a specific URL/domain only")
    print("=" * 56)

    if not full_targets:
        warn("No full-scan targets available (no open ports found)")
        choice = "2"
    else:
        choice = input("Select mode [1/2] (default 1, Enter for full scan): ").strip()

    if choice == "2":
        custom_url = input("Enter target URL (e.g. www.example.com or http://www.example.com:8080): ").strip()
        if not custom_url:
            warn("Empty custom URL, falling back to full scan")
            return full_targets
        targets = build_target_urls(custom_url)
        if not targets:
            warn(f"Invalid custom URL: {custom_url}, falling back to full scan")
            return full_targets
        info(f"Custom scan selected: {custom_url} -> {targets}")
        return targets

    if not full_targets:
        critical("No targets available for POC verification")
        return []
    info(f"Full scan selected: {total} targets will be verified, this may take a long time")
    return full_targets


def find_pocsuite_cmd():
    pocsuite = shutil.which("pocsuite")
    if pocsuite:
        return [pocsuite]
    return [sys.executable, "-m", "pocsuite3.cli"]


POC_EXTENSIONS = (".py",)


def load_poc_files(poc_dir):
    if not os.path.isdir(poc_dir):
        warn(f"POC directory not found: {poc_dir}")
        return []
    poc_files = []
    for root, _, files in os.walk(poc_dir):
        for f in files:
            if f.endswith(POC_EXTENSIONS) and f != "__init__.py":
                poc_files.append(os.path.join(root, f))
    return poc_files


def parse_poc_results(result_file):
    hits = []
    if not os.path.exists(result_file):
        return hits
    with open(result_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            target = item.get("target", "")
            poc_name = item.get("poc_name", "")
            result = item.get("result", {})
            hits.append((poc_name, target, result))
    return hits


def run_poc(targets, poc_dir="pocs", timeout=600, threads=50):
    info("Start POC verification")

    if not targets:
        critical("No valid targets for POC verification")
        return []

    poc_files = load_poc_files(poc_dir)
    if not poc_files:
        warn(f"No POC files in {poc_dir}, skip POC verification")
        return []

    safe_host = "scan"
    os.makedirs("output", exist_ok=True)
    targets_file = os.path.join("output", f"targets_{safe_host}.txt")
    with open(targets_file, "w", encoding="utf-8") as f:
        f.write("\n".join(targets) + "\n")
    info(f"POC targets ({len(targets)} URLs, {len(poc_files)} POCs): {targets_file}")

    result_file = os.path.join("output", f"poc_{safe_host}.jsonl")
    if os.path.exists(result_file):
        os.remove(result_file)

    cmd = find_pocsuite_cmd() + [
        "-r", poc_dir,
        "-f", targets_file,
        "--verify",
        "-o", result_file,
        "--threads", str(threads),
    ]
    info(f"Running pocsuite3: {' '.join(cmd)}")
    try:
        clean_env = {k: v for k, v in os.environ.items()
                     if k.upper() not in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY")}
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8", errors="replace",
                                stdin=subprocess.DEVNULL, env=clean_env)

        def forward_output(pipe):
            skip_banner = True
            in_table = False
            in_traceback = False
            for line in iter(pipe.readline, ""):
                if skip_banner:
                    if line.startswith("[*] starting at"):
                        skip_banner = False
                    continue
                if in_table:
                    if line.startswith("success :"):
                        in_table = False
                        print(line, end="", flush=True)
                    continue
                if re.match(r"^\+-+\+", line.strip()):
                    in_table = True
                    continue
                if "Traceback (most recent call last)" in line:
                    in_traceback = True
                    continue
                if in_traceback:
                    if re.match(r"^\[\d{2}:\d{2}:\d{2}\]", line):
                        in_traceback = False
                    else:
                        continue
                print(line, end="", flush=True)
            pipe.close()

        forward_thread = threading.Thread(target=forward_output, args=(proc.stdout,))
        forward_thread.daemon = True
        forward_thread.start()

        interrupt_flag = threading.Event()

        def watch_stdin_eof():
            try:
                if sys.stdin and sys.stdin.isatty():
                    while not interrupt_flag.is_set():
                        if sys.stdin.read(1) == "":
                            interrupt_flag.set()
                            break
            except Exception:
                pass

        stdin_thread = threading.Thread(target=watch_stdin_eof)
        stdin_thread.daemon = True
        stdin_thread.start()

        try:
            start_time = time.monotonic()
            while not interrupt_flag.is_set():
                try:
                    proc.wait(timeout=1)
                    break
                except subprocess.TimeoutExpired:
                    if time.monotonic() - start_time > timeout:
                        proc.kill()
                        warn(f"pocsuite3 timed out after {timeout}s, partial results may be saved")
                        break
                    continue
            if interrupt_flag.is_set():
                proc.kill()
                warn("Interrupted by user (Ctrl+C / Ctrl+Z), pocsuite3 process killed")
                return []
        except KeyboardInterrupt:
            proc.kill()
            warn("Interrupted by user, pocsuite3 process killed")
            raise
        except subprocess.TimeoutExpired:
            proc.kill()
            warn(f"pocsuite3 timed out after {timeout}s, partial results may be saved")
        forward_thread.join(timeout=5)
        if proc.returncode != 0:
            warn(f"pocsuite3 exited with code {proc.returncode}")
    except FileNotFoundError:
        critical("pocsuite3 not found. Install with: pip install pocsuite3")
        return []
    except Exception as e:
        warn(f"pocsuite3 execution failed: {e}")
        return []

    hits = parse_poc_results(result_file)
    if hits:
        for poc_name, target, _ in hits:
            info(f"Vulnerability found: [{poc_name}] {target}")
    else:
        info("No vulnerability found")
    return hits
