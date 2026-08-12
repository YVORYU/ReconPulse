```
    ____                        ____        __
   / __ \___  _________  ____  / __ \__  __/ /_______
  / /_/ / _ \/ ___/ __ \/ __ \/ /_/ / / / / / ___/ _ \
 / _, _/  __/ /__/ /_/ / / / / ____/ /_/ / (__  )  __/
/_/ |_|\___/\___/\____/_/ /_/_/    \__,_/_/____/\___/
```

# ReconPulse

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)]()

**English** | [简体中文](./README.zh-CN.md)

An automated reconnaissance tool that chains subdomain mining, port scanning, and POC-based vulnerability verification into a single command-line workflow with HTML report output. Built with pure Python, powered by the open-source [pocsuite3](https://github.com/knownsec/pocsuite3) framework for vulnerability checks.

## Features

- **Subdomain mining** — passive collection via [hackertarget](https://api.hackertarget.com/hostsearch/) plus DNS dictionary brute force
- **Port scanning** — multithreaded TCP connect scan, defaults to the nmap top-1000 ports, supports custom ranges like `80,443,8000-9000`; in `all` mode scans the root domain and every subdomain individually
- **POC verification** — 38 Python POCs from the official [pocsuite3](https://github.com/knownsec/pocsuite3) library (Struts2 full series S2-001~S2-066, ThinkPHP, WebLogic, Log4j2, Redis unauthorized access, Confluence, Drupal, etc.), all run in `--verify` mode (detection only, no exploitation). POCs are stored in `pocs/python/`
- **Interactive scan scope** — before POC verification in `all` mode you can choose: full scan of all subdomains x open ports (default), or enter a specific URL to verify a single target
- **HTML report** — a self-contained HTML report is generated after scanning, with subdomains, open ports, and vulnerabilities precisely mapped
- **Smart target handling** — a bare second-level domain (`example.com`) is automatically prefixed with `www`; third-level domains and IPs are used as-is; explicit ports are honored, defaulting to 80/443 otherwise
- **Live terminal feedback** — every subdomain, open port, and confirmed vulnerability is printed as it is found

## Installation

Requires Python 3.8+.

```bash
pip install -r requirements.txt
```

## Quick Start

```bash
# Run the full pipeline: subdomain mining + per-host port scan + POC verification + HTML report
python reconpulse.py -u example.com

# Scan a specific port range
python reconpulse.py -u example.com -m port -p 80,443,8080 -t 200

# Subdomain mining only
python reconpulse.py -u example.com -m subdomain

# POC verification against a target with an explicit port
python reconpulse.py -u example.com:8080 -m poc
```

### POC Scan Scope Interaction

In `all` mode, you are prompted to choose the scan scope before POC verification:

```text
POC verification mode:
  [1] Full scan - verify ALL subdomains x open ports
      (N target(s), may take a long time)
  [2] Custom URL - verify a specific URL/domain only
Select mode [1/2] (default 1, Enter for full scan):
```

- Press Enter to run a full scan: verifies every subdomain x its open ports; may take a long time when targets are many
- Enter `2` then type a specific URL (e.g. `www.example.com` or `www.example.com:8080`) to verify only that target

## CLI Options

| Option | Default | Description |
|---|---|---|
| `-u, --url` | (required) | Target URL or domain, e.g. `example.com` |
| `-m, --modules` | `all` | `subdomain` / `port` / `poc` / `all` |
| `-d, --directory` | `data/subnames.txt` | Subdomain dictionary file |
| `-t, --threads` | `50` | Number of concurrent threads |
| `-p, --ports` | top-1000 | Port range, e.g. `80,443,8000-9000` |
| `-T, --timeout` | `1` | Network timeout in seconds |
| `--poc-dir` | `pocs` | Directory containing POC files |
| `--report` | `output/report.html` | HTML report output path |

## Modules

| Module | Source | Description |
|---|---|---|
| `modules/subdomain.py` | hackertarget API + DNS brute force | Collects subdomains of the target root domain |
| `modules/portscan.py` | socket connect scan | Scans a single host or multiple hosts (all subdomains) for open TCP ports |
| `modules/poc.py` | pocsuite3 subprocess | Interactive scope selection, invokes pocsuite3 in verify mode, parses JSON results |
| `modules/report.py` | self-contained HTML template | Aggregates subdomains, open ports, and POC hits into an HTML report |
| `modules/input.py` | urllib + ipaddress | Normalizes user input: `www` prefixing, port extraction, IP detection |
| `modules/logger.py` | colorlog | Colorized terminal logging |

Scan results are written to the `output/` directory: subdomains, open ports, target URL list, POC JSON results, and the HTML report (default `output/report.html`).

## Bundled POC Coverage

The `pocs/` directory ships 38 Python POCs from the official [pocsuite3](https://github.com/knownsec/pocsuite3) POC library, covering common middleware, Java frameworks, and open-source applications. All POCs run in `--verify` mode (detection only, no exploitation).

### Python POCs (`pocs/python/`)

| POC | Vulnerability |
|---|---|
| `Apache_Struts2/*` (S2-001 ~ S2-066, 26 POCs) | Apache Struts2 RCE series, including S2-045 (CVE-2017-5638), Log4j2 (CVE-2021-44228), S2-066 (CVE-2023-50164) |
| `thinkphp_rce.py` / `thinkphp_rce2.py` | ThinkPHP 5.x RCE (multiple known payloads) |
| `weblogic_cve_2017_10271_unserialization.py` | Oracle WebLogic WLS deserialization RCE (CVE-2017-10271) |
| `20210923_*vCenter*.py` | VMware vCenter Server file upload RCE (CVE-2021-22005) |
| `20211008_*apache-httpd*.py` | Apache httpd directory traversal + RCE (CVE-2021-41773 / 42013) |
| `20190404_*Confluence*.py` | Atlassian Confluence path traversal |
| `redis_unauthorized_access.py` | Redis unauthorized access (no-auth) |
| `drupalgeddon2.py` | Drupalgeddon2 RCE (CVE-2018-7600) |
| `ecshop_rce.py` | ECShop shopping cart RCE |
| `libssh_auth_bypass.py` | libSSH authentication bypass (CVE-2018-10933) |
| `node_red_unauthorized_rce.py` | Node-RED unauthorized RCE |
| `wd_nas_login_bypass_rce.py` | Western Digital NAS login bypass RCE |

## Adding New POCs

`load_poc_files()` in `modules/poc.py` recursively scans `pocs/` and accepts `.py` files. Drop a new file into `pocs/python/` (Python format); it is picked up automatically on the next scan. A file named `__init__.py` is always ignored.

### Python format (pocsuite3)

Python POCs must follow the pocsuite3 format. Use the template below as a starting point and fill in the class fields plus the `_verify` method:

```python
from pocsuite3.api import Output, POCBase, register_poc, requests

class DemoPOC(POCBase):
    vulID = "0"           # Seebug SSVID or 0
    name = "Example vulnerability"   # <vendor> <component> <version> <type> <CVE>
    appName = "ExampleApp"
    vulType = "Code Execution"
    desc = "Short description"

    def _verify(self):
        result = {}
        # send detection request, put evidence into result if vulnerable
        resp = requests.get(self.url + "/path")
        if "marker" in resp.text:
            result["VerifyInfo"] = {"URL": self.url}
        return self.parse_output(result)

register_poc(DemoPOC)
```

Key rules: inherit `POCBase`; implement `_verify()` (required) and optionally `_attack()`; return `self.parse_output(result)`; register with `register_poc`. When the POC needs third-party modules, list them in `install_requires` (e.g. `["BeautifulSoup4:bs4"]`). Always wrap network calls in `try/except` and set an explicit `timeout`, otherwise a hanging target will produce noisy tracebacks during batch verification.

After adding a POC, verify it loads and runs:

```bash
python -m pocsuite3.cli -r pocs -f targets.txt --verify --quiet --threads 5
```

The line `pocsusite got a total of N tasks` confirms the POCs were parsed successfully.

## Project Structure

```
reconpulse.py              # CLI entry point
modules/
  ├── input.py             # Target normalization rules
  ├── logger.py            # Terminal logging
  ├── subdomain.py         # Subdomain mining
  ├── portscan.py          # Port scanning (single / multi host)
  ├── poc.py               # POC verification (scope interaction + pocsuite3)
  └── report.py            # HTML report generation
data/subnames.txt          # Subdomain dictionary
pocs/                      # POC library
  └── python/              # Python-format POCs (pocsuite3 format)
      └── Apache_Struts2/  # Struts2 POC collection (S2-001 ~ S2-066)
output/                    # Scan results (auto-generated)
```

## Disclaimer

ReconPulse is intended for security testing of systems you own or are explicitly authorized to test. POC verification sends active requests to targets and may trigger alerts on the target side. You are solely responsible for using this tool in compliance with applicable laws and regulations.

## License

[MIT](LICENSE)

---

[简体中文文档](./README.zh-CN.md) | **English**
