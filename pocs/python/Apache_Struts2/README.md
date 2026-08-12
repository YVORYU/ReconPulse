# Struts2 Exploits (pocsuite3)

## Legal Disclaimer

Unauthorized use of vulnerabilities to attack targets without prior mutual consent is illegal. This collection only keeps publicly disclosed historical Struts2 vulnerabilities for learning and research purposes.

## 法律免责声明

未经事先双方同意，使用漏洞攻击目标是非法的。本目录仅保留已公开的 Struts2 历史漏洞信息，仅供学习和研究目的。

## Overview

Bundled Struts2 POCs, authored in the pocsuite3 format. Run them through ReconPulse (`-m poc`) or directly with the `pocsuite` CLI.

## Vulnerability Environment

Docker image for the vulnerable environment:

```
docker run -it -p 8080:8080 isxiangyang/struts2-all-vul-pocsuite:latest
```

## Bundled POCs

### S2-045 (CVE-2017-5638)

http://localhost:8080/S2-032-showcase/fileupload/doUpload.action

```
pocsuite -r 20170129_WEB_Apache_Struts2_045_RCE_CVE-2017-5638.py -u http://localhost:8080/S2-032-showcase/fileupload/doUpload.action --attack --command whoami
```

### Log4j2 (CVE-2021-44228, Log4Shell)

```
pocsuite -r 20211126_WEB_Apache_Struts2_Log4j2_RCE_CVE-2021-44228.py -u http://localhost:8080 --verify
```

### S2-066 (CVE-2023-50164)

http://127.0.0.1:8080/S2-066/upload

```
pocsuite -r 20231204_WEB_Apache_Struts2_066_RCE_CVE-2023-50164.py -u http://127.0.0.1:8080/S2-066/upload
```
