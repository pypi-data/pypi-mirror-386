"""基本测试"""

import os
import sys

# 添加protein_mcp包到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from protein_mcp.server import create_server


def test_server_creation():
    """测试服务器创建"""
    print("🧪 测试服务器创建...")
    try:
        server = create_server()
        print("✅ 服务器创建成功!")
        print(f"📋 服务器名称: {server.name}")
        print(f"📦 版本: {server.version}")
        assert server is not None
    except Exception as e:
        print(f"❌ 服务器创建失败: {str(e)}")
        raise


def test_main_function():
    """测试主函数"""
    print("\n🧪 测试主函数...")
    try:
        import protein_mcp

        # 检查main函数是否存在
        assert hasattr(protein_mcp, "main")

        print("✅ 主函数导入成功!")
    except (ImportError, AssertionError) as e:
        print(f"❌ 主函数导入失败: {str(e)}")
        raise


if __name__ == "__main__":
    print("🧬 Protein MCP Server 基本测试")
    print("=" * 50)

    success = True
    success &= test_server_creation()
    success &= test_main_function()

    if success:
        print("🎉 所有测试通过!")
        print("\n📦 项目状态:")
        print("   ✅ 包结构正确")
        print("   ✅ 服务器创建正常")
        print("   ✅ 主函数可用")
        print("\n🚀 可以安全启动服务器:")
        print("   python -m protein_mcp.server")
    else:
        print("❌ 部分测试失败!")
