#!/usr/bin/env python3
"""
测试 IdMixin 的 id 字段是否正确
"""

from __future__ import annotations

from user import UserModel


def test_id_field():
    """测试 id 字段访问"""
    print('=' * 60)
    print('测试 IdMixin 的 id 字段')
    print('=' * 60)

    # 测试 1: 检查类属性
    print('\n【测试 1】检查类属性:')
    try:
        id_column = UserModel.id
        print(f'✅ UserModel.id 存在: {id_column}')
        print(f'   类型: {type(id_column)}')
    except AttributeError as e:
        print(f'❌ 错误: {e}')
        return False

    # 测试 2: 检查字段名
    print('\n【测试 2】检查字段名:')
    try:
        # 获取主键列
        pk_columns = [col for col in UserModel.__table__.columns if col.primary_key]
        if pk_columns:
            pk_name = pk_columns[0].name
            print(f'✅ 主键字段名: {pk_name}')
            if pk_name == 'id':
                print('✅ 字段名是 id (小写) - 正确!')
            else:
                print(f'❌ 字段名是 {pk_name} - 应该是 id')
                return False
        else:
            print('❌ 没有找到主键列')
            return False
    except Exception as e:
        print(f'❌ 错误: {e}')
        return False

    # 测试 3: 检查所有列
    print('\n【测试 3】所有列名:')
    for col in UserModel.__table__.columns:
        pk_marker = ' (主键)' if col.primary_key else ''
        print(f'   - {col.name}{pk_marker}')

    print('\n' + '=' * 60)
    print('✅ 所有测试通过! IdMixin 的 id 字段(小写)正常工作')
    print('=' * 60)
    return True


if __name__ == '__main__':
    import sys

    success = test_id_field()
    sys.exit(0 if success else 1)
