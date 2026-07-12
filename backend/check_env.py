"""
环境检查脚本 - 验证 Phase 2 运行环境
"""

import os
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings


def check_environment():
    """检查运行环境"""
    print("="*60)
    print("SignalPilot Phase 2 环境检查")
    print("="*60)

    issues = []
    warnings = []

    # 1. 检查 API Key
    print("\n[1] 检查 Anthropic API Key...")
    if settings.anthropic_api_key:
        # 只显示前10个字符
        masked_key = settings.anthropic_api_key[:10] + "..." if len(settings.anthropic_api_key) > 10 else "***"
        print(f"    ✓ API Key 已配置: {masked_key}")

        # 测试 API 连接
        print("    测试 API 连接...")
        try:
            from anthropic import Anthropic
            client = Anthropic(
                api_key=settings.anthropic_api_key,
                base_url=settings.ANTHROPIC_BASE_URL
            )
            # 简单的测试调用
            response = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            print("    ✓ API 连接成功！")
        except Exception as e:
            error_msg = str(e)
            if "Connection" in error_msg or "timeout" in error_msg.lower():
                issues.append("API 网络连接失败")
                print(f"    ✗ API 连接失败: {error_msg}")
                print("    建议:")
                print("      - 检查网络连接")
                print("      - 检查代理设置")
                print("      - 访问 https://console.anthropic.com 测试")
            elif "invalid" in error_msg.lower() or "401" in error_msg:
                issues.append("API Key 无效")
                print(f"    ✗ API Key 无效: {error_msg}")
                print("    建议:")
                print("      - 访问 https://console.anthropic.com/settings/keys")
                print("      - 生成新的 API Key")
                print("      - 重新设置环境变量")
            else:
                warnings.append(f"API 测试警告: {error_msg}")
                print(f"    ⚠ API 测试警告: {error_msg}")
    else:
        warnings.append("API Key 未配置，将使用 fallback 模式")
        print("    ⚠ ANTHROPIC_API_KEY 未配置")
        print("    系统将使用 fallback 模式（关键词匹配）")
        print("    设置方法:")
        print("      Windows: $env:ANTHROPIC_API_KEY='sk-ant-...'")
        print("      Linux/Mac: export ANTHROPIC_API_KEY='sk-ant-...'")

    # 2. 检查数据库文件
    print("\n[2] 检查数据库文件...")
    project_root = Path(__file__).parent.parent
    db_path = project_root / settings.database_path
    print(f"    路径: {db_path}")

    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"    ✓ 数据库文件存在 ({size_mb:.2f} MB)")

        # 测试数据库连接
        print("    测试数据库连接...")
        try:
            from app.adapters.database import DuckDBAdapter
            adapter = DuckDBAdapter(str(db_path), read_only=True)
            tables = adapter._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            print(f"    ✓ 数据库连接成功，找到 {len(tables)} 个表")
            adapter.close()
        except Exception as e:
            issues.append(f"数据库连接失败: {e}")
            print(f"    ✗ 数据库连接失败: {e}")
    else:
        issues.append("数据库文件不存在")
        print(f"    ✗ 数据库文件不存在")
        print("    生成数据库:")
        print(f"      cd {project_root.parent / 'data'}")
        print("      python generate_data.py")

    # 3. 检查依赖
    print("\n[3] 检查依赖...")
    required_packages = [
        ("langgraph", "0.2.34"),
        ("langchain_core", "0.3.15"),
        ("anthropic", None),
    ]

    for package, min_version in required_packages:
        try:
            import importlib
            module = importlib.import_module(package.replace("-", "_"))
            version = getattr(module, "__version__", "unknown")
            print(f"    ✓ {package}: {version}")
        except ImportError:
            issues.append(f"缺少依赖: {package}")
            print(f"    ✗ {package}: 未安装")

    # 4. 检查配置
    print("\n[4] 检查配置...")
    print(f"    数据库路径: {settings.database_path}")
    print(f"    默认 LLM: {settings.default_llm}")
    print(f"    API Host: {settings.api_host}:{settings.api_port}")

    # 总结
    print("\n" + "="*60)
    print("检查结果")
    print("="*60)

    if not issues and not warnings:
        print("\n✓ 环境检查通过！所有组件正常。")
        print("\n可以开始测试:")
        print("  python test_phase2.py")
        return True
    else:
        if issues:
            print(f"\n✗ 发现 {len(issues)} 个问题:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")

        if warnings:
            print(f"\n⚠ {len(warnings)} 个警告:")
            for i, warning in enumerate(warnings, 1):
                print(f"  {i}. {warning}")

        print("\n请先解决上述问题再继续。")
        return False


if __name__ == "__main__":
    success = check_environment()
    sys.exit(0 if success else 1)
