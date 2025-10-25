# xtsqlorm

<div align="center">

**现代化的 Python SQLAlchemy ORM 框架**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![SQLAlchemy](https://img.shields.io/badge/sqlalchemy-2.0%2B-red.svg)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

[English](README.en.md) | 简体中文

</div>

---

## ✨ 特性

### 🏗️ 现代化架构

-   ✅ **SOLID 原则**: 接口清晰，职责分明
-   ✅ **依赖注入**: ConnectionManager → SessionProvider → Repository
-   ✅ **异步支持**: 完整的异步架构实现
-   ✅ **类型安全**: 100% 类型注解覆盖

### 🚀 高性能

-   ✅ **连接池管理**: 自动连接池优化
-   ✅ **批量操作**: `bulk_create`, `bulk_update` 高效处理
-   ✅ **查询缓存**: 内置 LRU 缓存支持
-   ✅ **分页查询**: 优化的分页实现

### 🛡️ 数据安全

-   ✅ **数据验证**: 集成 Pydantic 验证
-   ✅ **软删除**: 内置软删除支持
-   ✅ **乐观锁**: 版本控制防止并发冲突
-   ✅ **事务管理**: 自动事务回滚

### 🔧 易用性

-   ✅ **Repository 模式**: 简化 CRUD 操作
-   ✅ **Mixin 扩展**: 时间戳、软删除、版本控制
-   ✅ **表反射**: 动态映射数据库表
-   ✅ **丰富示例**: 8+ 完整示例代码

---

## 📦 安装

### 基础安装

```bash
pip install xtsqlorm
```

### 开发环境安装

```bash
# 克隆仓库
git clone https://gitee.com/sandorn/xtsqlorm.git
cd xtsqlorm

# 安装依赖 (使用 uv)
uv sync

# 或使用 pip
pip install -e ".[dev]"
```

### 可选依赖

```bash
# 异步支持 (MySQL)
pip install aiomysql

# 数据验证
pip install pydantic

# 数据导出
pip install pandas

# 日志增强
pip install xtlog
```

---

## 🚀 快速开始

### 1. 配置数据库

```python
# xtsqlorm/cfg.py
DB_Config = {
    'default': {
        'driver': 'mysql+pymysql',
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'your_password',
        'database': 'your_database',
        'charset': 'utf8mb4',
        'pool_size': 5,
        'max_overflow': 10,
    }
}
```

### 2. 定义模型

```python
from xtsqlorm import BaseModel, IdMixin, TimestampMixin
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

class User(BaseModel, IdMixin, TimestampMixin):
    __tablename__ = 'users'

    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
```

### 3. 基础 CRUD 操作

```python
from xtsqlorm import create_repository

# 创建仓储
user_repo = create_repository(User, db_key='default')

# 创建
user = user_repo.create({
    'username': 'john_doe',
    'email': 'john@example.com',
    'phone': '13800138000'
})

# 查询
user = user_repo.get_by_id(1)
all_users = user_repo.get_all(limit=10)

# 更新
updated_user = user_repo.update(1, {'email': 'new@example.com'})

# 删除
user_repo.delete(1)
```

### 4. 高级功能

```python
from xtsqlorm import create_orm_operations

# 创建 ORM 操作对象 (带验证和缓存)
ops = create_orm_operations(User, db_key='default', cache_enabled=True)

# 分页查询
users, total = ops.get_paginated(page=1, per_page=10)

# 批量创建
users = ops.bulk_create([
    {'username': 'user1', 'email': 'user1@example.com'},
    {'username': 'user2', 'email': 'user2@example.com'},
])

# 字段统计
stats = ops.get_field_stats('created_at')

# 导出数据
df = ops.export_to_dataframe(limit=100)
```

### 5. 异步操作

```python
import asyncio
from xtsqlorm import create_async_repository

async def main():
    # 创建异步仓储
    async_repo = create_async_repository(User, db_key='default')

    # 异步查询
    users = await async_repo.get_all(limit=10)
    user = await async_repo.get_by_id(1)

    # 异步创建
    new_user = await async_repo.create({
        'username': 'async_user',
        'email': 'async@example.com'
    })

asyncio.run(main())
```

---

## 📚 核心组件

### Repository (仓储模式)

```python
from xtsqlorm import Repository, IRepository

class UserRepository(Repository[User]):
    """用户仓储 - 标准 CRUD 操作"""

    def find_by_username(self, username: str) -> User | None:
        """自定义查询方法"""
        with self._session_provider.transaction() as session:
            return session.query(self._model).filter_by(username=username).first()
```

### Mixins (模型扩展)

```python
from xtsqlorm import (
    IdMixin,           # 主键 ID
    TimestampMixin,    # 创建/更新时间
    SoftDeleteMixin,   # 软删除
    VersionedMixin,    # 乐观锁版本控制
    UTCTimeMixin,      # UTC 时间戳
)

class Article(BaseModel, IdMixin, TimestampMixin, SoftDeleteMixin, VersionedMixin):
    __tablename__ = 'articles'

    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
```

### 自定义类型

```python
from xtsqlorm import JsonEncodedDict, EnumType, UTCDateTime

class Config(BaseModel):
    __tablename__ = 'configs'

    # JSON 字段
    settings: Mapped[dict] = mapped_column(JsonEncodedDict)

    # 枚举字段
    status: Mapped[str] = mapped_column(EnumType('active', 'inactive'))

    # UTC 时间字段
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
```

### 数据验证

```python
from pydantic import BaseModel as PydanticModel, field_validator
from xtsqlorm import create_orm_operations, validate_email, validate_phone

class UserValidator(PydanticModel):
    username: str
    email: str
    phone: str

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        return validate_email(v, 'email')

    @field_validator('phone')
    @classmethod
    def validate_phone_format(cls, v: str) -> str:
        return validate_phone(v, 'phone')

# 使用验证
ops = create_orm_operations(User, db_key='default', validator_model=UserValidator)
```

---

## 🏗️ 架构设计

### 架构层次

```
┌─────────────────────────────────────────────┐
│          Application Layer                  │
│  (Controller / Service / Business Logic)    │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│        ORM Operations Layer                 │
│  (OrmOperations / AsyncOrmOperations)       │
│  - Data Validation                          │
│  - Query Caching                            │
│  - Advanced Features                        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         Repository Layer                    │
│  (Repository / AsyncRepository)             │
│  - CRUD Operations                          │
│  - Transaction Management                   │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│       Session Provider Layer                │
│  (SessionProvider / AsyncSessionProvider)   │
│  - Session Lifecycle                        │
│  - Transaction Context                      │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│     Connection Manager Layer                │
│  (ConnectionManager / AsyncConnectionManager)│
│  - Connection Pool                          │
│  - Engine Management                        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│          Database Layer                     │
│  (MySQL / PostgreSQL / SQLite)              │
└─────────────────────────────────────────────┘
```

### 核心原则

-   **依赖倒置**: 依赖抽象接口而非具体实现
-   **单一职责**: 每个组件只负责一个功能
-   **开闭原则**: 对扩展开放，对修改封闭
-   **组合优于继承**: 使用组合模式构建功能

---

## 📖 文档

-   [完整 API 文档](docs/API.md)
-   [架构设计文档](docs/ARCHITECTURE.md)
-   [示例代码](examples/)
-   [变更日志](CHANGELOG.md)
-   [贡献指南](CONTRIBUTING.md)

---

## 🧪 示例代码

项目包含 8+ 完整示例，涵盖所有核心功能：

| 示例文件                            | 功能说明              |
| ----------------------------------- | --------------------- |
| `example_01_basic_sync.py`          | 基础同步 CRUD 操作    |
| `example_02_advanced_operations.py` | 高级查询和批量操作    |
| `example_03_table_reflection.py`    | 表反射和动态模型      |
| `example_04_mixins_and_types.py`    | Mixin 和自定义类型    |
| `example_05_data_validation.py`     | 数据验证和 Pydantic   |
| `example_06_transactions.py`        | 事务管理和 UnitOfWork |
| `example_07_complete_workflow.py`   | 完整用户管理流程      |
| `example_08_table_management.py`    | 表管理工具            |
| `examples_async.py`                 | 异步操作完整示例      |

运行示例：

```bash
# 使用 uv (推荐)
uv run python examples/example_01_basic_sync.py

# 或使用 python
python examples/example_01_basic_sync.py
```

---

## 🧪 测试

```bash
# 运行所有测试
pytest

# 查看测试覆盖率
pytest --cov=xtsqlorm --cov-report=html

# 运行类型检查
basedpyright xtsqlorm/

# 代码质量检查
ruff check xtsqlorm/ examples/
```

---

## 🤝 贡献

我们欢迎所有形式的贡献！请阅读 [贡献指南](CONTRIBUTING.md) 了解详情。

### 快速开始贡献

1. Fork 本仓库
2. 创建特性分支: `git checkout -b feature/amazing-feature`
3. 提交更改: `git commit -m 'Add amazing feature'`
4. 推送分支: `git push origin feature/amazing-feature`
5. 提交 Pull Request

---

## 📝 变更日志

详见 [CHANGELOG.md](CHANGELOG.md)

### 最新版本 v0.1.0 (2025-10-25)

**新增**:

-   ✨ 完整的异步架构实现
-   ✨ 代码质量优化 (Ruff + basedPyright)
-   ✨ 增强的数据验证器

**修复**:

-   🐛 异步资源泄漏问题
-   🐛 类型检查错误
-   🐛 全角标点符号规范

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 💖 致谢

感谢以下开源项目：

-   [SQLAlchemy](https://www.sqlalchemy.org/) - 强大的 Python SQL 工具包
-   [Pydantic](https://pydantic-docs.helpmanual.io/) - 数据验证
-   [Ruff](https://github.com/astral-sh/ruff) - 代码质量工具
-   [basedPyright](https://github.com/DetachHead/basedpyright) - 类型检查

---

## 📮 联系方式

-   **作者**: sandorn
-   **邮箱**: sandorn@live.cn
-   **仓库**: [Gitee](https://gitee.com/sandorn/xtsqlorm) | [GitHub](https://github.com/sandorn/xtsqlorm)

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐ Star！**

Made with ❤️ by sandorn

</div>
