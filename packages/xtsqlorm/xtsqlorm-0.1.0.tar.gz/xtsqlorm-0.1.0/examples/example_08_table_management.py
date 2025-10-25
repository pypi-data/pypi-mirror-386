# !/usr/bin/env python3
"""
==============================================================
示例 08: 表管理 - 检查、创建、删除
==============================================================

本示例演示:
1. 检查表是否存在
2. 创建表(如果不存在)
3. 删除表
4. 批量创建多个表
5. 表结构验证
"""

from __future__ import annotations

from sqlalchemy import Column, Integer, String, inspect, text

from xtsqlorm import Base, BaseModel, IdMixin, TimestampMixin, create_connection_manager


def print_section(title: str):
    """打印分隔线"""
    print(f'\n{"=" * 60}')
    print(f'{title}')
    print('=' * 60)


def check_table_exists(conn_mgr, table_name: str) -> bool:
    """检查表是否存在

    Args:
        conn_mgr: 连接管理器
        table_name: 表名

    Returns:
        bool: 表是否存在
    """
    inspector = inspect(conn_mgr.engine)
    return inspector.has_table(table_name)


def create_table_if_not_exists(conn_mgr, model_class, table_name: str | None = None):
    """检查表是否存在, 不存在则创建

    Args:
        conn_mgr: 连接管理器
        model_class: 模型类
        table_name: 表名(可选, 默认从模型类获取)
    """
    if table_name is None:
        table_name = model_class.__tablename__  # type: ignore[attr-defined]

    inspector = inspect(conn_mgr.engine)

    if inspector.has_table(table_name):
        print(f'✅ 表 {table_name} 已存在')
        return False
    print(f'⚠️  表 {table_name} 不存在, 正在创建...')
    # 只创建这个模型的表
    model_class.__table__.create(conn_mgr.engine, checkfirst=True)  # type: ignore[attr-defined]
    print(f'✅ 表 {table_name} 创建成功')
    return True


def example_1_check_table_exists():
    """示例 1: 检查表是否存在"""
    print_section('示例 1: 检查表是否存在')

    conn_mgr = create_connection_manager(db_key='default')

    # 检查 users 表
    table_name = 'users'
    exists = check_table_exists(conn_mgr, table_name)

    if exists:
        print(f'✅ 表 {table_name} 存在')
    else:
        print(f'❌ 表 {table_name} 不存在')

    # 检查多个表
    tables_to_check = ['users', 'user_profiles', 'articles', 'non_existent_table']
    print('\n检查多个表:')
    for tbl in tables_to_check:
        exists = check_table_exists(conn_mgr, tbl)
        status = '✅ 存在' if exists else '❌ 不存在'
        print(f'   {tbl}: {status}')

    conn_mgr.dispose()


def example_2_create_if_not_exists():
    """示例 2: 检查并创建表"""
    print_section('示例 2: 检查并创建表(如果不存在)')

    from user import UserModel

    conn_mgr = create_connection_manager(db_key='default')

    # 检查并创建 users 表
    created = create_table_if_not_exists(conn_mgr, UserModel, 'users')

    if created:
        print('表是新创建的')
    else:
        print('表已经存在, 无需创建')

    conn_mgr.dispose()


def example_3_create_test_table():
    """示例 3: 创建测试表"""
    print_section('示例 3: 创建新的测试表')

    # 定义一个测试模型
    class TestModel(BaseModel, IdMixin, TimestampMixin):
        """测试模型"""

        __tablename__ = 'test_example_table'

        name = Column(String(100), nullable=False)
        description = Column(String(500))

    conn_mgr = create_connection_manager(db_key='default')

    # 检查并创建
    table_name = 'test_example_table'
    print(f'准备创建测试表: {table_name}')

    created = create_table_if_not_exists(conn_mgr, TestModel)

    if created:
        print(f'✅ 新表 {table_name} 创建成功')

        # 显示表结构
        inspector = inspect(conn_mgr.engine)
        columns = inspector.get_columns(table_name)
        print('\n表结构:')
        for col in columns:
            print(f'   - {col["name"]}: {col["type"]}')

    conn_mgr.dispose()


def example_4_batch_create_tables():
    """示例 4: 批量创建多个表"""
    print_section('示例 4: 批量创建多个表')

    # 定义多个模型
    class Category(BaseModel, IdMixin):
        """分类模型"""

        __tablename__ = 'categories_example'
        name = Column(String(100), nullable=False)

    class Tag(BaseModel, IdMixin):
        """标签模型"""

        __tablename__ = 'tags_example'
        name = Column(String(50), nullable=False)

    class Comment(BaseModel, IdMixin, TimestampMixin):
        """评论模型"""

        __tablename__ = 'comments_example'
        content = Column(String(1000), nullable=False)
        author_id = Column(Integer)

    conn_mgr = create_connection_manager(db_key='default')

    # 批量创建
    models = [
        (Category, 'categories_example'),
        (Tag, 'tags_example'),
        (Comment, 'comments_example'),
    ]

    print('批量创建表:')
    created_count = 0
    for model, table_name in models:
        created = create_table_if_not_exists(conn_mgr, model, table_name)
        if created:
            created_count += 1

    print(f'\n✅ 共创建了 {created_count} 个新表')

    conn_mgr.dispose()


def example_5_drop_table():
    """示例 5: 删除表"""
    print_section('示例 5: 删除测试表')

    conn_mgr = create_connection_manager(db_key='default')

    # 要删除的测试表
    test_tables = [
        'test_example_table',
        'categories_example',
        'tags_example',
        'comments_example',
    ]

    print('删除测试表:')
    inspector = inspect(conn_mgr.engine)

    for table_name in test_tables:
        if inspector.has_table(table_name):
            # 使用原生 SQL 删除
            try:
                with conn_mgr.engine.connect() as connection:
                    connection.execute(text(f'DROP TABLE IF EXISTS {table_name}'))
                    connection.commit()
                print(f'   ✅ 已删除表: {table_name}')
            except Exception as e:
                print(f'   ❌ 删除表 {table_name} 失败: {e}')
        else:
            print(f'   ⚠️  表不存在: {table_name}')

    conn_mgr.dispose()


def example_6_get_all_tables():
    """示例 6: 列出所有表"""
    print_section('示例 6: 列出数据库中的所有表')

    conn_mgr = create_connection_manager(db_key='default')
    inspector = inspect(conn_mgr.engine)

    # 获取所有表名
    table_names = inspector.get_table_names()

    print(f'数据库中共有 {len(table_names)} 个表:')
    for idx, table_name in enumerate(table_names, 1):
        print(f'   {idx}. {table_name}')

    conn_mgr.dispose()


def example_7_practical_usage():
    """示例 7: 实际应用场景"""
    print_section('示例 7: 实际应用 - 确保表存在后再操作')

    from user import UserModel

    from xtsqlorm import create_repository

    conn_mgr = create_connection_manager(db_key='default')

    print('场景: 在应用启动时, 确保必要的表都已创建\n')

    # 1. 检查并创建表
    print('步骤 1: 检查并创建 users 表')
    create_table_if_not_exists(conn_mgr, UserModel, 'users')

    # 2. 创建仓储并使用
    print('\n步骤 2: 创建仓储并查询数据')
    user_repo = create_repository(UserModel, db_key='default')
    total = user_repo.count()
    print(f'✅ 用户表记录总数: {total}')

    # 3. 清理
    conn_mgr.dispose()


def main():
    """主函数"""
    print('=' * 80)
    print('xtsqlorm 表管理示例')
    print('=' * 80)

    example_1_check_table_exists()
    example_2_create_if_not_exists()
    example_3_create_test_table()
    example_4_batch_create_tables()
    example_6_get_all_tables()
    example_7_practical_usage()

    # 清理：删除测试表
    example_5_drop_table()

    print('\n' + '=' * 80)
    print('🎉 所有示例运行完成!')
    print('=' * 80)
    print('\n💡 提示:')
    print('   - 使用 inspector.has_table() 检查表是否存在')
    print('   - 使用 model.__table__.create() 创建单个表')
    print('   - 使用 Base.metadata.create_all() 创建所有表')
    print('   - 在生产环境中, 建议使用数据库迁移工具(如 Alembic)')


if __name__ == '__main__':
    main()
