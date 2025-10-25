# !/usr/bin/env python3
"""
测试所有示例文件
"""

from __future__ import annotations

import subprocess
import sys

examples = [
    ('示例01: 基础同步CRUD', 'example_01_basic_sync.py'),
    ('示例02: 高级ORM操作', 'example_02_advanced_operations.py'),
    ('示例03: 表反射', 'example_03_table_reflection.py'),
    ('示例04: Mixin和自定义类型', 'example_04_mixins_and_types.py'),
    ('示例05: 数据验证', 'example_05_data_validation.py'),
    ('示例06: 事务管理', 'example_06_transactions.py'),
    ('示例07: 完整工作流', 'example_07_complete_workflow.py'),
    ('示例08: 表管理', 'example_08_table_management.py'),
]

results = []

for name, filename in examples:
    print(f'\n{"=" * 70}')
    print(f'测试: {name} ({filename})')
    print('=' * 70)

    try:
        result = subprocess.run([sys.executable, f'examples/{filename}'], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print(f'✅ {name} - 通过')
            results.append((name, 'PASS', None))
        else:
            print(f'❌ {name} - 失败 (exit code={result.returncode})')
            error_lines = result.stderr.splitlines()[-10:]  # 只显示最后10行错误
            error = '\n'.join(error_lines)
            print(f'错误信息:\n{error}')
            results.append((name, 'FAIL', error))

    except subprocess.TimeoutExpired:
        print(f'⏱️  {name} - 超时')
        results.append((name, 'TIMEOUT', None))
    except Exception as e:
        print(f'💥 {name} - 异常: {e}')
        results.append((name, 'ERROR', str(e)))


# 汇总结果
print('\n\n' + '=' * 70)
print('测试汇总')
print('=' * 70)

passed = sum(1 for _, status, _ in results if status == 'PASS')
failed = sum(1 for _, status, _ in results if status == 'FAIL')
errors = sum(1 for _, status, _ in results if status in ('TIMEOUT', 'ERROR'))

for name, status, error in results:
    status_icon = {'PASS': '✅', 'FAIL': '❌', 'TIMEOUT': '⏱️ ', 'ERROR': '💥'}.get(status, '❓')

    print(f'{status_icon} {name}: {status}')
    if error and status == 'FAIL':
        print(f'   错误: {error[:100]}...')

print(f'\n总计: {len(results)} 个示例')
print(f'通过: {passed}')
print(f'失败: {failed}')
print(f'错误: {errors}')

if failed == 0 and errors == 0:
    print('\n🎉 所有示例测试通过!')
    sys.exit(0)
else:
    print('\n⚠️  部分示例测试失败,请检查')
    sys.exit(1)
