# !/usr/bin/env python3
"""
==============================================================
示例 06: 事务管理和工作单元
==============================================================

本示例演示:
1. 基础事务管理
2. 工作单元模式 (UnitOfWork)
3. 复杂事务场景
4. 事务回滚
"""

from __future__ import annotations

from sqlalchemy import text

from xtsqlorm import UnitOfWork, create_repository, create_session_provider


def print_section(title: str):
    """打印分隔线"""
    print(f'\n{"=" * 60}')
    print(f'{title}')
    print('=' * 60)


def example_1_simple_transaction():
    """示例 1: 简单事务"""
    print_section('示例 1: 简单事务管理')

    from user import UserModel

    session_provider = create_session_provider(db_key='default')

    print('使用 transaction() 上下文管理器:')
    print('   - 自动开始事务')
    print('   - 成功时自动提交')
    print('   - 异常时自动回滚')
    print('   - 结束时自动关闭 Session\n')

    # 自动事务管理
    with session_provider.transaction() as session:
        print('✅ 事务已开始')

        # 在事务中执行操作
        result = session.execute(text('SELECT COUNT(*) FROM users'))
        count = result.scalar()
        print(f'✅ 查询到 {count} 个用户')

        # 事务会在退出 with 块时自动提交
    print('✅ 事务已自动提交\n')


def example_2_transaction_rollback():
    """示例 2: 事务回滚"""
    print_section('示例 2: 事务回滚')

    from user import UserModel

    session_provider = create_session_provider(db_key='default')
    create_repository(UserModel, session_provider=session_provider)

    print('当发生异常时,事务会自动回滚:\n')

    try:
        with session_provider.transaction() as session:
            print('✅ 事务已开始')

            # 执行一些操作 - 直接使用 session 查询
            users = session.query(UserModel).limit(1).all()
            print(f'✅ 查询到 {len(users)} 个用户')

            # 模拟异常
            print('⚠️  模拟发生异常...')
            raise ValueError('模拟的异常')

    except ValueError as e:
        print(f'❌ 捕获异常: {e}')
        print('✅ 事务已自动回滚')


def example_3_unit_of_work():
    """示例 3: 工作单元模式"""
    print_section('示例 3: 工作单元模式 (UnitOfWork)')

    from user import UserModel

    session_provider = create_session_provider(db_key='default')

    print('工作单元的优势:')
    print('   - 统一管理多个仓储')
    print('   - 自动事务控制')
    print('   - 原子性操作(全部成功或全部失败)\n')

    print('【实际执行示例】')

    # 使用工作单元 - 实际执行
    with UnitOfWork(session_provider) as uow:
        print('✅ 工作单元事务已开始')

        # 获取仓储 - 使用 repository() 方法
        uow.repository(UserModel)
        print('✅ 已创建 users 仓储')

        # 在同一事务中执行操作 - 使用 uow.session
        total_users = uow.session.query(UserModel).count()
        print(f'✅ 用户总数: {total_users}')

        # 工作单元会在退出 with 块时自动提交
    print('✅ 工作单元事务已自动提交')


def example_4_complex_transaction():
    """示例 4: 复杂事务场景"""
    print_section('示例 4: 复杂事务场景')

    from user import UserModel, UserProfileModel

    session_provider = create_session_provider(db_key='default')
    user_repo = create_repository(UserModel, session_provider=session_provider)
    profile_repo = create_repository(UserProfileModel, session_provider=session_provider)

    print('场景: 创建用户和用户资料(需要保证原子性)\n')
    print('【实际执行示例】')

    try:
        import time

        timestamp = int(time.time())

        with session_provider.transaction() as session:
            # 1. 创建用户
            user = user_repo.create_in_session(
                {
                    'username': f'complex_user_{timestamp}',
                    'email': f'complex_{timestamp}@example.com',
                    'password': 'hashed_password',
                },
                session,
            )
            session.flush()  # 确保获取到 user.id
            print(f'✅ 步骤1: 创建用户成功, ID={user.id}')  # type: ignore[attr-defined]

            # 2. 创建用户资料(需要 user_profiles 表存在)
            profile = profile_repo.create_in_session(
                {
                    'user_id': user.id,  # type: ignore[attr-defined]
                    'real_name': f'测试用户_{timestamp}',
                    'gender': 'male',
                },
                session,
            )
            print('✅ 步骤2: 创建用户资料成功')

            # 事务自动提交
        print('✅ 事务提交成功: 用户和资料都已创建')

        # 清理测试数据
        user_repo.delete(user.id)  # type: ignore[attr-defined]
        profile_repo.delete(profile.id)  # type: ignore[attr-defined]
        print('   已清理测试数据')

    except Exception as e:
        print(f'⚠️  操作失败(可能表不存在): {e}')
        print('   说明: 此示例需要 user_profiles 表存在')
        print('   如果任何步骤失败,整个事务会自动回滚')


def example_5_nested_transactions():
    """示例 5: 嵌套事务(说明)"""
    print_section('示例 5: 嵌套事务说明')

    print('SQLAlchemy 支持嵌套事务(Savepoint):')
    print('')
    print('from sqlalchemy.orm import Session')
    print('from xtsqlorm import create_session_provider')
    print('')
    print('provider = create_session_provider()')
    print('')
    print('with provider.transaction() as session:')
    print('    # 外层事务')
    print('    print("外层事务开始")')
    print('')
    print('    # 创建 savepoint')
    print('    with session.begin_nested():')
    print('        # 内层事务')
    print('        print("内层事务开始")')
    print('        # 执行操作...')
    print('        # 如果失败,只回滚到 savepoint')
    print('')
    print('    # 外层事务继续')
    print('    # 执行更多操作...')
    print('')
    print('注意: 嵌套事务依赖数据库支持(如 MySQL, PostgreSQL)')


def example_6_manual_transaction():
    """示例 6: 手动事务控制"""
    print_section('示例 6: 手动事务控制(不推荐)')

    from user import UserModel

    create_session_provider(db_key='default')

    print('虽然可以手动控制事务,但不推荐:')
    print('')
    print('# 不推荐的方式')
    print('session = session_provider.create_session()')
    print('try:')
    print('    # 执行操作...')
    print('    session.commit()')
    print('except Exception:')
    print('    session.rollback()')
    print('    raise')
    print('finally:')
    print('    session.close()')
    print('')
    print('推荐使用 transaction() 上下文管理器(自动管理)')


def main():
    """主函数"""
    print('=' * 80)
    print('xtsqlorm 事务管理和工作单元示例')
    print('=' * 80)

    example_1_simple_transaction()
    example_2_transaction_rollback()
    example_3_unit_of_work()
    example_4_complex_transaction()
    example_5_nested_transactions()
    example_6_manual_transaction()

    print('\n' + '=' * 80)
    print('🎉 所有示例运行完成!')
    print('=' * 80)


if __name__ == '__main__':
    main()
