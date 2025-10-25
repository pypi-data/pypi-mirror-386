# 示例代码转换为可执行代码总结

## 📅 完成日期

2025-10-24

## 🎯 目标

将所有示例中以 `print()` 打印形式展示的"仅演示"代码转换为实际可执行的测试代码。

---

## ✅ 已转换的示例

### 1. example_03_table_reflection.py

**位置**: 示例 2 - 获取或创建表模型

**修复前** ❌:

```python
print('\n【方式2: 复制表结构】（仅演示,不实际执行）')
print('   # NewUserModel = get_or_create_table_model(')
print('   #     source_table_name="users",')
# ... 注释掉的代码
```

**修复后** ✅:

```python
print('\n【方式2: 复制表结构到临时表】')
try:
    temp_table_name = 'users_temp_copy'
    # 创建临时表用于演示
    NewUserModel = get_or_create_table_model(
        source_table_name='users',
        db_conn=conn_mgr,
        new_table_name=temp_table_name,
    )
    # 清理临时表
    ...
```

**改进点**:

-   ✅ 实际执行表复制操作
-   ✅ 使用临时表名避免冲突
-   ✅ 自动清理测试数据
-   ✅ 错误处理友好提示

---

### 2. example_02_advanced_operations.py

**位置**: 示例 4 - 批量操作

**修复前** ❌:

```python
print('批量操作示例 (仅演示代码):')
print('   # users = ops.bulk_create([...')
print('   # updated_count = ops.bulk_update([...')
```

**修复后** ✅:

```python
print('批量操作示例 (实际执行):')
try:
    timestamp = int(time.time())

    # 批量创建（使用时间戳避免冲突）
    users_data = [
        {'username': f'batch_user1_{timestamp}', ...},
        {'username': f'batch_user2_{timestamp}', ...},
    ]
    created_users = ops.bulk_create(users_data)

    # 批量更新
    update_data = [...]
    updated_count = ops.bulk_update(update_data)

    # 清理测试数据
    for user in created_users:
        ops.delete(user.id)
```

**改进点**:

-   ✅ 实际执行批量创建和更新
-   ✅ 使用时间戳生成唯一用户名
-   ✅ 自动清理所有测试数据
-   ✅ 完整的错误处理

---

### 3. example_01_basic_sync.py

**位置**: 示例 3 - 完整的 CRUD 操作

**修复前** ❌:

```python
print('\n【创建操作】')
print('   # new_user = user_repo.create({...')

print('\n【更新操作】')
print('   # updated_user = user_repo.update(...')

print('\n【删除操作】')
print('   # deleted = user_repo.delete(...')
```

**修复后** ✅:

```python
print('\n【创建操作】')
try:
    timestamp = int(time.time())
    new_user = user_repo.create({
        'username': f'demo_user_{timestamp}',
        ...
    })
    created_id = new_user.id
    print(f'✅ 创建成功: ID={created_id}')
except Exception as e:
    print(f'⚠️  创建失败: {e}')

print('\n【更新操作】')
if created_id:
    updated_user = user_repo.update(created_id, {...})
    print(f'✅ 更新成功')

print('\n【删除操作】')
if created_id:
    deleted = user_repo.delete(created_id)
    print(f'✅ 删除成功')
```

**改进点**:

-   ✅ 实际执行 CREATE, UPDATE, DELETE
-   ✅ 完整的错误处理
-   ✅ 条件执行（只有创建成功才更新/删除）
-   ✅ 自动清理测试数据

---

### 4. example_05_data_validation.py

**位置**: 示例 2 - Pydantic 数据验证

**修复前** ❌:

```python
print('示例（不实际执行）:')
print('   # 有效数据')
print('   # ops.create({...')
print('   # 无效数据')
print('   # ops.create({...')  # ❌ 验证失败
```

**修复后** ✅:

```python
# 测试有效数据
print('【测试有效数据】')
try:
    valid_user = ops.create({
        'username': f'valid_user_{timestamp}',
        ...
    })
    print(f'✅ 验证通过，创建成功')
    ops.delete(valid_user.id)  # 清理
except Exception as e:
    print(f'⚠️  操作失败: {e}')

# 测试无效数据
print('\n【测试无效数据】')
try:
    invalid_user = ops.create({
        'username': 'ab',  # 太短
        ...
    })
    print(f'❌ 意外：验证应该失败')
except ValueError as e:
    print(f'✅ 验证失败（符合预期）: {e}')
```

**改进点**:

-   ✅ 实际测试有效和无效数据
-   ✅ 验证 Pydantic 验证器功能
-   ✅ 自动清理测试数据
-   ✅ 区分预期错误和意外错误

---

### 5. example_06_transactions.py

**位置**: 示例 3 和 示例 4

#### 示例 3: UnitOfWork

**修复前** ❌:

```python
print('示例代码（不实际执行复杂操作）:')
print('   with UnitOfWork(provider) as uow:')
print('       user_repo = uow.repository(User)')
```

**修复后** ✅:

```python
print('【实际执行示例】')
with UnitOfWork(session_provider) as uow:
    users_repo = uow.repository(UserModel)
    total_users = uow.session.query(UserModel).count()
    print(f'✅ 用户总数: {total_users}')
```

#### 示例 4: 复杂事务场景

**修复前** ❌:

```python
print('示例代码（不实际执行）:')
print('   with session_provider.transaction() as session:')
print('       user = user_repo.create_in_session({...}, session)')
```

**修复后** ✅:

```python
print('【实际执行示例】')
try:
    with session_provider.transaction() as session:
        # 1. 创建用户
        user = user_repo.create_in_session({...}, session)
        # 2. 创建用户资料
        profile = profile_repo.create_in_session({...}, session)
    # 清理测试数据
    ...
except Exception as e:
    print(f'⚠️  操作失败（可能表不存在）: {e}')
```

**改进点**:

-   ✅ 实际执行事务操作
-   ✅ 演示事务的原子性
-   ✅ 友好的错误提示（表不存在）
-   ✅ 自动清理测试数据

---

### 6. example_07_complete_workflow.py

**位置**: UserService.register 方法

**修复前** ❌:

```python
# 创建用户（示例，不实际执行）
print(f'准备创建用户: {data.username}')
# 实际代码:
# user_data = {...}
# user = self.user_ops.create(user_data)

return {
    'username': data.username,
    'message': '注册成功（模拟）',
}
```

**修复后** ✅:

```python
# 创建用户（实际执行）
print(f'准备创建用户: {data.username}')

user_data = {
    'username': data.username,
    'email': data.email,
    'password': self.hash_password(data.password),
    ...
}
user = self.user_ops.create(user_data)

return {
    'id': user.id,
    'username': data.username,
    'message': '注册成功',  # 不再是"模拟"
}
```

**改进点**:

-   ✅ 实际创建用户
-   ✅ 返回真实的用户 ID
-   ✅ 在 example_complete_workflow() 中添加清理逻辑
-   ✅ 使用时间戳避免用户名冲突

---

## 🔑 关键改进

### 1. 使用时间戳避免冲突

所有创建操作都使用时间戳生成唯一标识符：

```python
import time
timestamp = int(time.time())

username = f'test_user_{timestamp}'
email = f'test_{timestamp}@example.com'
```

### 2. 自动清理测试数据

每个测试都在完成后清理创建的数据：

```python
# 执行测试
created_user = ops.create({...})

# 测试逻辑
...

# 清理
ops.delete(created_user.id)
```

### 3. 完整的错误处理

使用 try-except 处理可能的错误：

```python
try:
    # 测试代码
    ...
except Exception as e:
    print(f'⚠️  操作失败: {e}')
```

### 4. 友好的提示信息

当操作可能失败时，提供友好的说明：

```python
except Exception as e:
    print(f'⚠️  操作失败（可能表不存在）: {e}')
    print('   说明: 此示例需要 user_profiles 表存在')
```

---

## 📊 转换统计

| 示例文件                          | 转换的部分 | 状态 |
| --------------------------------- | ---------- | ---- |
| example_01_basic_sync.py          | 3 处 CRUD  | ✅   |
| example_02_advanced_operations.py | 批量操作   | ✅   |
| example_03_table_reflection.py    | 表复制     | ✅   |
| example_05_data_validation.py     | 数据验证   | ✅   |
| example_06_transactions.py        | 2 处事务   | ✅   |
| example_07_complete_workflow.py   | 用户注册   | ✅   |

**总计**: 6 个文件, 9 处转换 ✅

---

## 🎯 测试验证

### 测试命令

```bash
# 测试单个示例
uv run python examples/example_01_basic_sync.py
uv run python examples/example_02_advanced_operations.py
uv run python examples/example_03_table_reflection.py
uv run python examples/example_05_data_validation.py
uv run python examples/example_06_transactions.py
uv run python examples/example_07_complete_workflow.py

# 批量测试
uv run python examples/test_all_examples.py
```

### 预期结果

-   ✅ 所有示例都应该实际执行测试代码
-   ✅ 测试数据应该被自动清理
-   ✅ 错误应该有友好的提示信息
-   ✅ 不应该在数据库中留下垃圾数据

---

## 💡 最佳实践

### 1. 编写可执行的示例

-   ❌ **错误**: 只打印代码不执行
-   ✅ **正确**: 实际执行代码并展示结果

### 2. 数据隔离

-   ❌ **错误**: 硬编码用户名，容易冲突
-   ✅ **正确**: 使用时间戳或 UUID 生成唯一标识

### 3. 清理测试数据

-   ❌ **错误**: 测试后不清理，污染数据库
-   ✅ **正确**: 自动删除所有测试创建的数据

### 4. 错误处理

-   ❌ **错误**: 让程序崩溃
-   ✅ **正确**: 捕获异常并提供友好提示

---

## ✅ 总结

所有示例中的"仅演示"代码都已转换为实际可执行的测试代码：

-   ✅ **9 处转换完成**
-   ✅ **自动清理测试数据**
-   ✅ **完整的错误处理**
-   ✅ **友好的用户体验**
-   ✅ **真实的功能演示**

现在所有示例都可以直接运行，并且会实际展示功能，而不仅仅是打印代码！

---

**完成时间**: 2025-10-24 21:10  
**修复类型**: 示例代码增强  
**测试状态**: ⏳ 待验证
