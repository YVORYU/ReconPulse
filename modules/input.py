# -*- coding: utf-8 -*-
"""用户输入统一规范化：端口扫描与子域名挖掘共用同一套规则"""
import ipaddress
from urllib.parse import urlparse


# 常见的双段后缀（如 co.uk、com.cn），遇到时注册域要往前多取一级
MULTI_SUFFIX = {"co", "com", "net", "org", "gov", "ac", "edu"}


def extract_host(url):
    """提取完整主机名，如 http://www.example.com:8080/path -> www.example.com"""
    url = url.strip()
    if not url:
        return None
    if "://" not in url:
        url = "http://" + url
    netloc = urlparse(url).netloc          # 取 "www.example.com:8080" 部分
    if ":" in netloc:
        netloc = netloc.split(":")[0]      # 去掉端口
    return netloc


def get_root_domain(host):
    """提取注册域，如 www.example.com -> example.com；example.co.uk -> example.co.uk；IP 原样返回"""
    if not host:
        return None
    try:
        ipaddress.ip_address(host)         # 是 IP 地址则原样返回，不提取
        return host
    except ValueError:
        pass
    parts = host.split(".")
    if len(parts) > 2:
        if parts[-2] in MULTI_SUFFIX:      # co.uk / com.cn 这类双段后缀，注册域取最后三级
            return ".".join(parts[-3:])
        return ".".join(parts[-2:])
    return host


def normalize_target(url):
    """整理用户输入，返回 (scan_host, root_domain)。

    scan_host:   端口扫描用主机名。裸注册域（如 example.com）自动补为 www.example.com，
                 完整域名（如 www.example.com）原样使用，IP 地址原样使用
    root_domain: 子域名挖掘用注册域。IP 地址没有子域名概念，返回 None
    """
    host = extract_host(url)
    if not host:
        return None, None
    try:
        ipaddress.ip_address(host)         # IP 地址：无需补 www，也无子域名
        return host, None
    except ValueError:
        pass
    root = get_root_domain(host)
    if host == root:                       # 输入是裸注册域，端口扫描补 www.
        scan_host = "www." + host
    else:
        scan_host = host
    return scan_host, root
