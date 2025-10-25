# !/usr/bin/env python3
"""
==============================================================
示例 01: 同步基础 CRUD 操作
==============================================================

本示例演示:
1. 使用 Repository 进行基础 CRUD 操作
2. 使用工厂函数创建对象
3. 三种使用模式对比
"""

from __future__ import annotations

from xtsqlorm import create_connection_manager, create_repository, create_session_provider
from xtsqlorm.base import BaseModel


def print_section(title: str):
    """打印分隔线"""
    print(f'\n{"=" * 60}')
    print(f'{title}')
    print('=' * 60)


def example_1_quick_start():
    """示例 1: 快速开始 - 最简单的方式"""
    print_section('示例 1: 快速开始')

    from sqlalchemy import inspect
    from user import UserModel

    # 检查数据库中表users是否存在,不存在则创建
    conn_mgr = create_connection_manager(db_key='default')
    inspector = inspect(conn_mgr.engine)
    table_name = 'users'

    if inspector.has_table(table_name):
        print(f'✅ 表 {table_name} 已存在')
    else:
        print(f'⚠️  表 {table_name} 不存在,正在创建...')
        # 创建表
        UserModel.metadata.create_all(conn_mgr.engine)
        print(f'✅ 表 {table_name} 创建成功')

    # 方式1: 一步到位(推荐)
    user_repo = create_repository(UserModel, db_key='default')
    print(f'✅ 创建仓储: {user_repo}')

    # 获取记录总数
    total = user_repo.count()
    print(f'✅ 用户总数: {total}')

    # 查询所有用户(限制5条)
    users = user_repo.get_all(limit=5)
    print(f'✅ 查询前5个用户: {len(users)} 条')
    for user in users:
        print(f'   - ID: {user.id}, 用户名: {user.username}')


def example_2_explicit_dependencies():
    """示例 2: 显式依赖构建 - 更清晰的依赖关系"""
    print_section('示例 2: 显式依赖构建')

    from user import UserModel

    # 方式2: 显式构建依赖链
    conn_mgr = create_connection_manager(db_key='default')
    print(f'✅ 创建连接管理器: {conn_mgr}')

    session_provider = create_session_provider(connection_manager=conn_mgr)
    print(f'✅ 创建会话提供者: {session_provider}')

    user_repo = create_repository(UserModel, session_provider=session_provider)
    print(f'✅ 创建仓储: {user_repo}')

    # 测试连接
    if conn_mgr.ping():
        print('✅ 数据库连接正常')

    # 获取连接池状态
    pool_status = conn_mgr.pool_status
    print(f'✅ 连接池状态: {pool_status}')

    # 清理资源
    conn_mgr.dispose()
    print('✅ 连接资源已释放')


def example_3_crud_operations():
    """示例 3: 完整的 CRUD 操作"""
    print_section('示例 3: 完整的 CRUD 操作')

    from user import UserModel

    user_repo = create_repository(UserModel, db_key='default')

    # === CREATE - 创建 ===
    print('\n【创建操作】')
    try:
        import time

        timestamp = int(time.time())

        new_user = user_repo.create({
            'username': f'demo_user_{timestamp}',
            'email': f'demo_{timestamp}@example.com',
            'password': 'hashed_password',
        })
        created_id = new_user.id  # type: ignore[attr-defined]
        print(f'✅ 创建成功: ID={created_id}, username={new_user.username}')  # type: ignore[attr-defined]
    except Exception as e:
        print(f'⚠️  创建失败: {e}')
        created_id = None

    # === READ - 读取 ===
    print('\n【读取操作】')
    users = user_repo.get_all(limit=3)
    if users:
        user_id = users[0].id  # type: ignore[attr-defined]
        print(f'   获取到用户 ID: {user_id}')

        # 根据 ID 获取单条记录
        user = user_repo.get_by_id(user_id)
        if user:
            print(f'   ✅ get_by_id({user_id}): {user.username}')  # type: ignore[attr-defined]

        # 检查记录是否存在
        exists = user_repo.exists(user_id)
        print(f'   ✅ exists({user_id}): {exists}')

    # === UPDATE - 更新 ===
    print('\n【更新操作】')
    if created_id:
        try:
            updated_user = user_repo.update(created_id, {'nickname': f'昵称_{timestamp}'})
            if updated_user:
                print(f'✅ 更新成功: ID={created_id}, nickname={updated_user.nickname}')  # type: ignore[attr-defined]
        except Exception as e:
            print(f'⚠️  更新失败: {e}')

    # === DELETE - 删除 ===
    print('\n【删除操作】')
    if created_id:
        try:
            deleted = user_repo.delete(created_id)
            if deleted:
                print(f'✅ 删除成功: ID={created_id}')
            else:
                print('⚠️  删除失败: 记录不存在')
        except Exception as e:
            print(f'⚠️  删除失败: {e}')


def example_4_external_transaction():
    """示例 4: 外部事务管理"""
    print_section('示例 4: 外部事务管理')

    from user import UserModel

    session_provider = create_session_provider(db_key='default')
    user_repo = create_repository(UserModel, session_provider=session_provider)

    print('使用外部事务可以在同一事务中执行多个操作:')

    # 使用外部事务
    with session_provider.transaction() as session:
        print('✅ 事务已开始')

        # 在同一事务中执行多个操作
        # 方式1: 直接使用 session 查询
        users = session.query(UserModel).limit(2).all()
        print(f'✅ 在事务中查询到 {len(users)} 条记录')

        if users:
            user_id = users[0].id  # type: ignore[attr-defined]
            # 方式2: 使用仓储的 *_in_session 方法
            user = user_repo.get_by_id_in_session(user_id, session)
            print(f'✅ 在事务中获取用户: {user.username if user else None}')  # type: ignore[attr-defined]

        # 事务会在退出 with 块时自动提交
    print('✅ 事务已自动提交')


def main():
    """主函数"""
    print('=' * 80)
    print('xtsqlorm 同步基础 CRUD 操作示例')
    print('=' * 80)

    example_1_quick_start()
    example_2_explicit_dependencies()
    example_3_crud_operations()
    example_4_external_transaction()

    print('\n' + '=' * 80)
    print('🎉 所有示例运行完成!')
    print('=' * 80)


if __name__ == '__main__':
    main()
