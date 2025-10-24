"""工具函数的单元测试"""

import os
import sys
from unittest.mock import patch

import pytest

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from protein_mcp.tools import (
    download_structure_file,
    get_amino_acid_sequence,
    get_protein_info,
    get_secondary_structure,
    list_supported_formats,
    validate_pdb_id_tool,
)
from protein_mcp.utils import validate_pdb_id


class TestValidatePdbId:
    """测试PDB ID验证功能"""

    def test_valid_pdb_ids(self):
        """测试有效的PDB ID"""
        valid_ids = ["1abc", "2DEF", "3xyz", "4ABC", "1234"]
        for pdb_id in valid_ids:
            assert validate_pdb_id(pdb_id) is True

    def test_invalid_pdb_ids(self):
        """测试无效的PDB ID"""
        # 根据PDB格式：4位字符，首位数字，后三位可数字可字母
        # "12ab" 实际上是有效的格式（数字+字母+字母）
        invalid_ids = ["abc", "123", "ABCDE", "ab12", ""]
        for pdb_id in invalid_ids:
            assert validate_pdb_id(pdb_id) is False

    def test_pdb_id_tool_valid(self):
        """测试PDB ID工具验证有效ID"""
        result = validate_pdb_id_tool("1abc")
        assert result["success"] is True
        assert result["data"]["is_valid"] is True
        assert result["data"]["pdb_id"] == "1abc"

    def test_pdb_id_tool_invalid(self):
        """测试PDB ID工具验证无效ID"""
        result = validate_pdb_id_tool("invalid")
        assert result["success"] is False
        assert "error" in result
        assert "context" in result
        assert "无效的PDB ID格式" in result["error"]


class TestListSupportedFormats:
    """测试支持格式列表功能"""

    def test_list_formats(self):
        """测试列出支持格式"""
        result = list_supported_formats()
        assert result["success"] is True
        assert "supported_formats" in result["data"]
        assert "total_count" in result["data"]
        assert result["data"]["total_count"] > 0


class TestGetProteinInfo:
    """测试蛋白质信息获取功能"""

    @patch("protein_mcp.tools.make_http_request")
    def test_get_protein_info_success(self, mock_http):
        """测试成功获取蛋白质信息"""
        # Mock成功的HTTP响应
        mock_response = {
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
        mock_http.return_value = mock_response

        result = get_protein_info("1abc")
        assert result["success"] is True
        assert result["data"]["pdb_id"] == "1ABC"
        assert result["data"]["entity_count"] == 1

    @patch("protein_mcp.tools.make_http_request")
    def test_get_protein_info_http_error(self, mock_http):
        """测试HTTP请求失败"""
        mock_http.return_value = None

        result = get_protein_info("1abc")
        assert result["success"] is False
        assert "RCSB API请求失败" in result["message"]

    @patch("protein_mcp.tools.make_http_request")
    def test_get_protein_info_invalid_response(self, mock_http):
        """测试无效响应"""
        mock_response = {"errors": [{"message": "Not found"}]}
        mock_http.return_value = mock_response

        result = get_protein_info("1abc")
        assert result["success"] is False
        assert "RCSB API请求失败" in result["message"]


class TestGetAminoAcidSequence:
    """测试氨基酸序列获取功能"""

    @patch("protein_mcp.tools.make_http_request")
    def test_get_sequence_success(self, mock_http):
        """测试成功获取氨基酸序列"""
        # Mock成功的GraphQL响应
        mock_response = {
            "data": {
                "polymer_entities": [
                    {
                        "rcsb_id": "1ABC",
                        "entity_polymer": {
                            "rcsb_polymer_entity": {
                                "sequence_1_letter": "ACDEFGHIKLMNPQRSTVWY",
                                "sequence_3_letter": "ALA CYS ASP GLU PHE GLY HIS ILE LYS LEU MET ASN PRO GLN ARG SER THR VAL TRP TYR",
                            },
                            "rcsb_polymer_entity_container_identifiers": {
                                "asym_ids": ["A"],
                                "auth_asym_ids": ["A"],
                                "entity_id": "1",
                            },
                        },
                    }
                ]
            }
        }
        mock_http.return_value = mock_response

        result = get_amino_acid_sequence("1abc")
        assert result["success"] is True
        assert result["data"]["pdb_id"] == "1ABC"
        assert result["data"]["sequence_1_letter"] == "ACDEFGHIKLMNPQRSTVWY"
        assert result["data"]["length"] == 20

    def test_get_sequence_invalid_pdb_id(self):
        """测试无效PDB ID"""
        result = get_amino_acid_sequence("invalid")
        assert result["success"] is False
        assert "无效的PDB ID格式" in result["message"]


class TestDownloadStructureFile:
    """测试结构文件下载功能"""

    @patch("protein_mcp.tools.download_file")
    @patch("os.path.exists")
    @patch("os.path.getsize")
    def test_download_success(self, mock_getsize, mock_exists, mock_download):
        """测试成功下载文件"""
        mock_download.return_value = True
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        result = download_structure_file("1abc", "pdb")
        assert result["success"] is True
        assert result["data"]["pdb_id"] == "1ABC"
        assert result["data"]["file_format"] == "pdb"
        assert result["data"]["status"] == "下载成功"

    def test_download_invalid_pdb_id(self):
        """测试下载时使用无效PDB ID"""
        result = download_structure_file("invalid", "pdb")
        assert result["success"] is False
        assert "无效的PDB ID格式" in result["message"]

    def test_download_invalid_format(self):
        """测试下载不支持的格式"""
        result = download_structure_file("1abc", "invalid")
        assert result["success"] is False
        assert "不支持的文件格式" in result["message"]


class TestGetSecondaryStructure:
    """测试二级结构获取功能"""

    @patch("protein_mcp.tools.get_amino_acid_sequence")
    @patch("protein_mcp.utils.calculate_dssp")
    def test_get_secondary_structure_success(self, mock_calculate, mock_get_seq):
        """测试成功计算二级结构"""
        # Mock氨基酸序列获取
        mock_get_seq.return_value = {
            "success": True,
            "data": {"sequence_1_letter": "ACDEFGHIKLMNPQRSTVWY"},
        }

        # Mock DSSP计算结果（使用真实计算结果）
        mock_calculate.return_value = "CCCECCHHHHHCCCHCCHCC"

        result = get_secondary_structure("1abc")
        assert result["success"] is True
        assert result["data"]["pdb_id"] == "1ABC"
        assert result["data"]["sequence_length"] == 20
        assert result["data"]["secondary_structure"] == "CCCECCHHHHHCCCHCCHCC"
        assert "statistics" in result["data"]

    @patch("protein_mcp.tools.get_amino_acid_sequence")
    def test_get_secondary_structure_seq_error(self, mock_get_seq):
        """测试获取氨基酸序列失败"""
        mock_get_seq.return_value = {"success": False, "message": "测试错误"}

        result = get_secondary_structure("1abc")
        assert result["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
