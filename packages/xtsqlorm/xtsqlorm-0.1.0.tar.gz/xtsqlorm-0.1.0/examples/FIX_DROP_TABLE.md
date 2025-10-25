# 修复删除表错误 (code=1)

## 问题描述

在运行 `example_08_table_management.py` 时，删除表操作失败，导致程序退出 (exit code=1)。

## 根本原因

SQLAlchemy 2.0+ 要求在执行原生 SQL 时使用 `text()` 函数包装 SQL 字符串。

### 错误代码

```python
# ❌ 这样会报错
connection.execute(f'DROP TABLE IF EXISTS {table_name}')
```

### 修复后代码

```python
# ✅ 正确的方式
from sqlalchemy import text

connection.execute(text(f'DROP TABLE IF EXISTS {table_name}'))
```

## 已修复的内容

### 1. 导入 `text` 函数

```python
# 在文件顶部添加
from sqlalchemy import Column, Integer, String, inspect, text
```

### 2. 更新 `example_5_drop_table()` 函数

**修复前:**

```python
for table_name in test_tables:
    if inspector.has_table(table_name):
        with conn_mgr.engine.connect() as connection:
            connection.execute(f'DROP TABLE IF EXISTS {table_name}')  # ❌ 会报错
            connection.commit()
        print(f'   ✅ 已删除表: {table_name}')
```

**修复后:**

```python
for table_name in test_tables:
    if inspector.has_table(table_name):
        try:
            with conn_mgr.engine.connect() as connection:
                connection.execute(text(f'DROP TABLE IF EXISTS {table_name}'))  # ✅ 使用 text()
                connection.commit()
            print(f'   ✅ 已删除表: {table_name}')
        except Exception as e:
            print(f'   ❌ 删除表 {table_name} 失败: {e}')
```

## 改进点

1. **使用 `text()` 包装 SQL** - 符合 SQLAlchemy 2.0+ 规范
2. **添加异常处理** - 捕获可能的删除错误，不会导致整个程序崩溃
3. **更好的错误提示** - 显示具体的错误信息

## 运行示例

```bash
# 运行完整的表管理示例
python examples/example_08_table_management.py

# 或者单独测试删除功能
python -c "
from examples.example_08_table_management import example_5_drop_table
example_5_drop_table()
"
```

## 其他可能的解决方案

### 方案 1: 使用 SQLAlchemy Table 对象删除

```python
from sqlalchemy import MetaData, Table

metadata = MetaData()
table = Table(table_name, metadata, autoload_with=conn_mgr.engine)
table.drop(conn_mgr.engine, checkfirst=True)
```

### 方案 2: 使用模型的 **table** 属性

```python
model_class.__table__.drop(conn_mgr.engine, checkfirst=True)
```

### 方案 3: 使用 metadata.drop_all()

```python
# 删除所有表
Base.metadata.drop_all(conn_mgr.engine)
```

## 注意事项

⚠️ **生产环境警告**:

-   删除表是危险操作，会导致数据丢失
-   建议在生产环境中使用数据库迁移工具（如 Alembic）
-   始终先备份数据
-   考虑使用软删除（添加 deleted_at 字段）而不是直接删除表

## 相关资源

-   [SQLAlchemy 2.0 文档](https://docs.sqlalchemy.org/en/20/)
-   [SQLAlchemy text() 函数](https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.expression.text)
-   [Alembic 数据库迁移](https://alembic.sqlalchemy.org/)

---

**修复完成日期**: 2025-10-24
**修复文件**: `examples/example_08_table_management.py`
