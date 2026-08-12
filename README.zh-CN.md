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

**简体中文** | [English](./README.md)

一款自动化的信息收集与漏洞验证工具，将子域名挖掘、端口扫描、POC 漏洞验证串联为一条命令行工作流，并输出 HTML 报告。核心功能基于纯 Python 实现，漏洞验证阶段接入开源框架 [pocsuite3](https://github.com/knownsec/pocsuite3)。

## 功能特性

- **子域名挖掘** — 通过 [hackertarget](https://api.hackertarget.com/hostsearch/) 被动收集，配合 DNS 字典爆破
- **端口扫描** — 多线程 TCP 连接扫描，默认使用 nmap 前 1000 常用端口，支持自定义范围如 `80,443,8000-9000`；`all` 模式下对主域名和每个子域名分别扫描
- **POC 验证** — 内置 38 个 Python POC，全部来源于 [pocsuite3](https://github.com/knownsec/pocsuite3) 官方 POC 库（Struts2 全系列 S2-001~S2-066、ThinkPHP、WebLogic、Log4j2、Redis 未授权访问、Confluence、Drupal 等），统一以 `--verify` 验证模式运行（仅检测，不利用）。POC 存放于 `pocs/python/`
- **扫描范围交互选择** — `all` 模式开启 POC 验证前可选择：全量扫描所有子域名 × 开放端口（默认），或输入特定 URL 只验证单个目标
- **HTML 报告** — 扫描结束自动生成自包含 HTML 报告，子域名、开放端口、漏洞三者精确对应
- **智能目标处理** — 裸二级域名（`example.com`）自动补 `www` 前缀；三级域名和 IP 原样使用；显式指定端口时按输入端口，否则默认 80/443
- **终端实时反馈** — 每发现一个子域名、开放端口、漏洞命中都即时打印

## 安装

需要 Python 3.8 及以上版本。

```bash
pip install -r requirements.txt
```

## 快速开始

```bash
# 完整流程：子域名挖掘 + 逐主机端口扫描 + POC 验证 + HTML 报告
python reconpulse.py -u example.com

# 指定端口范围扫描
python reconpulse.py -u example.com -m port -p 80,443,8080 -t 200

# 仅子域名挖掘
python reconpulse.py -u example.com -m subdomain

# 对带端口的显式目标做 POC 验证
python reconpulse.py -u example.com:8080 -m poc
```

### POC 扫描范围交互

`all` 模式下，POC 验证开启前会提示选择扫描范围：

```text
POC verification mode:
  [1] Full scan - verify ALL subdomains x open ports
      (N target(s), may take a long time)
  [2] Custom URL - verify a specific URL/domain only
Select mode [1/2] (default 1, Enter for full scan):
```

- 直接回车执行全量扫描：验证全部子域名 × 各自开放端口，目标多时可能耗时较长
- 输入 `2` 后填写特定 URL（如 `www.example.com` 或 `www.example.com:8080`），只验证该目标

## 命令行参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `-u, --url` | 必填 | 目标地址或域名，如 `example.com` |
| `-m, --modules` | `all` | `subdomain` / `port` / `poc` / `all` |
| `-d, --directory` | `data/subnames.txt` | 子域名字典文件 |
| `-t, --threads` | `50` | 并发线程数 |
| `-p, --ports` | 前 1000 常用端口 | 端口范围，如 `80,443,8000-9000` |
| `-T, --timeout` | `1` | 网络超时（秒） |
| `--poc-dir` | `pocs` | POC 文件所在目录 |
| `--report` | `output/report.html` | HTML 报告输出路径 |

## 模块说明

| 模块 | 来源 | 功能 |
|---|---|---|
| `modules/subdomain.py` | hackertarget API + DNS 爆破 | 收集目标注册域的子域名 |
| `modules/portscan.py` | socket 连接扫描 | 单主机或多主机（含全部子域名）并发检测开放 TCP 端口 |
| `modules/poc.py` | pocsuite3 子进程调用 | 全量/自定义目标交互选择，调用 pocsuite3 验证模式，解析 JSON 结果 |
| `modules/report.py` | 自包含 HTML 模板 | 汇总子域名、开放端口、POC 命中，生成 HTML 报告 |
| `modules/input.py` | urllib + ipaddress | 规范化用户输入：补 `www`、提取端口、识别 IP |
| `modules/logger.py` | colorlog | 终端彩色日志输出 |

扫描结果写入 `output/` 目录：子域名、开放端口、目标 URL 列表、POC 验证 JSON 结果，以及 HTML 报告（默认 `output/report.html`）。

## 内置 POC 漏洞覆盖

`pocs/` 目录内置 38 个 Python POC，全部来源于 [pocsuite3](https://github.com/knownsec/pocsuite3) 官方 POC 库，覆盖常见中间件、Java 框架与开源应用。所有 POC 均以 `--verify` 验证模式运行（仅检测，不利用）。

### Python 格式 POC（`pocs/python/`）

| POC | 漏洞 |
|---|---|
| `Apache_Struts2/*`（S2-001 ~ S2-066，26 个） | Apache Struts2 RCE 系列，含 S2-045（CVE-2017-5638）、Log4j2（CVE-2021-44228）、S2-066（CVE-2023-50164） |
| `thinkphp_rce.py` / `thinkphp_rce2.py` | ThinkPHP 5.x 远程代码执行（多个已知 payload） |
| `weblogic_cve_2017_10271_unserialization.py` | Oracle WebLogic WLS 反序列化 RCE（CVE-2017-10271） |
| `20210923_*vCenter*.py` | VMware vCenter Server 文件上传 RCE（CVE-2021-22005） |
| `20211008_*apache-httpd*.py` | Apache httpd 目录遍历 + RCE（CVE-2021-41773 / 42013） |
| `20190404_*Confluence*.py` | Atlassian Confluence 目录遍历 |
| `redis_unauthorized_access.py` | Redis 未授权访问（无认证） |
| `drupalgeddon2.py` | Drupalgeddon2 远程代码执行（CVE-2018-7600） |
| `ecshop_rce.py` | ECShop 购物车远程代码执行 |
| `libssh_auth_bypass.py` | libSSH 认证绕过（CVE-2018-10933） |
| `node_red_unauthorized_rce.py` | Node-RED 未授权远程代码执行 |
| `wd_nas_login_bypass_rce.py` | 西部数据 NAS 登录绕过 RCE |

## 如何添加新的 POC

`modules/poc.py` 中的 `load_poc_files()` 会递归扫描 `pocs/` 目录，识别 `.py` 扩展名。把新文件放入 `pocs/python/`（Python 格式）即可，下次扫描自动生效；名为 `__init__.py` 的文件会被忽略。

### Python 格式（pocsuite3 规范）

Python 格式 POC 必须遵循 pocsuite3 规范，按下方模板填充类字段并实现 `_verify` 方法：

```python
from pocsuite3.api import Output, POCBase, register_poc, requests

class DemoPOC(POCBase):
    vulID = "0"           # Seebug SSVID 或 0
    name = "示例漏洞"      # <厂商> <组件> <版本> <漏洞类型> <CVE>
    appName = "ExampleApp"
    vulType = "Code Execution"
    desc = "简要描述"

    def _verify(self):
        result = {}
        # 发送检测请求，命中则把证据写入 result
        resp = requests.get(self.url + "/path")
        if "marker" in resp.text:
            result["VerifyInfo"] = {"URL": self.url}
        return self.parse_output(result)

register_poc(DemoPOC)
```

关键规则：继承 `POCBase`；实现 `_verify()`（必填）和可选的 `_attack()`；返回 `self.parse_output(result)`；用 `register_poc` 注册。若 POC 依赖第三方模块，在 `install_requires` 中声明（如 `["BeautifulSoup4:bs4"]`）。网络请求务必用 `try/except` 包裹并显式设置 `timeout`，否则目标无响应时会在批量验证中刷出大量 traceback。

添加 POC 后，可用以下命令验证能否被加载执行：

```bash
python -m pocsuite3.cli -r pocs -f targets.txt --verify --quiet --threads 5
```

输出中出现 `pocsusite got a total of N tasks` 即代表 POC 解析成功。

## 项目结构

```
reconpulse.py              # 命令行入口
modules/
  ├── input.py             # 目标规范化规则
  ├── logger.py            # 终端日志
  ├── subdomain.py         # 子域名挖掘
  ├── portscan.py          # 端口扫描（单主机/多主机）
  ├── poc.py               # POC 验证（扫描范围交互 + pocsuite3 调用）
  └── report.py            # HTML 报告生成
data/subnames.txt          # 子域名字典
pocs/                      # POC 库
  └── python/              # Python 格式 POC（pocsuite3 格式）
      └── Apache_Struts2/  # Struts2 漏洞合集（S2-001 ~ S2-066）
output/                    # 扫描结果（自动生成）
```

## 免责声明

ReconPulse 仅用于测试你拥有或获得明确授权的系统。POC 验证会向目标发送主动请求，可能触发目标侧的告警。使用者需自行确保符合所在地区法律法规及授权范围。

## 许可证

[MIT](LICENSE)

---

**简体中文** | [English](./README.md)
