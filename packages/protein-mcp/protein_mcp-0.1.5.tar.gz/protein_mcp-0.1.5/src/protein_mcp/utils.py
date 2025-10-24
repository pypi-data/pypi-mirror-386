"""工具函数和配置"""

import re
import urllib.parse
import urllib.request
from typing import Any

import requests

# 配置
RCSB_GRAPHQL_URL = "https://data.rcsb.org/graphql"
RCSB_DOWNLOAD_URL = "https://files.rcsb.org/download"


def make_http_request(
    url: str,
    method: str = "GET",
    data: str | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    """
    发送HTTP请求，支持POST/GET方法

    Args:
        url: 请求URL
        method: HTTP方法 ("GET" 或 "POST")
        data: 请求数据 (POST请求时使用)
        headers: 请求头

    Returns:
        JSON响应数据或None (失败时)
    """
    try:
        if method == "POST":
            response = requests.post(
                url, data=data, headers=headers or {"Content-Type": "application/json"}, timeout=30
            )
        else:
            response = requests.get(url, headers=headers or {}, timeout=30)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"HTTP请求失败: {response.status_code}")
            return None

    except Exception as e:
        print(f"网络请求错误: {str(e)}")
        return None


def validate_pdb_id(pdb_id: str) -> bool:
    """
    验证PDB ID格式

    Args:
        pdb_id: PDB ID (例如: "5G53")

    Returns:
        True如果格式正确，否则False
    """
    if not pdb_id or not isinstance(pdb_id, str):
        return False

    # PDB ID格式: 4位字符，首位数字，后三位可数字可字母
    pattern = r"^[0-9][A-Za-z0-9]{3}$"
    return bool(re.match(pattern, pdb_id.strip().upper()))


def build_rcsb_query(
    entity_type: str = "polymer_entity", return_type: str = "polymer_entities"
) -> str:
    """
    构建RCSB GraphQL查询

    Args:
        entity_type: 查询的实体类型
        return_type: 返回类型

    Returns:
        GraphQL查询字符串
    """
    query = f"""
    query getStructure($rcsb_id: String!) {{
        {return_type}(rcsb_id: $rcsb_id) {{
            rcsb_id
            entity {{
                {{
                    type
                    polymer {{
                        {{rcsb_entity_source_organism}}
                        {{rcsb_entity_container_identifiers}}
                        {{rcsb_polymer_entity}}
                        {{rcsb_polymer_entity_container_identifiers}}
                    }}
                }}
            }}
            rcsb_entry_info {{
                {{resolution_combined}}
                {{experimental_method}}
            }}
        }}
    }}
    """
    return query.strip()


def extract_sequence_info(data: dict[str, Any], chain_id: str | None = None) -> dict[str, Any]:
    """
    从RCSB响应中提取序列信息

    Args:
        data: RCSB API响应数据
        chain_id: 链ID (可选)

    Returns:
        包含序列信息的字典
    """
    try:
        entities = data.get("polymer_entities", [])
        if not entities:
            return {}

        # 如果指定了链ID，尝试找到对应的实体
        if chain_id:
            for entity in entities:
                entity_id = entity.get("rcsb_id", "")
                if chain_id in entity_id:
                    return entity

        # 否则返回第一个实体
        return entities[0] if entities else {}

    except Exception as e:
        print(f"提取序列信息失败: {str(e)}")
        return {}


def calculate_dssp(pdb_id: str, sequence: str) -> str:
    """
    简化的DSSP二级结构计算 (示例实现)

    Args:
        pdb_id: PDB ID
        sequence: 氨基酸序列

    Returns:
        SS8格式二级结构字符串
    """
    try:
        # 这里是简化的实现，实际应该使用真正的DSSP算法
        # 例如使用BioPython的DSSP模块

        # 简单的二级结构预测规则
        structure_map = {
            "A": "C",  # Alanine - Coil
            "R": "H",  # Arginine - Helix
            "N": "C",  # Asparagine - Coil
            "D": "C",  # Aspartic acid - Coil
            "C": "C",  # Cysteine - Coil
            "E": "E",  # Glutamic acid - Strand
            "Q": "C",  # Glutamine - Coil
            "G": "C",  # Glycine - Coil
            "H": "H",  # Histidine - Helix
            "I": "H",  # Isoleucine - Helix
            "L": "H",  # Leucine - Helix
            "K": "H",  # Lysine - Helix
            "M": "H",  # Methionine - Helix
            "F": "C",  # Phenylalanine - Coil
            "P": "C",  # Proline - Coil
            "S": "C",  # Serine - Coil
            "T": "C",  # Threonine - Coil
            "W": "C",  # Tryptophan - Coil
            "Y": "C",  # Tyrosine - Coil
            "V": "H",  # Valine - Helix
        }

        # 构建二级结构序列
        ss_sequence = []
        for aa in sequence.upper():
            ss_sequence.append(structure_map.get(aa, "C"))

        # 简单的二级结构校正，确保合理的长度
        if len(ss_sequence) > len(sequence):
            ss_sequence = ss_sequence[: len(sequence)]
        elif len(ss_sequence) < len(sequence):
            ss_sequence.extend(["C"] * (len(sequence) - len(ss_sequence)))

        return "".join(ss_sequence)

    except Exception as e:
        print(f"DSSP计算失败: {str(e)}")
        return "C" * len(sequence)  # 返回全卷曲作为默认值


def download_file(url: str, local_path: str) -> bool:
    """
    下载文件到本地

    Args:
        url: 文件URL
        local_path: 本地保存路径

    Returns:
        True如果下载成功，否则False
    """
    try:
        urllib.request.urlretrieve(url, local_path)
        return True
    except Exception as e:
        print(f"文件下载失败: {str(e)}")
        return False


def get_supported_formats() -> list[str]:
    """获取支持的文件格式列表"""
    return ["pdb", "mmcif", "cif", "pdbx", "mmtf", "bcif"]


def extract_sequence_from_pdb(pdb_file: str, chain_id: str | None = None) -> dict[str, Any] | None:
    """
    从PDB文件中提取氨基酸序列

    Args:
        pdb_file: PDB文件路径
        chain_id: 链ID (可选，如果不指定则提取第一条链)

    Returns:
        包含序列信息的字典，如果失败返回None
    """
    try:
        sequences = {}
        current_chain = None
        current_sequence = []
        current_asym_ids = []
        current_auth_asym_ids = []

        with open(pdb_file) as f:
            for line in f:
                if line.startswith("ATOM") or line.startswith("HETATM"):
                    # PDB格式: columns 13-16 = residue name, 17 = chain, 18-20 = residue number
                    residue_name = line[17:20].strip()
                    chain = line[21:22].strip()

                    # 只处理标准氨基酸
                    if residue_name in [
                        "ALA",
                        "ARG",
                        "ASN",
                        "ASP",
                        "CYS",
                        "GLN",
                        "GLU",
                        "GLY",
                        "HIS",
                        "ILE",
                        "LEU",
                        "LYS",
                        "MET",
                        "PHE",
                        "PRO",
                        "SER",
                        "THR",
                        "TRP",
                        "TYR",
                        "VAL",
                    ]:
                        if current_chain != chain:
                            # 保存前一个链的序列
                            if current_chain and current_sequence:
                                sequences[current_chain] = {
                                    "sequence_1_letter": "".join(current_sequence),
                                    "sequence_3_letter": " ".join(current_sequence),
                                    "length": len(current_sequence),
                                    "asym_ids": current_asym_ids,
                                    "auth_asym_ids": current_auth_asym_ids,
                                }

                            # 开始新链
                            current_chain = chain
                            current_sequence = []
                            current_asym_ids = [chain]
                            current_auth_asym_ids = [chain]

                        # 添加氨基酸到当前序列
                        if not current_sequence or current_sequence[-1] != residue_name:
                            current_sequence.append(residue_name)

                elif line.startswith("TER"):
                    # 链结束标志
                    if current_chain and current_sequence:
                        sequences[current_chain] = {
                            "sequence_1_letter": "".join(current_sequence),
                            "sequence_3_letter": " ".join(current_sequence),
                            "length": len(current_sequence),
                            "asym_ids": current_asym_ids,
                            "auth_asym_ids": current_auth_asym_ids,
                        }
                        current_chain = None
                        current_sequence = []

        # 保存最后一个链
        if current_chain and current_sequence:
            sequences[current_chain] = {
                "sequence_1_letter": "".join(current_sequence),
                "sequence_3_letter": " ".join(current_sequence),
                "length": len(current_sequence),
                "asym_ids": current_asym_ids,
                "auth_asym_ids": current_auth_asym_ids,
            }

        if not sequences:
            return None

        # 转换3字母到1字母氨基酸代码
        aa_map = {
            "ALA": "A",
            "ARG": "R",
            "ASN": "N",
            "ASP": "D",
            "CYS": "C",
            "GLN": "Q",
            "GLU": "E",
            "GLY": "G",
            "HIS": "H",
            "ILE": "I",
            "LEU": "L",
            "LYS": "K",
            "MET": "M",
            "PHE": "F",
            "PRO": "P",
            "SER": "S",
            "THR": "T",
            "TRP": "W",
            "TYR": "Y",
            "VAL": "V",
        }

        for chain_id in sequences:
            seq_3_letter = sequences[chain_id]["sequence_3_letter"].split()
            seq_1_letter = "".join([aa_map.get(aa, "X") for aa in seq_3_letter])
            sequences[chain_id]["sequence_1_letter"] = seq_1_letter

        # 选择目标链
        if chain_id:
            target_chain = chain_id
        else:
            target_chain = list(sequences.keys())[0]  # 选择第一条链

        if target_chain not in sequences:
            return None

        sequence_data = sequences[target_chain]
        sequence_data["chain_id"] = target_chain
        sequence_data["entity_id"] = "1"  # 默认实体ID

        return sequence_data

    except Exception as e:
        print(f"从PDB文件提取序列失败: {str(e)}")
        return None


def format_error_response(error_msg: str, context: str = "") -> dict[str, Any]:
    """
    格式化错误响应

    Args:
        error_msg: 错误消息
        context: 错误上下文

    Returns:
        标准化的错误响应，包含 success、message、error 和 context 字段
    """
    response = {
        "success": False,
        "message": error_msg,  # 为了兼容测试，同时提供 message 字段
        "error": error_msg,
        "context": context,
    }

    return response


def format_success_response(data: Any, message: str = "操作成功") -> dict[str, Any]:
    """
    格式化成功响应

    Args:
        data: 响应数据
        message: 成功消息

    Returns:
        标准化的成功响应
    """
    response = {"success": True, "message": message, "data": data}

    return response
