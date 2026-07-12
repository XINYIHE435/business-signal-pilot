"""
快速设置第三方 API 代理
"""

import os
import sys


def setup_api_proxy():
    """设置第三方 API 代理"""
    print("="*60)
    print("SignalPilot - 第三方 API 代理设置")
    print("="*60)

    print("\n当前使用的代理服务: https://cn.zhihuiai.top/")
    print("（可在 app/core/config.py 中修改 ANTHROPIC_BASE_URL）")

    # 检查是否已设置 API Key
    current_key = os.getenv("ANTHROPIC_API_KEY")

    if current_key:
        masked_key = current_key[:10] + "..." if len(current_key) > 10 else "***"
        print(f"\n✓ 检测到已设置的 API Key: {masked_key}")

        choice = input("\n是否要更新 API Key? (y/N): ").strip().lower()
        if choice != 'y':
            print("\n保持现有配置。")
            return test_connection(current_key)
    else:
        print("\n⚠ 未检测到 ANTHROPIC_API_KEY 环境变量")

    # 提示输入 API Key
    print("\n请输入您的 API Key:")
    print("（从 https://cn.zhihuiai.top/ 获取）")
    api_key = input("API Key: ").strip()

    if not api_key:
        print("\n✗ API Key 不能为空")
        return False

    # 设置环境变量（仅当前会话）
    os.environ["ANTHROPIC_API_KEY"] = api_key
    print(f"\n✓ API Key 已设置: {api_key[:10]}...")

    # 提示如何永久设置
    print("\n要永久保存，请在终端执行:")
    if sys.platform == "win32":
        print(f'  $env:ANTHROPIC_API_KEY="{api_key}"')
    else:
        print(f'  export ANTHROPIC_API_KEY="{api_key}"')

    # 测试连接
    return test_connection(api_key)


def test_connection(api_key):
    """测试 API 连接"""
    print("\n" + "="*60)
    print("测试 API 连接")
    print("="*60)

    try:
        from anthropic import Anthropic
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from app.core.config import settings

        print(f"\n代理地址: {settings.ANTHROPIC_BASE_URL}")
        print("正在连接...")

        client = Anthropic(
            api_key=api_key,
            base_url=settings.ANTHROPIC_BASE_URL
        )

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=10,
            messages=[{"role": "user", "content": "test"}]
        )

        print("\n✓ API 连接成功！")
        print(f"响应: {response.content[0].text}")

        print("\n" + "="*60)
        print("设置完成！")
        print("="*60)
        print("\n下一步:")
        print("  1. python check_env.py  # 完整环境检查")
        print("  2. python test_phase2.py  # 运行测试")

        return True

    except Exception as e:
        error_msg = str(e)
        print(f"\n✗ API 连接失败: {error_msg}")

        if "Connection" in error_msg or "timeout" in error_msg.lower():
            print("\n可能的原因:")
            print("  - 网络连接问题")
            print("  - 代理地址不正确")
            print("  - 防火墙阻止")
        elif "invalid" in error_msg.lower() or "401" in error_msg:
            print("\n可能的原因:")
            print("  - API Key 无效")
            print("  - 账户余额不足")
            print("  - API Key 已过期")

        print("\n建议:")
        print("  1. 访问 https://cn.zhihuiai.top/ 检查 API Key")
        print("  2. 确认账户状态正常")
        print("  3. 尝试重新生成 API Key")

        return False


if __name__ == "__main__":
    success = setup_api_proxy()
    sys.exit(0 if success else 1)
