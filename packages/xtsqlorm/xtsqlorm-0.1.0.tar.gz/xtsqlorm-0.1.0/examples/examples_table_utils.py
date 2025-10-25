# !/usr/bin/env python3
"""
==============================================================
Description  : xtsqlorm 表工具函数使用示例
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-24 16:00:00
Github       : https://github.com/sandorn/xtsqlorm

本示例演示了 table_utils 模块的核心功能:
- get_or_create_table_model: 智能获取或创建表模型(两种模式)
- generate_model_file: 使用sqlacodegen生成模型文件
- reflect_table: 同步反射表结构
- reflect_table_async: 异步反射表结构(暂未实现)

注意: 示例已适配新架构(扁平化架构重构)
==============================================================
"""

from __future__ import annotations

import pprint

from xtlog import mylog as log

from xtsqlorm.table_utils import generate_model_file, get_or_create_table_model, reflect_table


def example_get_or_create_table_model():
    """示例: 智能获取或创建表模型(两种模式)"""

    try:
        log.info('\n' + '=' * 60)
        log.info('示例 1: get_or_create_table_model - 智能表模型管理')
        log.info('=' * 60)

        # ========== 模式1: 仅反射现有表(new_table_name=None)==========
        log.info('\n【模式1】仅反射现有表:')
        reflect_model = get_or_create_table_model(
            source_table_name='users2',
            db_key='default',
        )
        log.success(f'✅ 反射模型: {reflect_model.__name__} | 表名: {reflect_model.__tablename__}')
        log.info(f'   列数: {len(reflect_model.__table__.columns)}')
        log.info(f'   列名: {[col.name for col in reflect_model.__table__.columns]}')

        # ========== 模式2: 复制表结构创建新表(演示用法)==========
        log.info('\n【模式2】复制表结构创建新表:')
        backup_model = get_or_create_table_model('users2', new_table_name='users2_backup', db_key='default')

        log.info(f'   备份模型: {backup_model.__name__} | 表名: {backup_model.__tablename__}')
        log.info(f'   列数: {len(backup_model.__table__.columns)}')
        log.info(f'   列名: {[col.name for col in backup_model.__table__.columns]}')

    except Exception as e:
        log.error(f'\n❌ 示例失败: {e!s}')
        raise


def example_generate_model_file():
    """示例: 使用sqlacodegen生成模型文件"""
    try:
        log.info('\n' + '=' * 60)
        log.info('示例 2: generate_model_file - 生成静态模型文件')
        log.info('=' * 60)

        result = generate_model_file(
            tablename='users2',
            db_key='default',
        )

        if result == 0:
            log.success('✅ 模型文件已生成')
        else:
            log.error(f'❌ 生成模型文件失败,返回码: {result}')

    except Exception as e:
        log.error(f'❌ 错误: {e!s}')


def example_reflect_table():
    """示例: 同步反射表结构"""
    try:
        log.info('\n' + '=' * 60)
        log.info('示例 3: reflect_table - 同步反射表结构')
        log.info('=' * 60)

        # 反射表结构
        table_model = reflect_table(
            source_table_name='users2',
            db_key='default',
        )

        # 打印模型信息
        log.success('\n✅ 成功反射表模型')
        log.info(f'   模型类名: {table_model.__name__}')
        log.info(f'   表名: {table_model.__tablename__}')
        log.info(f'   模型类型: {type(table_model)}')

        # 打印表结构详细信息
        log.info('\n📋 表结构详情:')
        log.info(f'   列数量: {len(table_model.__table__.columns)}')

        # 打印每一列的详细信息
        log.info('\n📊 列定义:')
        for col in table_model.__table__.columns:
            log.info(f'   • {col.name}:')
            log.info(f'     - 类型: {col.type}')
            log.info(f'     - 主键: {col.primary_key}')
            log.info(f'     - 可空: {col.nullable}')
            if col.default:
                log.info(f'     - 默认值: {col.default}')
            if col.comment:
                log.info(f'     - 注释: {col.comment}')

        # 打印主键信息
        primary_keys = [col.name for col in table_model.__table__.columns if col.primary_key]
        if primary_keys:
            log.info(f'\n🔑 主键列: {", ".join(primary_keys)}')

        # 打印外键信息
        if table_model.__table__.foreign_keys:
            log.info('\n🔗 外键:')
            for fk in table_model.__table__.foreign_keys:
                log.info(f'   {fk.parent.name} -> {fk.target_fullname}')

        # 打印索引信息
        if table_model.__table__.indexes:
            log.info('\n📌 索引:')
            for idx in table_model.__table__.indexes:
                log.info(f'   {idx.name}: {[c.name for c in idx.columns]}')

        # 使用pprint打印完整结构
        log.info('\n🔍 完整表结构 (字典格式):')
        table_dict = {
            '表名': table_model.__tablename__,
            '模型类': table_model.__name__,
            '列定义': [
                {
                    '列名': col.name,
                    '类型': str(col.type),
                    '主键': col.primary_key,
                    '可空': col.nullable,
                    '默认值': str(col.default) if col.default else None,
                }
                for col in table_model.__table__.columns
            ],
            '主键': primary_keys,
        }
        pprint.pprint(table_dict, indent=2, width=100)  # noqa

        log.success('\n✨ 同步反射示例完成!\n')
        return table_model

    except Exception as e:
        log.error(f'\n❌ 反射失败: {e!s}')
        raise


def example_new_architecture():
    """示例: 使用新架构的工厂函数创建 ORM 操作对象"""
    try:
        log.info('\n' + '=' * 60)
        log.info('示例 4: 新架构 - 使用工厂函数创建 ORM 操作')
        log.info('=' * 60)

        # 导入新架构的组件
        from xtsqlorm import create_connection_manager, create_orm_operations, create_repository, create_session_provider

        # 方式1: 最简单 - 直接使用工厂函数
        log.info('\n【方式1】使用 create_orm_operations 工厂函数:')

        # 首先反射表模型
        user_model = reflect_table('users2', db_key='default')
        log.success(f'✅ 反射模型: {user_model.__name__}')

        # 创建 ORM 操作对象
        ops = create_orm_operations(user_model, db_key='default')
        log.success(f'✅ 创建 ORM 操作对象: {ops}')

        # 测试查询(如果数据库有数据)
        try:
            user = ops.get_by_id(1)
            if user:
                log.success(f'✅ 查询到用户: {user}')
            else:
                log.info('ID=1 的用户不存在')
        except Exception as e:
            log.warning(f'⚠️  查询失败(可能表中无数据): {e}')

        # 方式2: 显式构建 - 更清晰的依赖关系
        log.info('\n【方式2】显式构建依赖链:')

        # 创建连接管理器
        conn_mgr = create_connection_manager(db_key='default')
        log.success(f'✅ 创建连接管理器: {conn_mgr}')

        # 创建会话提供者
        session_provider = create_session_provider(connection_manager=conn_mgr)
        log.success(f'✅ 创建会话提供者: {session_provider}')

        # 创建仓储
        user_repo = create_repository(user_model, session_provider=session_provider)
        log.success(f'✅ 创建仓储: {user_repo}')

        # 测试基础 CRUD
        try:
            count = user_repo.count()
            log.success(f'✅ 用户总数: {count}')
        except Exception as e:
            log.warning(f'⚠️  统计失败: {e}')

        # 方式3: 工作单元模式 - 复杂事务
        log.info('\n【方式3】使用工作单元模式(UnitOfWork):')

        from xtsqlorm import UnitOfWork

        try:
            with UnitOfWork(session_provider) as uow:
                # 在同一事务中操作多个仓储
                repo = uow.repository(user_model)
                log.success('✅ 在工作单元中创建仓储')

                # 查询操作
                all_users = repo.get_all(limit=5)
                log.success(f'✅ 查询前5个用户: 共 {len(all_users)} 条')

                # 事务会自动提交
            log.success('✅ 工作单元事务已提交')

        except Exception as e:
            log.warning(f'⚠️  工作单元示例失败: {e}')

        log.success('\n✨ 新架构示例完成!\n')

    except Exception as e:
        log.error(f'\n❌ 新架构示例失败: {e!s}')
        raise


if __name__ == '__main__':
    log.info('=' * 80)
    log.info('xtsqlorm 表工具函数示例 - 新架构版本')
    log.info('=' * 80)

    # ==================== 运行示例 ====================
    # 示例1: 智能获取或创建表模型(新功能,推荐)
    example_get_or_create_table_model()

    # 示例2: 生成模型文件(使用sqlacodegen)
    example_generate_model_file()

    # 示例3: 同步反射表
    example_reflect_table()

    # 示例4: 使用新架构创建 ORM 操作
    example_new_architecture()

    log.info('=' * 80)
    log.success('🎉 所有示例运行完成!')
    log.info('=' * 80)
