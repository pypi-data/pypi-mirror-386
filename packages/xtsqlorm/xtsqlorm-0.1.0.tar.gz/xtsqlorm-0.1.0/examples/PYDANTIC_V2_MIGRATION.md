# Pydantic V2 迁移修复总结

## 📅 修复日期

2025-10-24 23:55

## 🐛 发现的问题

### 1. **弃用的 `@validator` 装饰器**

**问题描述**:

-   使用了 Pydantic V1 风格的 `@validator` 装饰器
-   Pydantic V2 要求使用 `@field_validator`
-   产生弃用警告: `Pydantic V1 style '@validator' validators are deprecated`

**问题代码**:

```python
from pydantic import validator

class UserValidator(PydanticModel):
    @validator('phone')
    def validate_phone_number(cls, v):
        ...
```

### 2. **弃用的 `.dict()` 方法**

**问题描述**:

-   Pydantic V1 的 `.dict()` 方法已被弃用
-   Pydantic V2 使用 `.model_dump()` 替代

**问题代码**:

```python
user = UserValidator(**data)
print(user.dict())  # Pydantic V1
```

### 3. **`EmailStr` 需要额外依赖**

**问题描述**:

-   使用 `EmailStr` 类型需要安装 `email-validator` 包
-   错误: `ImportError: email-validator is not installed`

**问题代码**:

```python
from pydantic import EmailStr

class UserValidator(PydanticModel):
    email: EmailStr  # 需要 email-validator 依赖
```

### 4. **验证器函数参数错误**

**问题描述**:

-   `validate_length` 使用了错误的参数名 (`min_length`/`max_length` 而不是 `min_len`/`max_len`)
-   `validate_range` 使用了错误的参数名 (`min_value`/`max_value` 而不是 `min_val`/`max_val`)
-   `validate_datetime` 接受字符串而不是 datetime 对象

---

## 🔧 修复方案

### 1. 迁移到 `@field_validator`

**修复前** ❌:

```python
from pydantic import validator

class UserValidator(PydanticModel):
    @validator('phone')
    def validate_phone_number(cls, v):
        if v and not v.isdigit():
            raise ValueError('手机号必须是数字')
        return v
```

**修复后** ✅:

```python
from pydantic import field_validator

class UserValidator(PydanticModel):
    @field_validator('phone')
    @classmethod
    def validate_phone_number(cls, v):
        if v and not v.isdigit():
            raise ValueError('手机号必须是数字')
        return v
```

**关键变更**:

-   ✅ `@validator` → `@field_validator`
-   ✅ 添加 `@classmethod` 装饰器 (Pydantic V2 要求)
-   ✅ 导入语句从 `validator` 改为 `field_validator`

### 2. 迁移到 `.model_dump()`

**修复前** ❌:

```python
user = UserValidator(**data)
print(user.dict())
```

**修复后** ✅:

```python
user = UserValidator(**data)
print(user.model_dump())
```

### 3. 替换 `EmailStr` 为自定义验证

**修复前** ❌:

```python
from pydantic import EmailStr

class UserValidator(PydanticModel):
    email: EmailStr
```

**修复后** ✅:

```python
import re
from pydantic import field_validator

class UserValidator(PydanticModel):
    email: str

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        if not v:
            raise ValueError('邮箱不能为空')
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('邮箱格式无效')
        return v
```

### 4. 修复验证器函数调用

**修复前** ❌:

```python
# validate_length - 参数名错误
validate_length('testuser', '用户名', min_length=3, max_length=50)

# validate_range - 参数名错误
validate_range(25, '年龄', min_value=0, max_value=150)

# validate_datetime - 类型错误
validate_datetime(datetime.now(), '创建时间')
```

**修复后** ✅:

```python
# validate_length - 正确的参数名
validate_length('testuser', min_len=3, max_len=50, field='用户名')

# validate_range - 正确的参数名
validate_range(25, min_val=0, max_val=150, field='年龄')

# validate_datetime - 传递字符串
validate_datetime(datetime.now().isoformat(), field='创建时间')
```

---

## 📊 修复统计

| 问题类型                          | 修复数量      | 状态 |
| --------------------------------- | ------------- | ---- |
| `@validator` → `@field_validator` | 3 处          | ✅   |
| `.dict()` → `.model_dump()`       | 1 处          | ✅   |
| `EmailStr` → 自定义验证           | 1 处          | ✅   |
| 验证器函数参数修复                | 6 处          | ✅   |
| **总计**                          | **11 处修复** | ✅   |

---

## 🧪 测试验证

### 测试结果

```bash
uv run python test_validator_fix.py
```

```
✅ 测试 1: 有效数据 - 通过
✅ 测试 2: 邮箱无效 - 验证失败(符合预期)
✅ 测试 3: 密码无效 - 验证失败(符合预期)

🎉 测试完成!
```

**状态**: ✅ 全部通过，无弃用警告

---

## 💡 Pydantic V2 迁移要点

### 主要变更

1. **验证器装饰器**:

    - `@validator` → `@field_validator`
    - 必须添加 `@classmethod` 装饰器

2. **模型方法**:

    - `.dict()` → `.model_dump()`
    - `.json()` → `.model_dump_json()`
    - `.parse_obj()` → `.model_validate()`

3. **类型注解**:
    - 某些特殊类型(如 `EmailStr`)需要额外依赖
    - 可以使用自定义 `@field_validator` 替代

### 迁移检查清单

-   ✅ 替换所有 `@validator` 为 `@field_validator`
-   ✅ 为所有验证器方法添加 `@classmethod`
-   ✅ 替换 `.dict()` 为 `.model_dump()`
-   ✅ 检查特殊类型的依赖(如 `EmailStr` 需要 `email-validator`)
-   ✅ 更新导入语句: `from pydantic import field_validator`

---

## 📚 参考资源

-   [Pydantic V2 迁移指南](https://docs.pydantic.dev/latest/migration/)
-   [Field Validators 文档](https://docs.pydantic.dev/latest/concepts/validators/)
-   [Model Serialization 文档](https://docs.pydantic.dev/latest/concepts/serialization/)

---

## ✅ 总结

**修复前**:

-   ❌ 使用 Pydantic V1 的 `@validator`
-   ❌ 使用弃用的 `.dict()` 方法
-   ❌ `EmailStr` 依赖缺失
-   ❌ 验证器函数参数错误

**修复后**:

-   ✅ 迁移到 Pydantic V2 的 `@field_validator`
-   ✅ 使用 `.model_dump()` 方法
-   ✅ 自定义邮箱验证，无额外依赖
-   ✅ 修正所有验证器函数调用
-   ✅ 无弃用警告
-   ✅ 测试全部通过

---

**完成时间**: 2025-10-24 23:55  
**修复类型**: Pydantic V2 迁移 + 验证器函数修复  
**影响范围**: example_05_data_validation.py  
**测试状态**: ✅ 全部通过，无弃用警告
