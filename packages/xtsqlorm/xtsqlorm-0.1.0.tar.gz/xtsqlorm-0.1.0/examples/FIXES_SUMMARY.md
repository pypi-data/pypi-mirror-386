# 示例文件修复总结

## 📅 修复日期

2025-10-24

## 🐛 发现的问题

### 1. **方法不存在错误**: `get_all_in_session`

**影响文件**:

-   `example_01_basic_sync.py`
-   `example_06_transactions.py`

**错误信息**:

```
AttributeError: 'Repository' object has no attribute 'get_all_in_session'
```

**原因**:
`Repository` 类只有以下 `*_in_session` 方法:

-   `get_by_id_in_session`
-   `create_in_session`
-   `update_in_session`
-   `delete_in_session`

但**没有** `get_all_in_session` 方法。

**修复方案**:
在外部事务中，直接使用 `session.query(Model).limit(n).all()` 来查询数据。

**修复代码**:

```python
# 修复前 ❌
users = user_repo.get_all_in_session(limit=2, session=session)

# 修复后 ✅
users = session.query(UserModel).limit(2).all()
```

---

### 2. **导入路径错误**: `from examples.user import`

**影响文件**:

-   `example_05_data_validation.py`
-   `example_06_transactions.py`
-   `example_07_complete_workflow.py`

**错误信息**:

```
ModuleNotFoundError: No module named 'examples.user'
```

**原因**:
示例文件使用 `uv run python examples/example_xx.py` 运行时，工作目录在项目根目录，但实际模块路径是相对于 `examples/` 目录。

**修复方案**:
将所有 `from examples.user import` 改为 `from user import`。

**修复代码**:

```python
# 修复前 ❌
from examples.user import UserModel

# 修复后 ✅
from user import UserModel
```

---

### 3. **SQL text() 包装缺失**

**影响文件**:

-   `example_06_transactions.py`
-   `example_08_table_management.py`

**错误信息**:

```
sqlalchemy.exc.ArgumentError: Textual SQL expression '...' should be explicitly declared as text('...')
```

**原因**:
SQLAlchemy 2.0+ 要求所有原生 SQL 字符串必须用 `text()` 函数包装。

**修复方案**:

1. 导入 `text` 函数: `from sqlalchemy import text`
2. 包装所有原生 SQL: `text('SELECT ...')`

**修复代码**:

```python
# 修复前 ❌
result = session.execute('SELECT COUNT(*) FROM users')
connection.execute(f'DROP TABLE IF EXISTS {table_name}')

# 修复后 ✅
from sqlalchemy import text
result = session.execute(text('SELECT COUNT(*) FROM users'))
connection.execute(text(f'DROP TABLE IF EXISTS {table_name}'))
```

---

### 4. **UnitOfWork API 错误**

**影响文件**:

-   `example_06_transactions.py`

**错误信息**:

```
AttributeError: 'UnitOfWork' object has no attribute 'register_repository'
```

**原因**:
`UnitOfWork` 类的实际 API 是:

-   ✅ `repository(model)` - 获取仓储
-   ❌ `register_repository(name, model)` - 不存在

**修复方案**:
使用 `uow.repository(Model)` 来获取仓储，而不是预先注册。

**修复代码**:

```python
# 修复前 ❌
uow = UnitOfWork(session_provider)
uow.register_repository('users', UserModel)
with uow:
    users_repo = uow.get_repository('users')

# 修复后 ✅
with UnitOfWork(session_provider) as uow:
    users_repo = uow.repository(UserModel)
    # 直接使用 uow.session 进行查询
    total = uow.session.query(UserModel).count()
```

---

### 5. **数据库表不存在**

**影响文件**:

-   `example_06_transactions.py`

**错误信息**:

```
sqlalchemy.exc.ProgrammingError: (1146, "Table 'bxflb.user_profiles' doesn't exist")
```

**原因**:
示例代码尝试查询数据库中不存在的 `user_profiles` 表。

**修复方案**:

-   简化示例，只使用确实存在的表（如 `users`）
-   对于复杂场景，只展示代码而不实际执行

**修复代码**:

```python
# 修复前 ❌
total_profiles = uow.session.query(UserProfileModel).count()

# 修复后 ✅
# 方案1: 移除不存在的表查询
total_users = uow.session.query(UserModel).count()

# 方案2: 只展示代码示例
print('示例代码（不实际执行）:')
print('   profile_repo.create_in_session({...}, uow.session)')
```

---

## ✅ 修复的文件列表

| 文件                              | 修复问题                                                       | 状态      |
| --------------------------------- | -------------------------------------------------------------- | --------- |
| `example_01_basic_sync.py`        | get_all_in_session, 导入路径                                   | ✅ 通过   |
| `example_05_data_validation.py`   | 导入路径                                                       | ✅ 通过   |
| `example_06_transactions.py`      | get_all_in_session, 导入路径, text(), UnitOfWork API, 表不存在 | ✅ 通过   |
| `example_07_complete_workflow.py` | 导入路径                                                       | ⏳ 待测试 |
| `example_08_table_management.py`  | text()                                                         | ✅ 通过   |

---

## 🔧 如何验证修复

### 方法 1: 逐个测试

```bash
uv run python examples/example_01_basic_sync.py
uv run python examples/example_06_transactions.py
uv run python examples/example_08_table_management.py
```

### 方法 2: 批量测试

```bash
uv run python examples/test_all_examples.py
```

---

## 📚 学到的教训

1. **Repository API**:

    - 只有 `get_by_id_in_session`, `create_in_session`, `update_in_session`, `delete_in_session`
    - 没有 `get_all_in_session`
    - 查询列表使用 `session.query(Model).all()`

2. **UnitOfWork API**:

    - 使用 `uow.repository(Model)` 获取仓储
    - 使用 `uow.session` 访问当前事务的 session
    - 不需要预先注册仓储

3. **SQLAlchemy 2.0+**:

    - 所有原生 SQL 必须用 `text()` 包装
    - 导入: `from sqlalchemy import text`

4. **导入路径**:

    - 在 `examples/` 目录内运行时，使用 `from user import`
    - 不要使用 `from examples.user import`

5. **示例健壮性**:
    - 示例应该能在空数据库或最小数据库上运行
    - 对于不存在的表，使用代码展示而不是实际执行
    - 添加适当的错误处理和友好的提示信息

---

## 🎯 下一步

-   [ ] 测试所有其他示例文件
-   [ ] 创建自动化测试脚本
-   [ ] 更新 README 中的示例说明
-   [ ] 添加更多错误处理和友好提示

---

**修复完成日期**: 2025-10-24  
**修复人**: AI Assistant  
**测试状态**: ✅ 部分通过，继续测试中
