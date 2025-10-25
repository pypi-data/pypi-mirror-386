# !/usr/bin/env python3
"""
==============================================================
示例 03: 表反射和动态模型
==============================================================

本示例演示:
1. 反射现有数据库表
2. 动态创建模型类
3. 表复制功能
4. 生成模型文件
"""

from __future__ import annotations

from xtsqlorm import create_connection_manager, create_repository, generate_model_file, get_or_create_table_model, reflect_table


def print_section(title: str):
    """打印分隔线"""
    print(f'\n{"=" * 60}')
    print(f'{title}')
    print('=' * 60)


def example_1_reflect_table():
    """示例 1: 反射数据库表"""
    print_section('示例 1: 反射数据库表')

    # 反射已存在的表
    UserModel = reflect_table('users', db_key='default')

    print(f'✅ 反射模型类: {UserModel.__name__}')
    print(f'✅ 表名: {UserModel.__tablename__}')  # type: ignore[attr-defined]
    print(f'✅ 列数: {len(UserModel.__table__.columns)}')  # type: ignore[attr-defined]

    # 显示所有列
    print('\n列信息:')
    for column in UserModel.__table__.columns:  # type: ignore[attr-defined]
        print(f'   - {column.name}: {column.type}')

    # 使用反射的模型进行查询
    user_repo = create_repository(UserModel, db_key='default')
    total = user_repo.count()
    print(f'\n✅ 使用反射模型查询: 共 {total} 条记录')


def example_2_get_or_create_table():
    """示例 2: 获取或创建表模型"""
    print_section('示例 2: 获取或创建表模型')

    conn_mgr = create_connection_manager(db_key='default')

    # 方式1: 仅反射(new_table_name=None)
    print('\n【方式1: 仅反射现有表】')
    UserModel = get_or_create_table_model(
        source_table_name='users',
        db_conn=conn_mgr,
        new_table_name=None,  # 仅反射
    )
    print(f'✅ 反射表: {UserModel.__tablename__}')  # type: ignore[attr-defined]

    # 方式2: 复制表结构(实际执行示例)
    print('\n【方式2: 复制表结构到临时表】')
    try:
        # 创建一个临时表用于演示
        temp_table_name = 'users_temp_copy'

        # 先删除如果存在
        from sqlalchemy import inspect, text

        inspector = inspect(conn_mgr.engine)
        if inspector.has_table(temp_table_name):
            with conn_mgr.engine.connect() as connection:
                connection.execute(text(f'DROP TABLE IF EXISTS {temp_table_name}'))
                connection.commit()
            print(f'   已删除旧的临时表: {temp_table_name}')

        # 复制表结构
        NewUserModel = get_or_create_table_model(
            source_table_name='users',
            db_conn=conn_mgr,
            new_table_name=temp_table_name,
        )
        print(f'✅ 复制表结构成功: {NewUserModel.__tablename__}')  # type: ignore[attr-defined]

        # 清理临时表
        with conn_mgr.engine.connect() as connection:
            connection.execute(text(f'DROP TABLE IF EXISTS {temp_table_name}'))
            connection.commit()
        print(f'   已清理临时表: {temp_table_name}')

    except Exception as e:
        print(f'⚠️  复制表结构失败(可能表不存在): {e}')

    conn_mgr.dispose()


def example_3_generate_model_file():
    """示例 3: 生成模型文件"""
    print_section('示例 3: 生成模型文件')

    # 实际执行(可选)
    try:
        output_file = 'examples/generated_models.py'
        generate_model_file(
            'users',  # tablename 必需参数
            db_key='default',
            output_file=output_file,
        )
        print(f'\n✅ 模型文件已生成: {output_file}')

        # 读取并显示生成的文件内容(前20行)
        with open(output_file) as f:
            lines = f.readlines()[:20]
            print('\n生成的模型文件预览(前20行):')
            print(''.join(lines))

    except Exception as e:
        print(f'⚠️  生成模型文件失败: {e}')


def example_4_table_metadata():
    """示例 4: 探索表元数据"""
    print_section('示例 4: 探索表元数据')

    UserModel = reflect_table('users', db_key='default')

    print('表的详细元数据:')

    # 主键
    print(f'\n主键: {UserModel.__table__.primary_key.columns.keys()}')  # type: ignore[attr-defined]

    # 外键
    print(f'外键: {[fk.target_fullname for fk in UserModel.__table__.foreign_keys]}')  # type: ignore[attr-defined]

    # 索引
    print(f'\n索引数量: {len(UserModel.__table__.indexes)}')  # type: ignore[attr-defined]
    for idx in UserModel.__table__.indexes:  # type: ignore[attr-defined]
        print(f'   - {idx.name}: {[col.name for col in idx.columns]}')

    # 约束
    print(f'\n约束数量: {len(UserModel.__table__.constraints)}')  # type: ignore[attr-defined]
    for constraint in UserModel.__table__.constraints:  # type: ignore[attr-defined]
        print(f'   - {type(constraint).__name__}: {constraint.name}')

    # 列详情
    print('\n列详细信息:')
    for column in UserModel.__table__.columns:  # type: ignore[attr-defined]
        nullable = '可空' if column.nullable else '非空'
        default = f', 默认值: {column.default}' if column.default else ''
        print(f'   - {column.name}: {column.type} ({nullable}{default})')


def main():
    """主函数"""
    print('=' * 80)
    print('xtsqlorm 表反射和动态模型示例')
    print('=' * 80)

    example_1_reflect_table()
    example_2_get_or_create_table()
    example_3_generate_model_file()
    example_4_table_metadata()

    print('\n' + '=' * 80)
    print('🎉 所有示例运行完成!')
    print('=' * 80)


if __name__ == '__main__':
    main()
