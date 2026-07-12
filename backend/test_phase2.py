"""
Phase 2 手动测试脚本

快速测试 Orchestrator V2 的各种场景
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.orchestrator_v2 import run_query
from app.core.config import settings
import json
from decimal import Decimal


class CustomJSONEncoder(json.JSONEncoder):
    """自定义 JSON Encoder 处理特殊类型"""
    def default(self, obj):
        # 处理 datetime/date/Timestamp
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        # 处理 Decimal
        if isinstance(obj, Decimal):
            return float(obj)
        # 处理 Pandas/Polars Timestamp
        if hasattr(obj, 'strftime'):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        # 其他类型转为字符串
        return str(obj)


async def test_scenario(query: str, description: str):
    """测试单个场景"""
    print(f"\n{'='*60}")
    print(f"测试: {description}")
    print(f"查询: {query}")
    print(f"{'='*60}")

    try:
        result = await run_query(query)

        print(f"\n✓ 意图: {result['intent']}")
        print(f"✓ 实体: {json.dumps(result['entities'], ensure_ascii=False, cls=CustomJSONEncoder)}")

        response = result['response']
        print(f"\n响应类型: {response['type']}")
        print(f"成功: {response.get('success', 'N/A')}")

        if response.get('sql'):
            print(f"\nSQL:\n{response['sql']}")

        if response.get('data'):
            data = response['data']
            print(f"\n数据行数: {len(data)}")
            if len(data) > 0:
                print(f"示例数据: {json.dumps(data[0], ensure_ascii=False, indent=2, cls=CustomJSONEncoder)}")

        print(f"\n推理轨迹:")
        for i, trace in enumerate(result['reasoning_trace'], 1):
            print(f"  {i}. {trace['node']} - {trace.get('timestamp', '')}")

        return True

    except Exception as e:
        print(f"\n✗ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试场景"""
    print("="*60)
    print("SignalPilot Phase 2 测试")
    print("="*60)

    # 检查 API Key
    if not settings.anthropic_api_key:
        print("\n⚠️  警告: ANTHROPIC_API_KEY 未配置")
        print("请设置环境变量: export ANTHROPIC_API_KEY='sk-ant-...'")
        print("\n将使用 fallback 模式（关键词匹配）进行测试\n")

    print(f"settings.database_path 的实际值: '{settings.database_path}'")
    # 检查数据库
    project_root = Path(__file__).parent.parent
    print(f"\n项目根目录: {project_root}")
    db_path = project_root / settings.database_path
    print(f"数据库路径: {db_path}")
    if not os.path.exists(db_path):
        print(f"\n⚠️  警告: 数据库文件不存在: {db_path}")
        print("SQL 执行将失败，但意图分类仍可测试\n")

    # 测试场景
    scenarios = [
        ("查询德国站GMV", "简单数据查询"),
        ("过去7天德国站的GMV是多少？", "带日期范围的查询"),
        ("为什么德国站GMV下降了15%？", "根因分析查询"),
        ("对比德国站和英国站的表现", "对比分析查询"),
        ("生成本周业务报告", "报告生成查询"),
    ]

    success_count = 0
    for query, description in scenarios:
        if await test_scenario(query, description):
            success_count += 1
        await asyncio.sleep(1)  # 避免 API 限流

    # 总结
    print(f"\n{'='*60}")
    print(f"测试完成: {success_count}/{len(scenarios)} 成功")
    print(f"{'='*60}\n")

    if success_count == len(scenarios):
        print("✓ 所有测试通过！Phase 2 工作正常。")
    else:
        print(f"⚠️  {len(scenarios) - success_count} 个测试失败，请检查配置。")


if __name__ == "__main__":
    asyncio.run(main())
