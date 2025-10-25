# table_utils.py 新架构适配说明

> **更新时间**: 2025-10-24
>
> **适配版本**: 扁平化架构重构后

---

## 📋 更新概览

`table_utils.py` 已成功适配新的扁平化架构，主要变更：

1. ✅ 使用新的 `ConnectionManager` 替代旧的 `SqlConnection`
2. ✅ 调用新的工厂函数 `create_connection_manager`
3. ⚠️ 异步功能 `reflect_table_async` 暂时抛出 `NotImplementedError`
4. ✅ 示例文件已更新并通过测试

---

## 🔧 核心变更

### 1. 导入变更

**旧版本**:

```python
if TYPE_CHECKING:
    from .connection import AsyncSqlConnection, SqlConnection
```

**新版本**:

```python
if TYPE_CHECKING:
    from .engine import ConnectionManager

    # 注意: 异步部分暂未完全整合到新架构,保留类型引用
    AsyncSqlConnection = Any
```

### 2. 函数签名变更

**旧版本**:

```python
def get_or_create_table_model(
    source_table_name: str,
    db_conn: SqlConnection | None = None,
    new_table_name: str | None = None,
    table_args: dict[str, Any] | None = None,
    **conn_kwargs: Any,
) -> type[BaseModel]:
    from xtsqlorm.factory import create_sqlconnection

    if db_conn is None:
        db_conn = create_sqlconnection(**conn_kwargs)
```

**新版本**:

```python
def get_or_create_table_model(
    source_table_name: str,
    db_conn: ConnectionManager | None = None,
    new_table_name: str | None = None,
    table_args: dict[str, Any] | None = None,
    **conn_kwargs: Any,
) -> type[BaseModel]:
    from xtsqlorm.factory import create_connection_manager

    if db_conn is None:
        db_conn = create_connection_manager(**conn_kwargs)
```

### 3. 异步功能状态

`reflect_table_async` 函数已更新为抛出明确的 `NotImplementedError`：

```python
async def reflect_table_async(
    source_table_name: str,
    db_conn: Any | None = None,
    **conn_kwargs: Any,
) -> type[BaseModel]:
    """
    ⚠️ 注意: 此函数暂未完全整合到新架构中,异步连接管理功能待实现。
    建议使用同步版本 reflect_table() 代替。
    """
    raise NotImplementedError(
        '异步反射功能暂未完全整合到新架构中。\n'
        '新架构计划:\n'
        '  - 创建 AsyncConnectionManager\n'
        '  - 创建 AsyncSessionProvider\n'
        '  - 创建 AsyncRepository\n'
        '请使用同步版本 reflect_table() 代替,或等待异步架构完善。'
    )
```

---

## 📚 可用函数

### ✅ 完全可用

| 函数                          | 说明                           | 状态        |
| ----------------------------- | ------------------------------ | ----------- |
| `get_or_create_table_model()` | 智能获取或创建表模型(两种模式) | ✅ 已适配   |
| `reflect_table()`             | 同步反射表结构                 | ✅ 已适配   |
| `generate_model_file()`       | 生成模型文件                   | ✅ 已适配   |
| `validate_sql_identifier()`   | 验证 SQL 标识符                | ✅ 无需改动 |
| `build_safe_command_args()`   | 构建安全命令参数               | ✅ 无需改动 |
| `execute_command_safely()`    | 安全执行命令                   | ✅ 无需改动 |

### ⚠️ 待实现

| 函数                    | 说明           | 状态        |
| ----------------------- | -------------- | ----------- |
| `reflect_table_async()` | 异步反射表结构 | ⚠️ 暂不可用 |

---

## 💡 使用示例

### 示例 1: 反射表模型

```python
from xtsqlorm import reflect_table

# 反射现有表
user_model = reflect_table('users', db_key='default')
print(f'表名: {user_model.__tablename__}')
print(f'列数: {len(user_model.__table__.columns)}')
```

### 示例 2: 复制表结构

```python
from xtsqlorm import get_or_create_table_model

# 复制表结构创建新表
backup_model = get_or_create_table_model(
    'users',
    new_table_name='users_backup',
    db_key='default'
)
```

### 示例 3: 使用新架构创建 ORM 操作

```python
from xtsqlorm import create_orm_operations, reflect_table

# 1. 反射表模型
user_model = reflect_table('users', db_key='default')

# 2. 创建ORM操作对象
ops = create_orm_operations(user_model, db_key='default')

# 3. 使用高级功能
results, total = ops.get_paginated(page=1, page_size=10)
count = ops.count()
```

### 示例 4: 使用工作单元模式

```python
from xtsqlorm import UnitOfWork, create_session_provider, reflect_table

# 1. 创建会话提供者
provider = create_session_provider(db_key='default')

# 2. 反射表模型
user_model = reflect_table('users', db_key='default')
order_model = reflect_table('orders', db_key='default')

# 3. 使用工作单元管理复杂事务
with UnitOfWork(provider) as uow:
    user_repo = uow.repository(user_model)
    order_repo = uow.repository(order_model)

    # 在同一事务中操作多个表
    user = user_repo.get_by_id_in_session(1, uow.session)
    order = order_repo.create_in_session({
        'user_id': user.id,
        'amount': 100
    }, uow.session)
    # 自动提交所有更改
```

---

## 🚀 运行示例

完整示例文件: `examples/examples_table_utils.py`

运行方式:

```bash
python examples/examples_table_utils.py
```

示例包含:

1. ✅ get_or_create_table_model - 智能表模型管理
2. ✅ generate_model_file - 生成静态模型文件
3. ✅ reflect_table - 同步反射表结构
4. ✅ 新架构 - 使用工厂函数创建 ORM 操作
5. ℹ️ 异步功能状态说明

---

## 📈 测试结果

**测试时间**: 2025-10-24 16:09

**测试环境**:

-   Python: 3.12+
-   SQLAlchemy: 2.x
-   数据库: MySQL
-   测试表: `users2`

**测试结果**:

-   ✅ 所有同步功能正常工作
-   ✅ 新架构三种使用方式验证通过
-   ✅ 工作单元模式事务管理正常
-   ✅ 查询操作成功（用户总数: 10）

**示例输出**:

```
✅ 反射模型: Users2 | 表名: users2
   列数: 9
   列名: ['id', 'name', 'phone', 'agent_code', 'member_level', ...]

✅ 备份模型: Users2Backup | 表名: users2_backup
   列数: 9

✅ 模型文件已生成
✅ 创建连接管理器: ConnectionManager(...)
✅ 创建会话提供者: SessionProvider(...)
✅ 创建仓储: Repository[Users2]
✅ 用户总数: 10
✅ 查询前5个用户: 共 5 条
✅ 工作单元事务已提交
```

---

## 🔮 未来计划

### 异步架构支持

异步功能将在以下组件完成后重新实现:

1. **AsyncConnectionManager** - 异步连接引擎管理

    - 异步连接池管理
    - 异步连接测试
    - 异步资源释放

2. **AsyncSessionProvider** - 异步会话提供者

    - 异步 Session 创建
    - 异步事务管理
    - 异步上下文管理器

3. **AsyncRepository** - 异步仓储

    - 异步 CRUD 操作
    - 异步批量查询
    - 异步外部事务支持

4. **reflect_table_async** - 异步反射
    - 重新实现异步表反射
    - 使用 AsyncConnectionManager
    - 完整异步链路支持

---

## 📚 相关文档

-   [REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md) - 扁平化架构重构总结
-   [FLAT_ARCHITECTURE_PLAN.md](./architecture_review/FLAT_ARCHITECTURE_PLAN.md) - 详细重构方案
-   [ARCHITECTURE_ANALYSIS.md](./architecture_review/ARCHITECTURE_ANALYSIS.md) - 原架构分析

---

**结论**: `table_utils.py` 已成功适配新架构，所有同步功能正常工作！异步支持将在异步架构完善后实现。🎉
