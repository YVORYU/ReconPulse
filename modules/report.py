
import html
import os
from datetime import datetime

from modules.logger import info


def build_report_data(target, host_port_map, subdomains, poc_hits):
    return {
        "target": target,
        "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "subdomains": sorted(subdomains) if subdomains else [],
        "host_port_map": host_port_map or {},
        "poc_hits": poc_hits or [],
    }


def _escape(text):
    return html.escape(str(text))


def _render_subdomain_table(data):
    if not data["host_port_map"]:
        return '<p class="empty">No subdomains or open ports found.</p>'

    rows = []
    for host, ports in data["host_port_map"].items():
        port_text = ", ".join(str(p) for p in ports) if ports else "-"
        rows.append(
            f"<tr><td class='mono'>{_escape(host)}</td>"
            f"<td class='mono'>{_escape(port_text)}</td></tr>"
        )
    return (
        "<table><thead><tr><th>Subdomain / Host</th><th>Open Ports</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def _format_result_detail(result):
    if not result:
        return "-"
    if not isinstance(result, dict):
        return _escape(result)
    for key in ("VerifyInfo", "Stdout", "DBInfo", "FileInfo", "XSSInfo"):
        val = result.get(key)
        if val:
            if isinstance(val, dict):
 
                parts = []
                for k, v in val.items():
                    parts.append(f"{k}: {v}")
                return _escape(", ".join(parts))
            return _escape(val)
    parts = [f"{k}: {v}" for k, v in result.items()]
    return _escape("; ".join(parts))


def _render_poc_table(data):
    if not data["poc_hits"]:
        return '<p class="empty">No vulnerabilities detected.</p>'

    rows = []
    for poc_name, target, result in data["poc_hits"]:
        try:
            host_port = target.split("://")[1]
        except IndexError:
            host_port = target
        rows.append(
            f"<tr><td class='mono'>{_escape(host_port)}</td>"
            f"<td>{_escape(poc_name)}</td>"
            f"<td class='mono'>{_format_result_detail(result)}</td></tr>"
        )
    return (
        "<table><thead><tr><th>Target (host:port)</th><th>POC Name</th>"
        "<th>Detail</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def generate_html_report(data, output_path=None):
    if not output_path:
        os.makedirs("output", exist_ok=True)
        output_path = os.path.join("output", "report.html")

    subdomain_count = len(data["host_port_map"])
    port_count = sum(len(v) for v in data["host_port_map"].values())
    vuln_count = len(data["poc_hits"])

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>ReconPulse Report - {_escape(data['target'])}</title>
<style>
  body {{ font-family: "Segoe UI", "Microsoft YaHei", sans-serif; margin: 0; background: #f5f7fa; color: #24292f; }}
  .header {{ background: linear-gradient(135deg, #1f2328, #3a4148); color: #fff; padding: 28px 40px; }}
  .header h1 {{ margin: 0 0 8px 0; font-size: 24px; }}
  .header p {{ margin: 2px 0; opacity: .85; font-size: 13px; }}
  .container {{ max-width: 960px; margin: 24px auto; padding: 0 24px; }}
  .card {{ background: #fff; border: 1px solid #e1e4e8; border-radius: 8px; padding: 20px 24px; margin-bottom: 20px; }}
  .card h2 {{ margin: 0 0 14px 0; font-size: 17px; border-left: 4px solid #0969da; padding-left: 10px; }}
  .stats {{ display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }}
  .stat {{ flex: 1; min-width: 140px; background: #fff; border: 1px solid #e1e4e8; border-radius: 8px; padding: 14px 18px; text-align: center; }}
  .stat .num {{ font-size: 26px; font-weight: 700; color: #0969da; }}
  .stat .label {{ font-size: 12px; color: #57606a; margin-top: 4px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th, td {{ border: 1px solid #e1e4e8; padding: 8px 10px; text-align: left; }}
  th {{ background: #f6f8fa; font-weight: 600; }}
  tr:nth-child(even) td {{ background: #fafbfc; }}
  .mono {{ font-family: Consolas, "Courier New", monospace; font-size: 12px; }}
  .empty {{ color: #57606a; font-style: italic; }}
  .footer {{ text-align: center; color: #57606a; font-size: 12px; margin: 28px 0 40px; }}
</style>
</head>
<body>
  <div class="header">
    <h1>ReconPulse Scan Report</h1>
    <p>Target: {_escape(data['target'])}</p>
    <p>Scan time: {_escape(data['scan_time'])}</p>
  </div>
  <div class="container">
    <div class="stats">
      <div class="stat"><div class="num">{subdomain_count}</div><div class="label">Subdomains</div></div>
      <div class="stat"><div class="num">{port_count}</div><div class="label">Open Ports</div></div>
      <div class="stat"><div class="num">{vuln_count}</div><div class="label">Vulnerabilities</div></div>
    </div>
    <div class="card">
      <h2>Subdomain &amp; Port Mapping</h2>
      {_render_subdomain_table(data)}
    </div>
    <div class="card">
      <h2>POC Verification Results</h2>
      {_render_poc_table(data)}
    </div>
    <div class="footer">Generated by ReconPulse</div>
  </div>
</body>
</html>
"""

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(page)
    info(f"HTML report generated: {output_path}")
    return output_path
