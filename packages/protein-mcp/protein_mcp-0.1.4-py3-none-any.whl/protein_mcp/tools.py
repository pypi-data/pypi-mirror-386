"""
优化后的3个核心蛋白质工具
从原来的8个工具优化为3个整合工具，减少复杂度，提升用户体验
"""

import json
from typing import Any

from .utils import (
    calculate_dssp,
    download_file,
    extract_sequence_from_pdb,
    format_error_response,
    format_success_response,
    get_supported_formats,
    make_http_request,
    validate_pdb_id,
)

RCSB_GRAPHQL_URL = "https://data.rcsb.org/graphql"
RCSB_REST_URL = "https://data.rcsb.org/rest/v1/core"
RCSB_SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
RCSB_DOWNLOAD_URL = "https://files.rcsb.org/download"


def _validate_pdb_exists(pdb_id: str) -> bool:
    """验证PDB ID是否存在于RCSB数据库"""
    try:
        url = f"{RCSB_REST_URL}/entry/{pdb_id}"
        response = make_http_request(url)
        return response is not None
    except Exception:
        return False


def _get_entry_info(pdb_id: str) -> dict[str, Any] | None:
    """获取PDB条目的基本信息"""
    try:
        url = f"{RCSB_REST_URL}/entry/{pdb_id}"
        return make_http_request(url)
    except Exception:
        return None


def _search_rcsb_structures(keywords: str, max_results: int = 10) -> list[dict[str, Any]]:
    """使用RCSB搜索API查找蛋白质结构"""
    try:
        search_query = {
            "query": {
                "type": "terminal",
                "service": "text",
                "parameters": {
                    "attribute": "struct.title",
                    "operator": "contains_words",
                    "value": keywords,
                },
            },
            "return_type": "entry",
            "request_options": {
                "return_all_hits": False,
                "paginate": {"start": 0, "rows": max_results},
                "sort": [
                    {"sort_by": "rcsb_accession_info.initial_release_date", "direction": "desc"}
                ],
            },
        }

        response = make_http_request(RCSB_SEARCH_URL, method="POST", data=json.dumps(search_query))

        if response and "result_set" in response:
            results = []
            for item in response["result_set"][:max_results]:
                results.append(
                    {
                        "pdb_id": item.get("identifier", ""),
                        "title": item.get("cite", {}).get("title", ""),
                        "score": item.get("score", 0.0),
                    }
                )
            return results

        return []
    except Exception as e:
        print(f"搜索错误: {str(e)}")
        return []


def find_protein_structures(
    keywords: str | None = None,
    category: str | None = None,
    pdb_id: str | None = None,
    max_results: int = 10,
) -> dict[str, Any]:
    """
    蛋白质结构发现工具 - 搜索、示例、验证的统一入口

    这是蛋白质研究的起点，帮助你发现和验证PDB结构。

    Args:
        keywords: 搜索关键词 (如: "hemoglobin", "kinase", "DNA")
        category: 预设类别 ("癌症靶点", "病毒蛋白", "酶类", "抗体", "膜蛋白", "核糖体")
        pdb_id: 直接验证或查看特定PDB ID (如: "1A3N")
        max_results: 搜索结果最大数量 (默认10，最大100)

    Returns:
        包含PDB结构列表、验证结果、示例数据的综合响应
    """
    try:
        # 限制max_results范围
        max_results = min(max(max_results, 1), 100)

        # 模式1: 验证特定PDB ID
        if pdb_id:
            if not validate_pdb_id(pdb_id):
                return format_error_response(
                    "无效的PDB ID格式",
                    f"期望格式: 4位字符 (首位数字，后三位可数字可字母)，实际: {pdb_id}",
                )

            if _validate_pdb_exists(pdb_id):
                entry_info = _get_entry_info(pdb_id)
                title = "未知标题"
                if entry_info and "struct" in entry_info:
                    title = entry_info["struct"].get("title", "未知标题")

                return format_success_response(
                    {
                        "mode": "validation",
                        "pdb_id": pdb_id,
                        "exists": True,
                        "title": title,
                        "validation_result": "PDB ID有效且存在于RCSB数据库中",
                    },
                    f"PDB ID {pdb_id} 验证成功，结构存在于RCSB数据库",
                )
            else:
                return format_error_response(
                    "PDB ID不存在", f"PDB ID {pdb_id} 在RCSB数据库中未找到"
                )

        # 模式2: 分类示例
        elif category:
            # 预定义的分类示例数据库
            category_examples = {
                "癌症靶点": {
                    "EGFR": ["1M14", "4MNF"],
                    "KRAS": ["4OBE", "6OIM"],
                    "p53": ["1TUP", "2OCJ"],
                    "BCR-ABL": ["1IEP", "1XBB"],
                },
                "病毒蛋白": {
                    "SARS-CoV-2刺突蛋白": ["6VSB", "6Y2E"],
                    "HIV蛋白酶": ["1HHP", "3PHV"],
                    "流感病毒血凝素": ["1RU7", "4WE8"],
                },
                "酶类": {
                    "溶菌酶": ["1HEW", "1LZ1"],
                    "DNA聚合酶": ["1KLN", "3K0M"],
                    "激酶": ["1ATP", "2SRC"],
                },
                "抗体": {"单克隆抗体": ["1HZH", "1IGT"], "抗体片段": ["1FVC", "3HFM"]},
                "膜蛋白": {"G蛋白偶联受体": ["1U19", "3DQB"], "离子通道": ["1BL8", "2A9W"]},
                "核糖体": {"核糖体亚基": ["1FJG", "2VQE"], "核糖体相关因子": ["1EF1", "2AW4"]},
            }

            if category not in category_examples:
                available_categories = list(category_examples.keys())
                return format_error_response(
                    "不支持的类别", f"可用类别: {', '.join(available_categories)}"
                )

            examples = category_examples[category]
            return format_success_response(
                {
                    "mode": "category_examples",
                    "category": category,
                    "examples": examples,
                    "total_proteins": len(examples),
                },
                f"获取 {category} 类别的蛋白质结构示例",
            )

        # 模式3: 关键词搜索
        elif keywords:
            results = _search_rcsb_structures(keywords, max_results)
            if results:
                return format_success_response(
                    {
                        "mode": "search",
                        "keywords": keywords,
                        "results": results,
                        "total_found": len(results),
                    },
                    f"找到 {len(results)} 个匹配的结构",
                )
            else:
                return format_error_response(
                    "未找到匹配结果", f"使用关键词 '{keywords}' 未找到匹配的PDB结构"
                )

        # 模式4: 默认 - 返回热门示例
        else:
            popular_examples = {
                "经典蛋白质": {
                    "血红蛋白": ["1A3N", "2HHB"],
                    "胰岛素": ["1ZNJ", "4INS"],
                    "溶菌酶": ["1HEW", "1LZ1"],
                    "DNA聚合酶": ["1KLN", "3K0M"],
                },
                "热门研究领域": {
                    "癌症研究": ["1M14", "4MNF", "1TUP"],
                    "病毒研究": ["6VSB", "6Y2E", "1HHP"],
                    "神经科学": ["2BEG", "5O3L", "1XQ8"],
                },
            }

            return format_success_response(
                {
                    "mode": "default_examples",
                    "popular_examples": popular_examples,
                    "total_categories": len(popular_examples),
                    "usage_tips": {
                        "search": "使用 keywords 参数搜索特定蛋白质",
                        "category": "使用 category 参数获取分类示例",
                        "validate": "使用 pdb_id 参数验证特定结构",
                    },
                },
                "提供热门蛋白质结构示例和使用指南",
            )

    except Exception as e:
        return format_error_response("工具执行错误", f"find_protein_structures 执行失败: {str(e)}")


def get_protein_data(
    pdb_id: str, data_types: list[str], chain_id: str | None = None
) -> dict[str, Any]:
    """
    蛋白质综合数据工具 - 获取完整蛋白质信息包

    这个工具是蛋白质数据获取的核心，一次性获取你需要的所有信息。

    Args:
        pdb_id: PDB ID (例如: "5G53")
        data_types: 需要的数据类型列表
            - "basic": 基本信息 (标题、方法、分辨率等)
            - "sequence": 氨基酸序列信息
            - "structure": 二级结构分析
            - "all": 获取所有数据
        chain_id: 特定链ID (例如: "A"，可选)

    Returns:
        完整的蛋白质数据包，包含请求的所有数据类型
    """
    try:
        if not validate_pdb_id(pdb_id):
            return format_error_response(
                "无效的PDB ID格式",
                f"期望格式: 4位字符 (首位数字，后三位可数字可字母)，实际: {pdb_id}",
            )

        # 处理 "all" 参数
        if "all" in data_types:
            data_types = ["basic", "sequence", "structure"]

        # 验证PDB ID存在性
        if not _validate_pdb_exists(pdb_id):
            return format_error_response("PDB ID不存在", f"PDB ID {pdb_id} 在RCSB数据库中未找到")

        result_data = {}

        # 获取基本信息
        if "basic" in data_types:
            entry_info = _get_entry_info(pdb_id)
            if entry_info:
                struct_data = entry_info.get("struct", {})
                result_data["basic"] = {
                    "pdb_id": pdb_id,
                    "title": struct_data.get("title", "未知标题"),
                    "method": struct_data.get("pdbx_descriptor", "未知方法"),
                    "resolution": struct_data.get("pdbx_resolution", None),
                    "deposition_date": struct_data.get("pdbx_deposit_date", "未知"),
                    "authors": [
                        author.get("name", "未知") for author in entry_info.get("audit_author", [])
                    ],
                }
            else:
                result_data["basic"] = {"error": "无法获取基本信息"}

        # 获取序列信息
        if "sequence" in data_types:
            try:
                # 下载PDB文件并提取序列
                pdb_url = f"{RCSB_DOWNLOAD_URL}/{pdb_id}.pdb"
                local_pdb_file = f"{pdb_id}.pdb"

                if download_file(pdb_url, local_pdb_file):
                    sequence_data = extract_sequence_from_pdb(local_pdb_file, chain_id)
                    if sequence_data:
                        result_data["sequence"] = {
                            "chain_id": sequence_data.get("chain_id", chain_id or "A"),
                            "sequence_1_letter": sequence_data.get("sequence_1_letter", ""),
                            "sequence_3_letter": sequence_data.get("sequence_3_letter", ""),
                            "length": sequence_data.get("length", 0),
                        }
                    else:
                        result_data["sequence"] = {"error": "无法提取序列信息"}
                else:
                    result_data["sequence"] = {"error": "PDB文件下载失败"}
            except Exception as e:
                result_data["sequence"] = {"error": f"序列提取失败: {str(e)}"}

        # 获取二级结构信息
        if "structure" in data_types:
            if "sequence" in result_data and "sequence_1_letter" in result_data["sequence"]:
                sequence = result_data["sequence"]["sequence_1_letter"]
                try:
                    secondary_structure = calculate_dssp(pdb_id, sequence)
                    result_data["structure"] = {
                        "dssp_prediction": secondary_structure,
                        "sequence_length": len(sequence),
                        "composition": {
                            "helix": secondary_structure.count("H"),
                            "strand": secondary_structure.count("E"),
                            "coil": secondary_structure.count("C"),
                        },
                    }
                except Exception as e:
                    result_data["structure"] = {"error": f"二级结构分析失败: {str(e)}"}
            else:
                result_data["structure"] = {"error": "需要先获取序列信息"}

        # 计算成功率
        successful_types = [
            dt for dt in data_types if dt in result_data and "error" not in result_data[dt]
        ]
        success_rate = len(successful_types) / len(data_types) * 100 if data_types else 0

        return format_success_response(
            {
                "pdb_id": pdb_id,
                "requested_data_types": data_types,
                "data": result_data,
                "success_rate": success_rate,
                "chain_id": chain_id,
            },
            f"成功获取 {pdb_id} 的数据: {', '.join(successful_types)} ({success_rate:.0f}%)",
        )

    except Exception as e:
        return format_error_response("数据获取错误", f"get_protein_data 执行失败: {str(e)}")


def download_structure(
    pdb_id: str, file_format: str = "pdb", save_local: bool = False
) -> dict[str, Any]:
    """
    结构文件工具 - 下载和管理蛋白质结构文件

    这个工具处理所有文件相关的操作，从下载到格式说明。

    Args:
        pdb_id: PDB ID (例如: "5G53")
        file_format: 文件格式
            - "pdb": 标准PDB格式 (推荐，人类可读)
            - "mmcif": 大分子晶体信息文件格式 (现代标准)
            - "cif": 晶体信息文件格式
            - "mmtf": 大分子传输格式 (二进制，速度快)
        save_local: 是否保存到本地文件 (默认False返回内容)

    Returns:
        文件内容或下载信息 + 格式说明和使用指南
    """
    try:
        if not validate_pdb_id(pdb_id):
            return format_error_response(
                "无效的PDB ID格式",
                f"期望格式: 4位字符 (首位数字，后三位可数字可字母)，实际: {pdb_id}",
            )

        # 验证PDB ID存在性
        if not _validate_pdb_exists(pdb_id):
            return format_error_response("PDB ID不存在", f"PDB ID {pdb_id} 在RCSB数据库中未找到")

        # 验证文件格式
        supported_formats = get_supported_formats()
        if file_format not in supported_formats:
            return format_error_response(
                "不支持的文件格式", f"支持格式: {', '.join(supported_formats)}"
            )

        # 构建下载URL
        download_url = f"{RCSB_DOWNLOAD_URL}/{pdb_id}.{file_format}"
        local_filename = f"{pdb_id}.{file_format}"

        # 下载文件
        if save_local:
            success = download_file(download_url, local_filename)
            if success:
                result_data = {
                    "pdb_id": pdb_id,
                    "file_format": file_format,
                    "file_path": local_filename,
                    "download_method": "saved_local",
                    "file_size": None,  # 可以添加文件大小信息
                }
            else:
                return format_error_response(
                    "文件下载失败", f"无法下载 {pdb_id}.{file_format} 文件"
                )
        else:
            # 返回文件内容（对于小文件）
            try:
                import requests

                response = requests.get(download_url, timeout=30)
                if response.status_code == 200:
                    result_data = {
                        "pdb_id": pdb_id,
                        "file_format": file_format,
                        "file_path": download_url,
                        "download_method": "url_provided",
                        "file_content": (
                            response.text[:1000] + "..."
                            if len(response.text) > 1000
                            else response.text
                        ),
                        "content_preview": True,
                    }
                else:
                    return format_error_response(
                        "文件下载失败", f"HTTP {response.status_code}: 无法访问文件"
                    )
            except Exception as e:
                return format_error_response("网络错误", f"下载失败: {str(e)}")

        # 添加格式信息
        format_info = {
            "pdb": {
                "name": "Protein Data Bank (PDB) 格式",
                "description": "经典的文本格式，人类可读",
                "recommended": True,
                "use_case": "一般用途，化学演示，小分子结构",
                "advantages": ["人类可读", "广泛支持", "适合编辑"],
            },
            "mmcif": {
                "name": "大分子晶体信息文件格式",
                "description": "现代的XML风格格式，更灵活",
                "recommended": True,
                "use_case": "复杂结构，大批量数据，现代软件",
                "advantages": ["更详细", "支持复杂数据", "现代标准"],
            },
            "cif": {
                "name": "晶体信息文件格式",
                "description": "标准化格式， mmcif的简化版",
                "recommended": False,
                "use_case": "基本晶体学数据",
                "advantages": ["标准化", "简洁"],
            },
            "mmtf": {
                "name": "大分子传输格式",
                "description": "二进制格式，压缩高效",
                "recommended": True,
                "use_case": "大批量传输，高性能应用",
                "advantages": ["文件小", "加载快", "压缩效率高"],
            },
        }

        result_data["format_info"] = format_info.get(
            file_format,
            {
                "name": f"{file_format.upper()} 格式",
                "description": "支持的文件格式",
                "recommended": False,
                "use_case": "通用格式",
                "advantages": ["标准支持"],
            },
        )

        return format_success_response(
            result_data,
            f"成功获取 {pdb_id} 的 {file_format} 格式文件。{format_info.get(file_format, {}).get('description', '')}",
        )

    except Exception as e:
        return format_error_response("文件操作错误", f"download_structure 执行失败: {str(e)}")


def register_all_tools(mcp) -> None:
    """
    注册3个核心整合工具到FastMCP服务器

    优化后的工具设计：
    1. find_protein_structures - 蛋白质结构发现工具
    2. get_protein_data - 蛋白质综合数据工具
    3. download_structure - 结构文件工具

    Args:
        mcp: FastMCP服务器实例
    """

    # 工具1: 蛋白质结构发现工具 - 整合搜索、示例、验证功能
    @mcp.tool()
    def find_protein_structures_tool(
        keywords: str | None = None,
        category: str | None = None,
        pdb_id: str | None = None,
        max_results: int = 10,
    ) -> dict[str, Any]:
        """
        蛋白质结构发现工具 - 搜索、示例、验证的统一入口

        这是蛋白质研究的起点，帮助你发现和验证PDB结构。

        Args:
            keywords: 搜索关键词 (如: "hemoglobin", "kinase", "DNA")
            category: 预设类别 ("癌症靶点", "病毒蛋白", "酶类", "抗体", "膜蛋白", "核糖体")
            pdb_id: 直接验证或查看特定PDB ID (如: "1A3N")
            max_results: 搜索结果最大数量 (默认10，最大100)

        Returns:
            包含PDB结构列表、验证结果、示例数据的综合响应

        Examples:
            # 搜索血红蛋白相关结构
            find_protein_structures(keywords="hemoglobin")

            # 获取癌症靶点示例
            find_protein_structures(category="癌症靶点")

            # 验证PDB ID
            find_protein_structures(pdb_id="1A3N")
        """
        return find_protein_structures(keywords, category, pdb_id, max_results)

    # 工具2: 蛋白质综合数据工具 - 一次获取所有蛋白质信息
    @mcp.tool()
    def get_protein_data_tool(
        pdb_id: str,
        data_types: list[str] | None = None,
        chain_id: str | None = None,
    ) -> dict[str, Any]:
        """
        蛋白质综合数据工具 - 获取完整蛋白质信息包

        这个工具是蛋白质数据获取的核心，一次性获取你需要的所有信息。

        Args:
            pdb_id: PDB ID (例如: "5G53")
            data_types: 需要的数据类型列表
                - "basic": 基本信息 (标题、方法、分辨率等)
                - "sequence": 氨基酸序列信息
                - "structure": 二级结构分析
                - "all": 获取所有数据
            chain_id: 特定链ID (例如: "A"，可选)

        Returns:
            完整的蛋白质数据包，包含请求的所有数据类型

        Examples:
            # 获取所有数据
            get_protein_data("5G53", ["all"])

            # 只获取基本信息和序列
            get_protein_data("1A3N", ["basic", "sequence"])

            # 获取特定链的数据
            get_protein_data("2HHB", ["all"], "A")
        """
        # 如果没有指定数据类型，默认获取基本数据
        if data_types is None:
            data_types = ["basic", "sequence", "structure"]
        return get_protein_data(pdb_id, data_types, chain_id)

    # 工具3: 结构文件工具 - 下载和管理蛋白质结构文件
    @mcp.tool()
    def download_structure_tool(
        pdb_id: str, file_format: str = "pdb", save_local: bool = False
    ) -> dict[str, Any]:
        """
        结构文件工具 - 下载和管理蛋白质结构文件

        这个工具处理所有文件相关的操作，从下载到格式说明。

        Args:
            pdb_id: PDB ID (例如: "5G53")
            file_format: 文件格式
                - "pdb": 标准PDB格式 (推荐，人类可读)
                - "mmcif": 大分子晶体信息文件格式 (现代标准)
                - "cif": 晶体信息文件格式
                - "mmtf": 大分子传输格式 (二进制，速度快)
            save_local: 是否保存到本地文件 (默认False返回内容)

        Returns:
            文件内容或下载信息 + 格式说明和使用指南

        Examples:
            # 获取PDB文件内容
            download_structure("1A3N")

            # 下载mmCIF格式并保存到本地
            download_structure("2HHB", "mmcif", True)

            # 获取快速MMTF格式
            download_structure("6VSB", "mmtf")
        """
        return download_structure(pdb_id, file_format, save_local)
