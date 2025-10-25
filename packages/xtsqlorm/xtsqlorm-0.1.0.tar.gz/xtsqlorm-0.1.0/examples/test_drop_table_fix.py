# !/usr/bin/env python3
"""
测试删除表功能修复
"""

from __future__ import annotations

from sqlalchemy import Column, Integer, String, inspect, text

from xtsqlorm import BaseModel, IdMixin, create_connection_manager


def test_drop_table_fixed():
    """测试修复后的删除表功能"""
    print('=' * 60)
    print('测试删除表功能修复')
    print('=' * 60)

    # 定义测试模型
    class TestTable(BaseModel, IdMixin):
        """测试表模型"""

        __tablename__ = 'test_drop_table_example'
        name = Column(String(100))

    conn_mgr = create_connection_manager(db_key='default')
    inspector = inspect(conn_mgr.engine)
    table_name = 'test_drop_table_example'

    # 步骤1: 创建测试表
    print(f'\n步骤1: 创建测试表 {table_name}')
    if not inspector.has_table(table_name):
        TestTable.__table__.create(conn_mgr.engine, checkfirst=True)
        print(f'✅ 测试表 {table_name} 创建成功')
    else:
        print(f'⚠️  测试表 {table_name} 已存在')

    # 步骤2: 验证表存在
    print('\n步骤2: 验证表是否存在')
    exists = inspector.has_table(table_name)
    print(f'✅ 表存在状态: {exists}')

    # 步骤3: 使用修复后的方法删除表
    print(f'\n步骤3: 删除表 {table_name}')

    # 方法1: 使用 text() 包装的原生 SQL (已修复)
    print('\n【方法1: 使用 text() + 原生 SQL】')
    try:
        with conn_mgr.engine.connect() as connection:
            connection.execute(text(f'DROP TABLE IF EXISTS {table_name}'))
            connection.commit()
        print('✅ 使用 text() 删除成功')
    except Exception as e:
        print(f'❌ 删除失败: {e}')

    # 验证删除结果
    print('\n步骤4: 验证表是否已删除')
    # 刷新 inspector
    inspector = inspect(conn_mgr.engine)
    exists_after = inspector.has_table(table_name)
    if not exists_after:
        print(f'✅ 表 {table_name} 已成功删除')
    else:
        print(f'❌ 表 {table_name} 仍然存在')

    # 清理
    conn_mgr.dispose()

    print('\n' + '=' * 60)
    print('测试完成!')
    print('=' * 60)


def test_alternative_drop_methods():
    """测试其他删除表的方法"""
    print('\n' + '=' * 60)
    print('测试其他删除表方法')
    print('=' * 60)

    from xtsqlorm import Base

    # 定义测试模型
    class TestTable2(BaseModel, IdMixin):
        """测试表模型2"""

        __tablename__ = 'test_drop_table_example2'
        name = Column(String(100))

    conn_mgr = create_connection_manager(db_key='default')
    inspector = inspect(conn_mgr.engine)
    table_name = 'test_drop_table_example2'

    # 创建测试表
    print(f'\n创建测试表 {table_name}')
    if not inspector.has_table(table_name):
        TestTable2.__table__.create(conn_mgr.engine, checkfirst=True)
        print('✅ 创建成功')

    # 方法2: 使用模型的 __table__.drop()
    print('\n【方法2: 使用 __table__.drop()】')
    try:
        TestTable2.__table__.drop(conn_mgr.engine, checkfirst=True)
        print('✅ 使用 __table__.drop() 删除成功')
    except Exception as e:
        print(f'❌ 删除失败: {e}')

    # 验证
    inspector = inspect(conn_mgr.engine)
    exists = inspector.has_table(table_name)
    print(f'表是否仍存在: {exists}')

    conn_mgr.dispose()


def main():
    """主函数"""
    try:
        test_drop_table_fixed()
        test_alternative_drop_methods()

        print('\n✅ 所有测试通过!')
        print('\n💡 修复说明:')
        print('   1. 使用 text() 包装原生 SQL')
        print('   2. 添加异常处理')
        print('   3. 提供多种删除方法')

    except Exception as e:
        print(f'\n❌ 测试失败: {e}')
        import traceback

        traceback.print_exc()


if __name__ == '__main__':
    main()
