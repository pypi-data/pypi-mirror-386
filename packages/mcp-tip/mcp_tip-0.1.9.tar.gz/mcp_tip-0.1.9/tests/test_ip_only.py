# -*- coding: UTF-8 -*-
'''
@File    ：test_ip_only.py
@Date    ：2025/10/20 15:00 
@Author  ：Fbx
'''

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_single_ip():
    """使用官方 MCP SDK 单独测试 IP 查询功能"""
    print("=" * 50)
    print("MCP 客户端 - IP 查询测试")
    print("=" * 50)
    
    # 设置服务器参数
    server_params = StdioServerParameters(
        command="uvx",
        args=["--from", "mcp-tip", "mcp_threatbook"],
        env={
            "TIP_API_URL": "https://tip91-8090.threatbook-inc.cn",
            "TIP_APIKEY": "62b04f6bd6a64cc6bc53e1b340b4fbb8"
        }
    )
    
    # 要查询的 IP 地址
    test_ip = "8.8.8.8"
    
    print(f"正在查询 IP: {test_ip}")
    print("-" * 30)
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # 初始化连接
                await session.initialize()
                
                # 调用 search_ip 工具
                result = await session.call_tool(
                    "search_ip", 
                    arguments={"resource": test_ip}
                )
                
                print("查询结果:")
                for content in result.content:
                    if hasattr(content, 'text'):
                        print(content.text)
                
                # 分析结果
                if result.content:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        try:
                            data = json.loads(content.text)
                            if data.get("ok"):
                                print(f"\n查询成功!")
                                response_data = data.get("data", {})
                                print(f"响应代码: {response_data.get('response_code', 'N/A')}")
                                print(f"响应消息: {response_data.get('verbose_msg', 'N/A')}")
                                
                                # 显示威胁情报摘要
                                intelligence_data = response_data.get("data", [])
                                if intelligence_data:
                                    for item in intelligence_data:
                                        print(f"\nIOC: {item.get('ioc', 'N/A')}")
                                        intelligence = item.get('intelligence', [])
                                        for intel in intelligence:
                                            print(f"  类型: {intel.get('type', 'N/A')}")
                                            print(f"  恶意性: {'是' if intel.get('is_malicious') else '否'}")
                                            print(f"  严重程度: {intel.get('severity', 'N/A')}")
                                            print(f"  置信度: {intel.get('confidence_level', 'N/A')}")
                                            judgments = intel.get('judgments', [])
                                            if judgments:
                                                print(f"  判断: {', '.join(judgments)}")
                            else:
                                print(f"\n查询失败!")
                                error = data.get("error", {})
                                print(f"错误代码: {error.get('code', 'N/A')}")
                                print(f"错误消息: {error.get('message', 'N/A')}")
                        except json.JSONDecodeError:
                            print(f"原始响应: {content.text}")
                    else:
                        print(f"响应内容: {content}")
                        
    except Exception as e:
        print(f"测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_single_ip())