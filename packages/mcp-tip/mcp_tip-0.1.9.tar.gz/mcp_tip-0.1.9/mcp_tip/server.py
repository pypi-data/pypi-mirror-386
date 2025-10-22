# -*- coding: UTF-8 -*-
'''
@File    ：server
@Date    ：2025/10/20 14:36 
@Author  ：Fbx
'''
import os
import json
import requests
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ThreatBook IP‑Lookup")

def load_config() -> Dict[str, Any]:
    """从环境变量中读取配置参数"""
    api_url = os.getenv("TIP_API_URL")
    apikey = os.getenv("TIP_APIKEY")
    lang = os.getenv("TIP_LANG", "zh")

    if not api_url or not apikey:
        raise RuntimeError("环境变量 API_URL 或 APIKEY 未设置")
    
    return {
        "api_url": api_url,
        "apikey": apikey,
        "lang": lang
    }


def _call_threatbook_api(resource: str, api_type: str, timeout: float = 10.0) -> Dict[str, Any]:
    cfg = load_config()
    base_url = cfg.get("api_url")
    apikey = cfg.get("apikey")
    lang = cfg.get("lang", "zh")
    
    # 根据查询类型构建完整的API URL
    if api_type == "ip":
        api_url = base_url.rstrip('/') + "/tip_api/v5/ip"
    elif api_type == "dns":
        api_url = base_url.rstrip('/') + "/tip_api/v5/dns"
    elif api_type == "location":
        api_url = base_url.rstrip('/') + "/tip_api/v5/location"
    elif api_type == "hash":
        api_url = base_url.rstrip('/') + "/tip_api/v5/hash"
    else:
        return {"ok": False, "error": {"code": "INVALID_TYPE", "message": f"不支持的查询类型: {api_type}"}}
    
    # 根据API类型使用不同的参数名
    params = {"apikey": apikey, "resource": resource}
    if api_type in {"ip", "dns"}:
        params["lang"] = lang
    
    try:
        resp = requests.get(api_url, params=params, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        msg = f"网络请求失败: {e}"
        return {"ok": False, "error": {"code": "REQUEST_ERROR", "message": msg}}

    try:
        data = resp.json()
    except (ValueError, json.JSONDecodeError) as e:
        msg = f"响应不是合法 JSON: {e}; HTTP {resp.status_code}; 前1000字: {resp.text[:1000]!r}"
        return {"ok": False, "error": {"code": "INVALID_JSON", "message": msg, "status_code": resp.status_code}}
    # 成功：返回结构化结果
    return {"ok": True, "data": data}


@mcp.tool()
def search_ip(resource: str) -> Dict[str, Any]:
    """
        查询 IP 地址的威胁情报。
        调用 /tip_api/v4/ip 接口
        
        参数：
        - resource: 要查询的IP地址，如 "8.8.8.8" 或 "192.168.1.1"
        
        返回统一结构：
          成功 -> {"ok": True, "data": ...}
          失败 -> {"ok": False, "error": {"code": "...", "message": "..."}}
        """
    if not resource:
        msg = "参数 resource 非法或为空"
        return {"ok": False, "error": {"code": "INVALID_PARAM", "message": msg}}
    try:
        return _call_threatbook_api(resource, "ip")
    except Exception as e:
        raise RuntimeError(f"TTP IP API 调用失败: {e}")


@mcp.tool()
def search_domain(resource: str) -> Dict[str, Any]:
    """
        查询域名的威胁情报。
        调用 /tip_api/v4/domain 接口

        参数：
        - resource: 要查询的doamin地址，如 "maimai666.com"

        返回统一结构：
          成功 -> {"ok": True, "data": ...}
          失败 -> {"ok": False, "error": {"code": "...", "message": "..."}}
        """
    if not resource:
        msg = "参数 resource 非法或为空"
        return {"ok": False, "error": {"code": "INVALID_PARAM", "message": msg}}
    try:
        return _call_threatbook_api(resource, "dns")
    except Exception as e:
        raise RuntimeError(f"TIP DNS API 调用失败: {e}")


@mcp.tool()
def search_location(resource: str) -> Dict[str, Any]:
    """
        获取IP地理位置信息。
        调用 /tip_api/v4/location 接口

        参数：
        - resource: 要查询的ip地理位置信息，如 "8.8.8.8"

        返回统一结构：
          成功 -> {"ok": True, "data": ...}
          失败 -> {"ok": False, "error": {"code": "...", "message": "..."}}
        """
    if not resource:
        msg = "参数 resource 非法或为空"
        return {"ok": False, "error": {"code": "INVALID_PARAM", "message": msg}}
    try:
        return _call_threatbook_api(resource, "location")
    except Exception as e:
        raise RuntimeError(f"TIP Location API 调用失败: {e}")


@mcp.tool()
def search_hash(resource: str) -> Dict[str, Any]:
    """
        文件信誉检测
        调用 /tip_api/v4/hash 接口
        参数：
        - resource: 文件sha1、sha256、md5
        返回统一结构：
          成功 -> {"ok": True, "data": ...}
          失败 -> {"ok": False, "error": {"code": "...", "message": "..."}}
        """
    if not resource:
        msg = "参数 resource 非法或为空"
        return {"ok": False, "error": {"code": "INVALID_PARAM", "message": msg}}
    try:
        return _call_threatbook_api(resource, "hash")
    except Exception as e:
        raise RuntimeError(f"TIP Hash API 调用失败: {e}")


@mcp.tool()
def search_vuln(
    vuln_id: str = None,
    cursor: str = None,
    limit: int = 10,
    vendor: str = None,
    product: str = None,
    component_package_manager: str = None,
    component_name: str = None,
    version: str = None,
    update_time: str = None,
    threatbook_create_time: str = None,
    is_highrisk: bool = None
) -> Dict[str, Any]:

    """
    获取漏洞情报信息接口。
    调用 /tip_api/v5/vuln 接口

    支持以下参数：
    1. apikey (自动从环境变量获取)
    2. cursor 可选
    3. limit 可选（默认10，最大50）
    4. vuln_id 可选，最多100个，用逗号分隔
    5. vendor 可选
    6. product 可选，最多20个
    7. component_package_manager 可选
    8. component_name 可选，最多20个
    9. version 可选
    10. update_time 可选（1d,3d,7d,30d）
    11. threatbook_create_time 可选（1d,3d,7d,30d）
    12. is_highrisk 可选（布尔值）
        返回统一结构：
          成功 -> {"ok": True, "data": ...}
          失败 -> {"ok": False, "error": {"code": "...", "message": "..."}}
        """
    cfg = load_config()
    api_url = cfg.get("api_url").rstrip('/') + "/tip_api/v5/vuln"
    apikey = cfg.get("apikey")

    # ---------- 参数校验 ----------
    errors = []

    if limit is not None:
        if not isinstance(limit, int) or limit <= 0:
            errors.append("limit 必须是正整数")
        elif limit > 50:
            errors.append("limit 不能超过 50")

    if vuln_id:
        ids = vuln_id.split(",")
        if len(ids) > 100:
            errors.append("vuln_id 最多支持 100 个，以逗号分隔")

    if product:
        prods = product.split(",")
        if len(prods) > 20:
            errors.append("product 最多支持 20 个，以逗号分隔")

    if component_name:
        comps = component_name.split(",")
        if len(comps) > 20:
            errors.append("component_name 最多支持 20 个，以逗号分隔")

    if update_time and update_time not in {"1d", "3d", "7d", "30d"}:
        errors.append("update_time 仅支持 1d,3d,7d,30d")

    if threatbook_create_time and threatbook_create_time not in {"1d", "3d", "7d", "30d"}:
        errors.append("threatbook_create_time 仅支持 1d,3d,7d,30d")

    if errors:
        return {"ok": False, "error": {"code": "INVALID_PARAM", "message": "；".join(errors)}}

    # ---------- 组装参数 ----------
    params = {"apikey": apikey}

    # 只加入非空参数
    optional_params = {
        "cursor": cursor,
        "limit": limit,
        "vuln_id": vuln_id,
        "vendor": vendor,
        "product": product,
        "component_package_manager": component_package_manager,
        "component_name": component_name,
        "version": version,
        "update_time": update_time,
        "threatbook_create_time": threatbook_create_time,
        "is_highrisk": is_highrisk,
    }

    for key, value in optional_params.items():
        if value is not None and value != "":
            params[key] = value

        # ---------- 发起请求 ----------
        try:
            resp = requests.get(api_url, params=params, timeout=10.0)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            return {"ok": False, "error": {"code": "REQUEST_ERROR", "message": f"网络请求失败: {e}"}}

        # ---------- 响应解析 ----------
        try:
            data = resp.json()
        except (ValueError, json.JSONDecodeError) as e:
            msg = f"响应不是合法 JSON: {e}; HTTP {resp.status_code}; 前1000字: {resp.text[:1000]!r}"
            return {"ok": False, "error": {"code": "INVALID_JSON", "message": msg}}

        return {"ok": True, "data": data}


def main():
    mcp.run()

if __name__ == "__main__":
    main()

app = mcp