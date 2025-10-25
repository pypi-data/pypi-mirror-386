# !/usr/bin/env python3
"""
==============================================================
示例 02: 高级 ORM 操作
==============================================================

本示例演示:
1. OrmOperations 的高级查询功能
2. 分页查询
3. 统计分析
4. 批量操作
5. 数据导出
"""

from __future__ import annotations

from xtsqlorm import create_orm_operations


def print_section(title: str):
    """打印分隔线"""
    print(f'\n{"=" * 60}')
    print(f'{title}')
    print('=' * 60)


def example_1_paginated_query():
    """示例 1: 分页查询"""
    print_section('示例 1: 分页查询')

    from user import UserModel

    ops = create_orm_operations(UserModel, db_key='default')

    # 分页查询
    page = 1
    page_size = 5
    results, total = ops.get_paginated(
        page=page,
        page_size=page_size,
        order_by='id',  # IdMixin 字段名已改为小写 id
        order_dir='desc',
    )

    print(f'✅ 第 {page} 页, 每页 {page_size} 条')
    print(f'✅ 总记录数: {total}')
    print(f'✅ 当前页记录数: {len(results)}')

    for idx, user in enumerate(results, 1):
        print(f'   {idx}. ID: {user.id}, 用户名: {user.username}')  # type: ignore[attr-defined]


def example_2_conditional_query():
    """示例 2: 条件查询"""
    print_section('示例 2: 条件查询')

    from user import UserModel

    ops = create_orm_operations(UserModel, db_key='default')

    # 单条件查询
    user = ops.get_one({'is_active': True})
    if user:
        print(f'✅ 找到活跃用户: {user.username}')  # type: ignore[attr-defined]

    # 多条件 OR 查询
    # (is_admin=True) OR (login_count > 10)
    from user import UserModel as UM

    results = ops.filter_by_conditions(
        [
            {'is_admin': True},
            # {'login_count': 10},  # 需要更复杂的条件表达式
        ],
        limit=5,
    )
    print(f'✅ 多条件查询结果: {len(results)} 条')


def example_3_statistics():
    """示例 3: 统计分析"""
    print_section('示例 3: 统计分析')

    from user import UserModel

    ops = create_orm_operations(UserModel, db_key='default')

    # 字段统计
    try:
        stats = ops.get_field_stats('login_count')
        print('✅ login_count 字段统计:')
        print(f'   - 总数: {stats["count"]}')
        print(f'   - 最小值: {stats["min"]}')
        print(f'   - 最大值: {stats["max"]}')
        print(f'   - 平均值: {stats["avg"]:.2f}')
    except Exception as e:
        print(f'⚠️  统计失败: {e}')


def example_4_batch_operations():
    """示例 4: 批量操作"""
    print_section('示例 4: 批量操作')

    from user import UserModel

    ops = create_orm_operations(UserModel, db_key='default')

    print('批量操作示例 (实际执行):')

    try:
        import time

        timestamp = int(time.time())

        # 批量创建
        print('\n【批量创建】')
        users_data = [
            {
                'username': f'batch_user1_{timestamp}',
                'email': f'batch1_{timestamp}@example.com',
                'password': 'hash1',
            },
            {
                'username': f'batch_user2_{timestamp}',
                'email': f'batch2_{timestamp}@example.com',
                'password': 'hash2',
            },
            {
                'username': f'batch_user3_{timestamp}',
                'email': f'batch3_{timestamp}@example.com',
                'password': 'hash3',
            },
        ]

        created_users = ops.bulk_create(users_data)
        print(f'✅ 批量创建成功: {len(created_users)} 条记录')

        # 批量更新
        print('\n【批量更新】')
        if created_users and len(created_users) >= 2:
            update_data = [
                {'id': created_users[0].id, 'nickname': f'批量昵称1_{timestamp}'},  # type: ignore[attr-defined]
                {'id': created_users[1].id, 'nickname': f'批量昵称2_{timestamp}'},  # type: ignore[attr-defined]
            ]
            updated_count = ops.bulk_update(update_data)
            print(f'✅ 批量更新成功: {updated_count} 条记录')
        else:
            print('⚠️  跳过批量更新(没有足够的测试数据)')

        # 清理测试数据
        print('\n【清理测试数据】')
        for user in created_users:
            ops.delete(user.id)  # type: ignore[attr-defined]
        print(f'✅ 已清理 {len(created_users)} 条测试数据')

        # 优化的批量创建说明
        print('\n【优化的批量创建】')
        print('   说明: ops.bulk_create() 已经包含了优化逻辑')
        print('   可以直接处理大量数据,内部会自动分批处理')

    except Exception as e:
        print(f'⚠️  批量操作失败: {e}')


def example_5_data_export():
    """示例 5: 数据导出"""
    print_section('示例 5: 数据导出到 Pandas DataFrame')

    from user import UserModel

    ops = create_orm_operations(UserModel, db_key='default')

    # 导出所有数据
    df_all = ops.export_to_dataframe()
    print(f'✅ 导出全部数据: {len(df_all)} 行')
    print(f'✅ 列名: {list(df_all.columns)}')

    # 导出指定列
    df_partial = ops.export_to_dataframe(columns=['id', 'username', 'email'])
    print(f'✅ 导出部分列: {len(df_partial)} 行, {len(df_partial.columns)} 列')

    # 显示前几行
    if len(df_partial) > 0:
        print('\n前3行数据:')
        print(df_partial.head(3))


def example_6_raw_sql():
    """示例 6: 原生 SQL 执行"""
    print_section('示例 6: 原生 SQL 执行')

    from user import UserModel

    ops = create_orm_operations(UserModel, db_key='default')

    # 执行原生 SQL
    sql = 'SELECT COUNT(*) as total FROM users WHERE is_active = :is_active'
    result = ops.execute_raw_sql(sql, {'is_active': True})

    # 获取结果
    row = result.fetchone()
    if row:
        print(f'✅ 活跃用户数: {row[0]}')

    # 映射到 ORM 模型
    sql = 'SELECT * FROM users WHERE is_active = :is_active LIMIT :limit'
    users = ops.from_statement(sql, {'is_active': True, 'limit': 5})
    print(f'✅ 查询到 {len(users)} 个活跃用户')


def example_7_cache():
    """示例 7: 查询缓存"""
    print_section('示例 7: 查询缓存')

    from user import UserModel

    ops = create_orm_operations(UserModel, db_key='default', cache_enabled=True)

    # 第一次查询(从数据库)
    ops.get_by_id(1)
    print('✅ 第一次查询(从数据库)')

    # 第二次查询(从缓存)
    ops.get_by_id(1)
    print('✅ 第二次查询(从缓存)')

    # 清空缓存
    ops.clear_cache()
    print('✅ 缓存已清空')


def main():
    """主函数"""
    print('=' * 80)
    print('xtsqlorm 高级 ORM 操作示例')
    print('=' * 80)

    example_1_paginated_query()
    example_2_conditional_query()
    example_3_statistics()
    example_4_batch_operations()
    example_5_data_export()
    example_6_raw_sql()
    example_7_cache()

    print('\n' + '=' * 80)
    print('🎉 所有示例运行完成!')
    print('=' * 80)


if __name__ == '__main__':
    main()
