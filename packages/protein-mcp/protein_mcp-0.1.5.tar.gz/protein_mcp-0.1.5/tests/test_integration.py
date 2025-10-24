"""集成测试和端到端测试"""

import asyncio
import os
import sys
from unittest.mock import patch

import pytest

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


from protein_mcp.server import create_server


class TestServerIntegration:
    """服务器集成测试"""

    def test_server_creation_with_tools(self):
        """测试服务器创建并注册所有工具"""
        server = create_server()
        assert server is not None
        assert hasattr(server, "name")
        assert server.name == "protein-mcp"
        assert hasattr(server, "version")
        assert server.version == "1.0.0"

        # 检查工具是否正确注册（get_tools() 返回协程，需要 await）
        async def get_tools_list():
            tools = await server.get_tools()
            return [tool.name for tool in tools]

        tool_names = asyncio.run(get_tools_list())
        expected_tools = [
            "get_amino_acid_sequence",
            "get_secondary_structure",
            "download_structure_file",
            "get_protein_info",
            "validate_pdb_id_tool",
            "list_supported_formats",
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    def test_server_tool_execution(self):
        """测试服务器工具执行"""
        server = create_server()

        # 获取工具
        async def get_tools_dict():
            tools = await server.get_tools()
            return {tool.name: tool for tool in tools}

        tools = asyncio.run(get_tools_dict())

        # 测试PDB ID验证工具
        validate_tool = tools.get("validate_pdb_id_tool")
        assert validate_tool is not None

        # 执行工具（这应该通过FastMCP的执行机制）
        # 这里我们只是验证工具存在且可调用

    def test_full_server_functionality(self):
        """测试完整服务器功能"""
        server = create_server("test-server", "1.0.0-test")

        # 验证服务器配置
        assert server.name == "test-server"
        assert server.version == "1.0.0-test"

        # 验证工具数量
        async def get_tools_count():
            tools = await server.get_tools()
            return tools

        tools = asyncio.run(get_tools_count())
        assert len(tools) == 6  # 6个工具


class TestDataFlow:
    """数据流测试"""

    @patch("protein_mcp.utils.make_http_request")
    @patch("protein_mcp.utils.calculate_dssp")
    def test_protein_info_to_sequence_flow(self, mock_calculate, mock_http_request):
        """测试从蛋白质信息到序列的数据流"""
        # Mock蛋白质信息响应
        mock_http_request.return_value = {
            "data": {
                "polymer_entities": [
                    {
                        "rcsb_id": "1ABC",
                        "entity_polymer": {
                            "rcsb_entity_source_organism": {
                                "ncbi_taxonomy_id": 9606,
                                "scientific_name": "Homo sapiens",
                            },
                            "rcsb_polymer_entity": {
                                "pdbx_seq_one_letter_code": "ACDEFGHIKLMNPQRSTVWY",
                                "pdbx_seq_three_letter_code": "ALA CYS ASP GLU PHE GLY HIS ILE LYS LEU MET ASN PRO GLN ARG SER THR VAL TRP TYR",
                            },
                            "rcsb_polymer_entity_container_identifiers": {
                                "entity_id": "1",
                                "asym_ids": ["A"],
                                "auth_asym_ids": ["A"],
                            },
                        },
                    }
                ]
            }
        }

        # Mock DSSP计算
        mock_calculate.return_value = "HHHHEEEEECCCCCHHHHCCCC"

        # 测试get_protein_info
        from protein_mcp.tools import get_protein_info

        protein_result = get_protein_info("1abc")
        assert protein_result["success"]
        assert protein_result["data"]["pdb_id"] == "1ABC"

        # 测试get_amino_acid_sequence
        from protein_mcp.tools import get_amino_acid_sequence

        sequence_result = get_amino_acid_sequence("1abc")
        assert sequence_result["success"]
        assert sequence_result["data"]["sequence_1_letter"] == "ACDEFGHIKLMNPQRSTVWY"

        # 测试get_secondary_structure
        from protein_mcp.tools import get_secondary_structure

        structure_result = get_secondary_structure("1abc")
        assert structure_result["success"]
        assert structure_result["data"]["secondary_structure"] == "HHHHEEEEECCCCCHHHHCCCC"


class TestErrorHandling:
    """错误处理测试"""

    def test_server_robustness(self):
        """测试服务器的健壮性"""
        # 创建多个服务器实例
        servers = []
        for i in range(3):
            server = create_server(f"server-{i}", f"1.0.{i}")
            servers.append(server)

        # 定义在循环外部的辅助函数
        async def get_tools_count(test_server):
            tools = await test_server.get_tools()
            return tools

        # 验证所有服务器都正常创建
        for i, server in enumerate(servers):
            assert server.name == f"server-{i}"
            assert server.version == f"1.0.{i}"

            tools = asyncio.run(get_tools_count(server))
            assert len(tools) == 6

    def test_tool_registration_consistency(self):
        """测试工具注册的一致性"""
        server1 = create_server("test1", "1.0.0")
        server2 = create_server("test2", "1.0.0")

        async def get_tools_dict(server):
            tools = await server.get_tools()
            return {tool.name: tool for tool in tools}

        tools1 = asyncio.run(get_tools_dict(server1))
        tools2 = asyncio.run(get_tools_dict(server2))

        # 验证两个服务器有相同的工具
        assert set(tools1.keys()) == set(tools2.keys())

        # 验证工具功能相同
        for tool_name in tools1.keys():
            tool1 = tools1[tool_name]
            tool2 = tools2[tool_name]
            assert tool1.name == tool2.name
            assert tool1.description == tool2.description


if __name__ == "__main__":
    # 运行所有集成测试
    pytest.main([__file__, "-v", "--tb=short"])
