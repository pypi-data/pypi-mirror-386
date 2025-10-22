# -*- coding: UTF-8 -*-
'''
@File    ：test_server.py
@Date    ：2025/10/20 14:42 
@Author  ：Fbx
'''

import asyncio
import json
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_ip_query():
    """使用官方 MCP Python SDK 测试 IP 查询功能"""
    print("=" * 60)
    print("MCP 客户端测试 - 使用官方 SDK")
    print("=" * 60)
    
    # 设置服务器参数
    server_params = StdioServerParameters(
        command="uvx",
        args=["--from", "mcp-tip", "mcp_threatbook"],
        env={
            "TIP_API_URL": "https://tip91-8090.threatbook-inc.cn",
            "TIP_APIKEY": "62b04f6bd6a64cc6bc53e1b340b4fbb8"
        }
    )
    
    try:
        print("[连接] 正在连接到 MCP 服务器...")
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # 初始化连接
                print("[初始化] 正在初始化连接...")
                await session.initialize()
                
                # 获取可用工具列表
                print("[工具] 正在获取可用工具列表...")
                tools = await session.list_tools()
                print(f"[工具] 发现 {len(tools.tools)} 个工具:")
                for tool in tools.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                print("\n" + "-" * 40)
                print("开始测试 IP 查询")
                print("-" * 40)
                
                # 调用 search_ip 工具
                ip_to_search = "8.8.8.8"
                print(f"[查询] 正在查询 IP: {ip_to_search}")
                
                result = await session.call_tool(
                    "search_ip", 
                    arguments={"resource": ip_to_search}
                )
                
                print(f"[结果] IP 查询结果:")
                for content in result.content:
                    if hasattr(content, 'text'):
                        print(content.text)
                    else:
                        print(str(content))
                
                # 分析结果
                if result.content:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        try:
                            data = json.loads(content.text)
                            if data.get("ok"):
                                print(f"\n[成功] IP 查询成功!")
                                print(f"[数据] 响应代码: {data.get('data', {}).get('response_code', 'N/A')}")
                                print(f"[数据] 响应消息: {data.get('data', {}).get('verbose_msg', 'N/A')}")
                            else:
                                print(f"\n[失败] IP 查询失败!")
                                error = data.get("error", {})
                                print(f"[错误] 错误代码: {error.get('code', 'N/A')}")
                                print(f"[错误] 错误消息: {error.get('message', 'N/A')}")
                        except json.JSONDecodeError:
                            print(f"[数据] 原始响应: {content.text}")
                    else:
                        print(f"[数据] 响应内容: {content}")
                
    except Exception as e:
        print(f"[错误] 连接或调用失败: {e}")
        import traceback
        traceback.print_exc()


async def test_all_tools():
    """测试所有可用工具"""
    print("=" * 60)
    print("MCP 客户端测试 - 所有工具")
    print("=" * 60)
    
    server_params = StdioServerParameters(
        command="uvx",
        args=["--from", "mcp-tip", "mcp_threatbook"],
        env={
            "TIP_API_URL": "https://tip91-8090.threatbook-inc.cn",
            "TIP_APIKEY": "62b04f6bd6a64cc6bc53e1b340b4fbb8"
        }
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # 获取工具列表
                tools = await session.list_tools()
                print(f"[工具] 发现 {len(tools.tools)} 个工具:")
                for tool in tools.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                # 测试各种工具
                test_cases = [
                    ("search_ip", {"resource": "8.8.8.8"}),
                    ("search_domain", {"resource": "google.com"}),
                    ("search_location", {"resource": "8.8.8.8"}),
                    ("search_hash", {"resource": "d41d8cd98f00b204e9800998ecf8427e"}),
                    ("search_vuln", {"vuln_id": "CVE-2021-44228"})
                ]
                
                results = []
                
                for tool_name, args in test_cases:
                    print(f"\n[测试] {tool_name}")
                    print("-" * 30)
                    
                    try:
                        result = await session.call_tool(tool_name, arguments=args)
                        
                        if result.content:
                            print(f"[成功] {tool_name} 调用成功")
                            results.append((tool_name, True))
                            
                            # 显示结果摘要
                            content = result.content[0]
                            if hasattr(content, 'text'):
                                try:
                                    data = json.loads(content.text)
                                    if data.get("ok"):
                                        print(f"[数据] 查询成功")
                                    else:
                                        print(f"[数据] 查询失败: {data.get('error', {}).get('message', '未知错误')}")
                                except:
                                    print(f"[数据] 原始响应: {content.text[:100]}...")
                        else:
                            print(f"[失败] {tool_name} 调用失败 - 无响应内容")
                            results.append((tool_name, False))
                            
                    except Exception as e:
                        print(f"[失败] {tool_name} 调用异常: {e}")
                        results.append((tool_name, False))
                
                # 打印总结
                print("\n" + "=" * 60)
                print("测试总结")
                print("=" * 60)
                
                total = len(results)
                success = sum(1 for _, s in results if s)
                failed = total - success
                
                print(f"总测试数: {total}")
                print(f"成功: {success}")
                print(f"失败: {failed}")
                print(f"成功率: {(success/total*100):.1f}%")
                
                print("\n详细结果:")
                for tool_name, success in results:
                    status = "[成功]" if success else "[失败]"
                    print(f"  {status} {tool_name}")
                
    except Exception as e:
        print(f"[错误] 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("MCP ThreatBook 客户端测试工具 (使用官方 SDK)")
    print("=" * 60)
    
    # 直接运行 IP 查询测试
    print("运行 IP 查询测试...")
    asyncio.run(test_ip_query())


if __name__ == "__main__":
    main()