# !/usr/bin/env python3
"""
==============================================================
Description  : xtsqlorm 异步功能使用示例
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-24 17:00:00
Github       : https://github.com/sandorn/xtsqlorm

本示例演示了 xtsqlorm 异步架构的核心功能:
- AsyncConnectionManager: 异步连接管理
- AsyncSessionProvider: 异步会话和事务管理
- AsyncRepository: 异步仓储模式
- reflect_table_async: 异步表反射
- 异步工厂函数

注意: 异步功能已完全实现并集成到新架构中
==============================================================
"""

from __future__ import annotations

import asyncio

from xtlog import mylog as log


async def example_async_connection_manager():
    """示例 1: 异步连接管理器"""
    try:
        log.info('\n' + '=' * 60)
        log.info('示例 1: AsyncConnectionManager - 异步连接管理')
        log.info('=' * 60)

        # 导入异步连接管理器
        from xtsqlorm import create_async_connection_manager

        # 创建异步连接管理器
        async_conn_mgr = create_async_connection_manager(db_key='default')
        log.success(f'✅ 创建异步连接管理器: {async_conn_mgr}')

        # 测试异步连接
        if await async_conn_mgr.ping():
            log.success('✅ 异步数据库连接正常')
        else:
            log.error('❌ 异步数据库连接失败')

        # 获取连接池状态
        status = async_conn_mgr.pool_status  # type: ignore[attr-defined]
        log.info(f'   连接池大小: {status["size"]}')
        log.info(f'   活跃连接数: {status["checked_out"]}')

        # 释放资源
        await async_conn_mgr.dispose()
        log.success('✅ 异步连接资源已释放\n')

    except Exception as e:
        log.error(f'\n❌ 示例失败: {e!s}')
        raise


async def example_async_session_provider():
    """示例 2: 异步会话提供者"""
    async_conn_mgr = None
    try:
        log.info('\n' + '=' * 60)
        log.info('示例 2: AsyncSessionProvider - 异步会话和事务管理')
        log.info('=' * 60)

        # 导入异步会话提供者
        from xtsqlorm import create_async_connection_manager, create_async_session_provider

        # 创建异步连接管理器和会话提供者
        async_conn_mgr = create_async_connection_manager(db_key='default')
        async_provider = create_async_session_provider(connection_manager=async_conn_mgr)
        log.success(f'✅ 创建异步会话提供者: {async_provider}')

        # 使用异步事务上下文管理器
        async with async_provider.transaction():
            log.success('✅ 异步事务已开始')
            # 可以在这里执行数据库操作
            # 事务会自动提交或回滚
        log.success('✅ 异步事务已自动提交\n')

    except Exception as e:
        log.error(f'\n❌ 示例失败: {e!s}')
        raise
    finally:
        # 清理资源
        if async_conn_mgr:
            await async_conn_mgr.dispose()


async def example_reflect_table_async():
    """示例 3: 异步反射表结构"""
    # 注意: reflect_table_async 内部会创建临时的 AsyncConnectionManager 并自动清理
    try:
        log.info('\n' + '=' * 60)
        log.info('示例 3: reflect_table_async - 异步反射表结构')
        log.info('=' * 60)

        # 导入异步反射函数
        from xtsqlorm import reflect_table_async

        # 异步反射表 (内部自动管理连接资源)
        user_model = await reflect_table_async('users2', db_key='default')
        log.success(f'✅ 异步反射模型: {user_model.__name__}')
        log.info(f'   表名: {user_model.__tablename__}')
        log.info(f'   列数: {len(user_model.__table__.columns)}')
        log.info(f'   列名: {[col.name for col in user_model.__table__.columns]}\n')

        return user_model

    except Exception as e:
        log.error(f'\n❌ 示例失败: {e!s}')
        raise


async def example_async_repository():
    """示例 4: 异步仓储模式"""
    async_conn_mgr = None
    try:
        log.info('\n' + '=' * 60)
        log.info('示例 4: AsyncRepository - 异步仓储模式')
        log.info('=' * 60)

        # 导入异步工厂函数
        from xtsqlorm import create_async_connection_manager, create_async_repository, create_async_session_provider, reflect_table_async

        # 首先异步反射表模型
        user_model = await reflect_table_async('users2', db_key='default')
        log.success(f'✅ 反射模型: {user_model.__name__}')

        # 显式创建连接管理器以便后续清理
        async_conn_mgr = create_async_connection_manager(db_key='default')
        async_provider = create_async_session_provider(connection_manager=async_conn_mgr)
        async_repo = create_async_repository(user_model, session_provider=async_provider)
        log.success(f'✅ 创建异步仓储: {async_repo}')

        # 异步查询操作
        count = await async_repo.count()  # type: ignore[attr-defined]
        log.success(f'✅ 用户总数: {count}')

        # 异步获取记录
        if count > 0:
            all_users = await async_repo.get_all(limit=5)  # type: ignore[attr-defined]
            log.success(f'✅ 查询前5个用户: 共 {len(all_users)} 条')

            # 显示第一个用户的信息
            if all_users:
                first_user = all_users[0]
                log.info(f'   第一个用户: {first_user}')

        log.success('✨ 异步仓储示例完成!\n')

    except Exception as e:
        log.error(f'\n❌ 示例失败: {e!s}')
        raise
    finally:
        # 清理资源
        if async_conn_mgr:
            await async_conn_mgr.dispose()


async def example_async_full_workflow():
    """示例 5: 异步完整工作流 - 使用工厂函数"""
    async_conn_mgr1 = None
    async_conn_mgr2 = None
    async_conn_mgr3 = None
    try:
        log.info('\n' + '=' * 60)
        log.info('示例 5: 异步完整工作流 - 三种使用方式')
        log.info('=' * 60)

        from xtsqlorm import create_async_connection_manager, create_async_repository, create_async_session_provider, reflect_table_async

        # 方式1: 显式构建 - 最清晰的依赖关系和资源管理
        log.info('\n【方式1】显式构建异步依赖链:')
        user_model = await reflect_table_async('users2', db_key='default')
        async_conn_mgr1 = create_async_connection_manager(db_key='default')
        async_provider1 = create_async_session_provider(connection_manager=async_conn_mgr1)
        async_repo1 = create_async_repository(user_model, session_provider=async_provider1)
        count1 = await async_repo1.count()  # type: ignore[attr-defined]
        log.success(f'✅ 用户总数(方式1): {count1}')

        # 方式2: 共享模型 - 复用已反射的模型类
        log.info('\n【方式2】复用模型类:')
        async_conn_mgr2 = create_async_connection_manager(db_key='default')
        async_provider2 = create_async_session_provider(connection_manager=async_conn_mgr2)
        async_repo2 = create_async_repository(user_model, session_provider=async_provider2)
        count2 = await async_repo2.count()  # type: ignore[attr-defined]
        log.success(f'✅ 用户总数(方式2): {count2}')

        # 方式3: 外部事务管理 - 复杂操作
        log.info('\n【方式3】外部异步事务管理:')
        async_conn_mgr3 = create_async_connection_manager(db_key='default')
        async_provider3 = create_async_session_provider(connection_manager=async_conn_mgr3)

        async with async_provider3.transaction():
            async_repo3 = create_async_repository(user_model, session_provider=async_provider3)
            # 在同一事务中执行多个操作
            users = await async_repo3.get_all(limit=3)  # type: ignore[attr-defined]
            log.success(f'✅ 查询前3个用户(方式3): 共 {len(users)} 条')

        log.success('\n✨ 异步完整工作流示例完成!\n')

    except Exception as e:
        log.error(f'\n❌ 示例失败: {e!s}')
        raise
    finally:
        # 清理所有资源
        if async_conn_mgr1:
            await async_conn_mgr1.dispose()
        if async_conn_mgr2:
            await async_conn_mgr2.dispose()
        if async_conn_mgr3:
            await async_conn_mgr3.dispose()


async def example_async_crud_operations():
    """示例 6: 异步CRUD操作"""
    async_conn_mgr = None
    try:
        log.info('\n' + '=' * 60)
        log.info('示例 6: 异步CRUD操作 - 创建、读取、更新、删除')
        log.info('=' * 60)

        from xtsqlorm import create_async_connection_manager, create_async_repository, create_async_session_provider, reflect_table_async

        # 反射表模型
        user_model = await reflect_table_async('users2', db_key='default')

        # 显式创建连接管理器以便后续清理
        async_conn_mgr = create_async_connection_manager(db_key='default')
        async_provider = create_async_session_provider(connection_manager=async_conn_mgr)
        async_repo = create_async_repository(user_model, session_provider=async_provider)

        # 读取操作
        log.info('\n【读取操作】')
        all_users = await async_repo.get_all(limit=5, offset=0)  # type: ignore[attr-defined]
        log.success(f'✅ 查询用户: 共 {len(all_users)} 条')

        if all_users:
            # 获取单个用户
            first_user_id = all_users[0].id  # type: ignore[attr-defined]
            user = await async_repo.get_by_id(first_user_id)  # type: ignore[attr-defined]
            if user:
                log.success(f'✅ 获取用户 ID={first_user_id}: {user}')

            # 检查用户是否存在
            exists = await async_repo.exists(first_user_id)  # type: ignore[attr-defined]
            log.success(f'✅ 用户 ID={first_user_id} 存在: {exists}')

        # 创建操作 (注意: 这里仅作演示,实际可能会因为约束失败)
        log.info('\n【创建操作】(仅演示代码,可能因约束而失败)')
        log.info('   # new_user = await async_repo.create({"name": "Async Test User", "phone": "1234567890", "password_hash": "test"})')

        # 更新操作 (仅演示代码)
        log.info('\n【更新操作】(仅演示代码)')
        log.info('   # updated_user = await async_repo.update(user_id, {"name": "Updated Name"})')

        # 删除操作 (仅演示代码)
        log.info('\n【删除操作】(仅演示代码)')
        log.info('   # deleted = await async_repo.delete(user_id)')

        log.success('\n✨ 异步CRUD操作示例完成!\n')

    except Exception as e:
        log.error(f'\n❌ 示例失败: {e!s}')
        raise
    finally:
        # 清理资源
        if async_conn_mgr:
            await async_conn_mgr.dispose()


async def main():
    """主函数 - 运行所有异步示例"""
    log.info('=' * 80)
    log.info('xtsqlorm 异步功能示例 - 完整演示')
    log.info('=' * 80)

    # 示例1: 异步连接管理器
    await example_async_connection_manager()

    # 示例2: 异步会话提供者
    await example_async_session_provider()

    # 示例3: 异步反射表结构
    await example_reflect_table_async()

    # 示例4: 异步仓储模式
    await example_async_repository()

    # 示例5: 异步完整工作流
    await example_async_full_workflow()

    # 示例6: 异步CRUD操作
    await example_async_crud_operations()

    log.info('=' * 80)
    log.success('🎉 所有异步示例运行完成!')
    log.info('=' * 80)


if __name__ == '__main__':
    # 运行异步主函数
    asyncio.run(main())
