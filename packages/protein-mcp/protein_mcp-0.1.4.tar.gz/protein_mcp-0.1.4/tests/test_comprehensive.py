#!/usr/bin/env python3
"""
Protein MCP服务器简化综合测试
专注于核心功能验证，避免复杂的会话管理
"""

import json
import os
import time

import requests

# 禁用代理
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)


def test_comprehensive():
    """综合测试所有核心功能"""
    base_url = "http://localhost:37787/mcp"
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}

    print("🔬 Protein MCP服务器综合测试")
    print("=" * 50)

    session_id = None
    test_count = 0
    passed_count = 0

    def parse_sse_response(response_text):
        """解析SSE响应"""
        if "event: message" in response_text:
            lines = response_text.split("\n")
            for line in lines:
                if line.startswith("data: "):
                    try:
                        return json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue
        return None

    def run_test(test_name, payload, expected_success=True):
        nonlocal test_count, passed_count
        test_count += 1

        print(f"\n🧪 测试 {test_count}: {test_name}")

        try:
            response_headers = headers.copy()
            if session_id:
                response_headers["Mcp-Session-Id"] = session_id

            start_time = time.time()
            response = requests.post(
                base_url, json=payload, headers=response_headers, timeout=30, proxies={}
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = parse_sse_response(response.text)
                if data:
                    # 检查是否是工具调用响应
                    if "result" in data:
                        result = data["result"]
                        structured_content = result.get("structuredContent", {})
                        success = structured_content.get("success", False)
                        message = structured_content.get("message", "")

                        if success == expected_success:
                            passed_count += 1
                            print(f"   ✅ 通过 ({response_time:.2f}s)")
                            print(f"   消息: {message[:100]}...")
                            return True
                        else:
                            print(f"   ❌ 失败 - 预期成功: {expected_success}, 实际: {success}")
                            print(f"   消息: {message}")
                            return False
                    # 检查是否是工具列表响应
                    elif "result" in data and "tools" in data["result"]:
                        tools = data["result"]["tools"]
                        print(f"   ✅ 工具列表获取成功 - {len(tools)} 个工具")
                        for tool in tools:
                            print(f"   • {tool.get('name', 'Unknown')}")
                        passed_count += 1
                        return True
                    else:
                        print("   ❌ 未知响应格式")
                        return False
                else:
                    print("   ❌ 无法解析响应")
                    return False
            else:
                print(f"   ❌ HTTP错误: {response.status_code}")
                return False

        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")
            return False

    # 1. 初始化会话
    print("\n🔧 初始化会话...")
    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "comprehensive-test", "version": "1.0.0"},
        },
    }

    try:
        response = requests.post(
            base_url, json=init_payload, headers=headers, timeout=10, proxies={}
        )
        if response.status_code == 200:
            session_id = response.headers.get("Mcp-Session-Id")
            print(f"✅ 会话ID: {session_id}")
        else:
            print(f"❌ 初始化失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 初始化错误: {str(e)}")
        return False

    # 2. 发送initialized通知
    try:
        notif_headers = headers.copy()
        if session_id:
            notif_headers["Mcp-Session-Id"] = session_id

        notif_payload = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}

        requests.post(base_url, json=notif_payload, headers=notif_headers, timeout=10, proxies={})
        print("✅ initialized通知已发送")
    except Exception as e:
        print(f"❌ 通知发送失败: {str(e)}")

    # 3. 测试工具列表
    tools_payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    run_test("获取工具列表", tools_payload)

    # 4. 测试find_protein_structures工具
    print("\n🔍 测试 find_protein_structures 工具")

    find_tests = [
        (
            "默认模式",
            {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {"name": "find_protein_structures_tool", "arguments": {}},
            },
        ),
        (
            "癌症靶点示例",
            {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {
                    "name": "find_protein_structures_tool",
                    "arguments": {"category": "癌症靶点"},
                },
            },
        ),
        (
            "PDB验证",
            {
                "jsonrpc": "2.0",
                "id": 12,
                "method": "tools/call",
                "params": {"name": "find_protein_structures_tool", "arguments": {"pdb_id": "1A3N"}},
            },
        ),
        (
            "关键词搜索",
            {
                "jsonrpc": "2.0",
                "id": 13,
                "method": "tools/call",
                "params": {
                    "name": "find_protein_structures_tool",
                    "arguments": {"keywords": "hemoglobin", "max_results": 5},
                },
            },
        ),
        (
            "无效PDB ID",
            {
                "jsonrpc": "2.0",
                "id": 14,
                "method": "tools/call",
                "params": {
                    "name": "find_protein_structures_tool",
                    "arguments": {"pdb_id": "INVALID"},
                },
                "expected_success": False,
            },
        ),
    ]

    for test in find_tests:
        expected = test[3] if len(test) > 3 else True
        run_test(test[0], test[1], expected)

    # 5. 测试get_protein_data工具
    print("\n📊 测试 get_protein_data 工具")

    data_tests = [
        (
            "获取所有数据",
            {
                "jsonrpc": "2.0",
                "id": 20,
                "method": "tools/call",
                "params": {
                    "name": "get_protein_data_tool",
                    "arguments": {"pdb_id": "1A3N", "data_types": ["all"]},
                },
            },
        ),
        (
            "基本信息",
            {
                "jsonrpc": "2.0",
                "id": 21,
                "method": "tools/call",
                "params": {
                    "name": "get_protein_data_tool",
                    "arguments": {"pdb_id": "2HHB", "data_types": ["basic"]},
                },
            },
        ),
        (
            "序列信息",
            {
                "jsonrpc": "2.0",
                "id": 22,
                "method": "tools/call",
                "params": {
                    "name": "get_protein_data_tool",
                    "arguments": {"pdb_id": "1A3N", "data_types": ["sequence"]},
                },
            },
        ),
        (
            "无效PDB ID",
            {
                "jsonrpc": "2.0",
                "id": 23,
                "method": "tools/call",
                "params": {
                    "name": "get_protein_data_tool",
                    "arguments": {"pdb_id": "INVALID", "data_types": ["basic"]},
                },
                "expected_success": False,
            },
        ),
    ]

    for test in data_tests:
        expected = test[3] if len(test) > 3 else True
        run_test(test[0], test[1], expected)

    # 6. 测试download_structure工具
    print("\n💾 测试 download_structure 工具")

    download_tests = [
        (
            "PDB格式",
            {
                "jsonrpc": "2.0",
                "id": 30,
                "method": "tools/call",
                "params": {
                    "name": "download_structure_tool",
                    "arguments": {"pdb_id": "1A3N", "file_format": "pdb"},
                },
            },
        ),
        (
            "mmCIF格式",
            {
                "jsonrpc": "2.0",
                "id": 31,
                "method": "tools/call",
                "params": {
                    "name": "download_structure_tool",
                    "arguments": {"pdb_id": "2HHB", "file_format": "mmcif"},
                },
            },
        ),
        (
            "无效格式",
            {
                "jsonrpc": "2.0",
                "id": 32,
                "method": "tools/call",
                "params": {
                    "name": "download_structure_tool",
                    "arguments": {"pdb_id": "1A3N", "file_format": "invalid"},
                },
                "expected_success": False,
            },
        ),
    ]

    for test in download_tests:
        expected = test[3] if len(test) > 3 else True
        run_test(test[0], test[1], expected)

    # 7. 生成测试报告
    print("\n" + "=" * 60)
    print("📋 测试报告")
    print("=" * 60)

    success_rate = (passed_count / test_count * 100) if test_count > 0 else 0
    print(f"总测试数: {test_count}")
    print(f"通过: {passed_count}")
    print(f"失败: {test_count - passed_count}")
    print(f"成功率: {success_rate:.1f}%")

    if success_rate >= 80:
        print("\n🎉 综合测试通过！服务器功能正常。")
        return True
    else:
        print(f"\n⚠️ 测试成功率较低 ({success_rate:.1f}%)，需要检查失败项目。")
        return False


if __name__ == "__main__":
    success = test_comprehensive()
    exit(0 if success else 1)
