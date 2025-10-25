# xtsqlorm 架构分析报告

## 📋 目录

1. [当前设计分析](#当前设计分析)
2. [DB-API 2.0 规范对照](#db-api-20-规范对照)
3. [存在的问题](#存在的问题)
4. [优化建议](#优化建议)
5. [重构方案](#重构方案)

---

## 1. 当前设计分析

### 1.1 SqlConnection 类职责

**核心职责**（✅ 合理）:

-   数据库连接管理（Engine、URL、连接池）
-   Session 工厂创建和管理
-   底层连接测试（ping）
-   资源释放和清理

**扩展职责**（⚠️ 值得商榷）:

-   Session 实例管理（直接暴露 `self.session` 属性）
-   事务管理（commit/rollback/session_scope）
-   SQL 执行（execute_sql、execute_many）
-   连接池状态查询
-   数据库信息查询（datainfo）

### 1.2 OrmOperations 类职责

**核心职责**（✅ 合理）:

-   ORM 模型的 CRUD 操作
-   高级查询接口（过滤、排序、分页）
-   批量操作
-   数据验证（Pydantic 集成）
-   查询缓存

**扩展职责**（⚠️ 值得商榷）:

-   事务管理（session_scope、transaction_scope）
-   Session 管理（通过 self.db.session 直接访问）
-   SQL 执行（execute_raw_sql）
-   数据导出（export_to_dataframe）
-   统计分析（get_field_stats）

---

## 2. DB-API 2.0 规范对照

### 2.1 DB-API 2.0 核心要求

Python DB-API 2.0 (PEP 249) 定义了以下核心概念：

```python
# 标准DB-API 2.0结构
Connection  # 连接对象
  ├── cursor()      # 创建游标
  ├── commit()      # 提交事务
  ├── rollback()    # 回滚事务
  └── close()       # 关闭连接

Cursor      # 游标对象
  ├── execute()     # 执行SQL
  ├── executemany() # 批量执行
  ├── fetchone()    # 获取单行
  ├── fetchmany()   # 获取多行
  ├── fetchall()    # 获取所有行
  └── close()       # 关闭游标
```

### 2.2 当前实现与 DB-API 2.0 的对应关系

| DB-API 2.0              | xtsqlorm 当前实现              | 符合度                  |
| ----------------------- | ------------------------------ | ----------------------- |
| `Connection`            | `SqlConnection`                | ⚠️ 部分符合             |
| `Connection.cursor()`   | `SqlConnection.session`        | ❌ 概念不同             |
| `Connection.commit()`   | `SqlConnection.commit()`       | ✅ 符合                 |
| `Connection.rollback()` | `SqlConnection.rollback()`     | ✅ 符合                 |
| `Connection.close()`    | `SqlConnection.dispose()`      | ✅ 符合                 |
| `Cursor.execute()`      | `SqlConnection.execute_sql()`  | ⚠️ 混合在 Connection 中 |
| `Cursor.executemany()`  | `SqlConnection.execute_many()` | ⚠️ 混合在 Connection 中 |

**分析**:

-   ✅ **优点**: 事务管理（commit/rollback）符合标准
-   ❌ **问题**: SQLAlchemy 的 Session 概念与 DB-API 2.0 的 Cursor 不同，但混用了职责
-   ❌ **问题**: 将 Cursor 级别的 execute 操作放在了 Connection 级别

### 2.3 现代 ORM 设计模式对照

**Repository 模式** (推荐):

```
Repository (仓储层)
  ├── 封装数据访问逻辑
  ├── 提供业务友好的接口
  └── 隔离底层实现细节

Unit of Work (工作单元)
  ├── 管理事务边界
  ├── 跟踪对象变更
  └── 批量提交更改

Connection Pool (连接池)
  └── 纯粹的连接管理
```

**当前实现**:

-   `SqlConnection` = Connection Pool + Transaction Manager + Query Executor (职责混合)
-   `OrmOperations` = Repository + Transaction Manager (职责重复)

---

## 3. 存在的问题

### 3.1 🔴 严重问题

#### 问题 1: 职责重叠 - 事务管理双重实现

```python
# SqlConnection有session_scope
class SqlConnection:
    @contextlib.contextmanager
    def session_scope(self) -> Generator[Session]:
        session = self.new_session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
        finally:
            session.close()

# OrmOperations也有session_scope
class OrmOperations:
    @contextlib.contextmanager
    def session_scope(self, session: Session | None = None) -> Generator[Session]:
        external_session = session is not None
        current_session = session or self.db.session
        try:
            yield current_session
            if not external_session:
                current_session.commit()
        except:
            if not external_session:
                current_session.rollback()
        finally:
            if not external_session:
                current_session.close()
```

**问题**:

-   两个类都实现了相同的事务管理逻辑
-   OrmOperations 的实现更复杂（支持外部 session）
-   维护成本高，容易产生不一致

#### 问题 2: 紧耦合 - 直接访问内部状态

```python
class OrmOperations:
    @property
    def db(self) -> SqlConnection:
        if not self._db_conn:
            self._db_conn = SqlConnection()  # 直接创建依赖
        return self._db_conn

    def get_one(self, where_dict, session=None):
        session = session or self.db.session  # 直接访问session
        query = session.query(self._data_model)
        ...
```

**问题**:

-   `OrmOperations` 直接依赖 `SqlConnection` 的具体实现
-   违反依赖倒置原则（应依赖抽象接口）
-   难以进行单元测试和 mock
-   难以替换底层实现

#### 问题 3: Session 生命周期管理混乱

```python
# SqlConnection暴露全局session
@property
def session(self) -> Session:
    if self._session is None:
        self._session = self._scoped_session_factory()
    return self._session

# OrmOperations多处使用
session = session or self.db.session  # 使用全局session
session = self.db.new_session()       # 创建新session
```

**问题**:

-   全局 session 容易导致状态污染
-   不清楚何时应该使用全局 session，何时创建新 session
-   缺乏明确的 session 生命周期管理规范

### 3.2 🟡 中等问题

#### 问题 4: 单例模式的滥用

```python
class SqlConnection(metaclass=SingletonMeta):
    ...
```

**问题**:

-   单例模式限制了多数据库连接的灵活性
-   难以在测试中隔离不同的连接实例
-   不适合微服务和多租户场景

#### 问题 5: 缺乏抽象层

```python
# 没有定义数据库接口抽象
class SqlConnection:
    # 直接实现，无抽象
    pass

class OrmOperations:
    # 直接依赖具体类
    def __init__(self, data_model, db_conn: SqlConnection | None = None):
        ...
```

**问题**:

-   无法轻松切换不同的数据库实现
-   不符合"面向接口编程"原则
-   扩展性差

#### 问题 6: 异步与同步代码混用

```python
class AsyncSqlConnection:
    async def commit_async(self): ...

    def commit(self):  # 同步版本
        return self.run_sync([self.commit_async()])
```

**问题**:

-   同步方法内部调用异步方法，增加复杂度
-   容易导致事件循环问题
-   不符合"async 一路到底"的最佳实践

### 3.3 🟢 次要问题

#### 问题 7: 方法命名不一致

```python
# SqlConnection
def execute_sql(self, sql, params): ...
def execute_many(self, sql, params_list): ...

# OrmOperations
def execute_raw_sql(self, sql, params, session): ...
```

#### 问题 8: 缺乏连接上下文管理器的正确实现

```python
class SqlConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.cleanup_session(exc_val)
```

**问题**:

-   假设使用 with 语句就需要自动提交
-   不符合 session-per-request 模式
-   过于激进的自动提交可能导致意外行为

---

## 4. 优化建议

### 4.1 职责重新划分

#### 推荐架构:

```
层级1: 连接管理层 (ConnectionManager)
  ├── 职责: 纯粹的连接池管理、引擎创建、ping测试
  └── 不应包含: 事务管理、session管理、SQL执行

层级2: 会话管理层 (SessionManager / UnitOfWork)
  ├── 职责: Session生命周期、事务边界、commit/rollback
  └── 依赖: ConnectionManager

层级3: 仓储层 (Repository / OrmOperations)
  ├── 职责: 业务友好的CRUD接口、查询构建
  └── 依赖: SessionManager (通过抽象接口)

层级4: 工具层 (QueryBuilder, DataExporter)
  ├── 职责: SQL构建、数据导出、统计分析
  └── 独立工具类，按需组合
```

### 4.2 遵循 SOLID 原则

#### S - 单一职责原则 (Single Responsibility)

**当前**: SqlConnection 承担了 5 个职责
**建议**: 拆分为多个专职类

```python
# 连接管理 (唯一职责: 管理数据库连接)
class ConnectionManager:
    def create_engine(self, url, **kwargs) -> Engine: ...
    def ping(self) -> bool: ...
    def dispose(self) -> None: ...

# 会话工厂 (唯一职责: 创建Session)
class SessionFactory:
    def __init__(self, engine: Engine): ...
    def create_session(self) -> Session: ...

# 工作单元 (唯一职责: 管理事务边界)
class UnitOfWork:
    def __init__(self, session_factory: SessionFactory): ...

    @contextmanager
    def transaction(self):
        session = self._session_factory.create_session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
```

#### D - 依赖倒置原则 (Dependency Inversion)

**当前**: OrmOperations 直接依赖 SqlConnection 具体类
**建议**: 依赖抽象接口

```python
# 定义抽象接口
from abc import ABC, abstractmethod

class ISessionProvider(ABC):
    """会话提供者接口"""

    @abstractmethod
    def get_session(self) -> Session:
        """获取数据库会话"""
        pass

    @abstractmethod
    @contextmanager
    def transaction(self) -> Generator[Session, None, None]:
        """事务上下文管理器"""
        pass

# SqlConnection实现接口
class SqlConnection(ISessionProvider):
    def get_session(self) -> Session:
        return self._session_factory()

    @contextmanager
    def transaction(self):
        session = self.get_session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

# OrmOperations依赖接口
class OrmOperations[T]:
    def __init__(
        self,
        data_model: type[T],
        session_provider: ISessionProvider,  # 依赖抽象
    ):
        self._data_model = data_model
        self._session_provider = session_provider

    def get_by_id(self, id_value: int) -> T | None:
        with self._session_provider.transaction() as session:
            return session.get(self._data_model, id_value)
```

### 4.3 对齐 DB-API 2.0 精神

虽然 SQLAlchemy 不是严格的 DB-API 2.0 实现，但可以借鉴其设计理念：

```python
# Connection层: 只负责连接和事务
class DatabaseConnection:
    """对应 DB-API 2.0 的 Connection"""

    def __init__(self, url: str):
        self._engine = create_engine(url)

    def session(self) -> "SessionContext":
        """类似于 cursor()，返回会话上下文"""
        return SessionContext(self._engine)

    def commit(self): ...  # 全局事务提交
    def rollback(self): ...  # 全局事务回滚
    def close(self): ...  # 关闭连接

# Session层: 对应 Cursor，负责执行操作
class SessionContext:
    """对应 DB-API 2.0 的 Cursor"""

    def __init__(self, engine: Engine):
        self._session = Session(engine)

    def execute(self, sql, params=None): ...
    def query(self, model): ...
    def add(self, instance): ...
    def commit(self): ...
    def rollback(self): ...
    def close(self): ...

# ORM层: 高层封装，不接触底层细节
class Repository[T]:
    """业务层仓储，只关心模型操作"""

    def __init__(self, model: type[T], session: Session):
        self._model = model
        self._session = session

    def get_by_id(self, id_value: int) -> T | None:
        return self._session.get(self._model, id_value)

    def save(self, instance: T) -> T:
        self._session.add(instance)
        return instance
```

---

## 5. 重构方案

### 5.1 Phase 1: 引入抽象层（最小侵入）

#### 步骤 1: 定义接口协议

```python
# xtsqlorm/protocols.py
from typing import Protocol, Generator
from sqlalchemy.orm import Session

class SessionProvider(Protocol):
    """会话提供者协议"""

    def get_session(self) -> Session:
        """获取会话实例"""
        ...

    def transaction(self) -> Generator[Session, None, None]:
        """事务上下文管理器"""
        ...

class ConnectionManager(Protocol):
    """连接管理器协议"""

    @property
    def engine(self) -> Engine:
        """获取数据库引擎"""
        ...

    def ping(self) -> bool:
        """测试连接"""
        ...

    def dispose(self) -> None:
        """释放连接"""
        ...
```

#### 步骤 2: SqlConnection 实现收缩

```python
# xtsqlorm/connection.py (重构后)
class SqlConnection(ConnectionManager, SessionProvider):
    """数据库连接管理类 - 专注于连接和会话管理"""

    def __init__(self, db_key: str = 'default', url: str | None = None, **kwargs):
        if not url:
            url = connect_str(db_key)

        engine_config, session_config, _ = self._extract_engine_config(kwargs)
        self._engine = create_engine(url, **engine_config)
        self._session_factory = sessionmaker(bind=self._engine, **session_config)

    # ============ ConnectionManager 接口实现 ============
    @property
    def engine(self) -> Engine:
        return self._engine

    def ping(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            return True
        except Exception:
            return False

    def dispose(self) -> None:
        if hasattr(self, '_engine'):
            self._engine.dispose()

    # ============ SessionProvider 接口实现 ============
    def get_session(self) -> Session:
        """创建新会话（推荐用法）"""
        return self._session_factory()

    @contextmanager
    def transaction(self) -> Generator[Session, None, None]:
        """事务上下文管理器（推荐用法）"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ============ 移除的内容 ============
    # ❌ 移除: self.session 全局属性
    # ❌ 移除: commit() / rollback() 全局方法
    # ❌ 移除: execute_sql() 等直接执行方法
    # ❌ 移除: session_scope() (已被 transaction() 替代)
```

#### 步骤 3: OrmOperations 解耦

```python
# xtsqlorm/operations.py (重构后)
class OrmOperations[T]:
    """ORM操作类 - 专注于业务逻辑"""

    def __init__(
        self,
        data_model: type[T],
        session_provider: SessionProvider,  # 依赖抽象
        validator_model: type[BaseModel] | None = None,
    ):
        self._data_model = data_model
        self._session_provider = session_provider
        self._validator_model = validator_model

    # ============ 推荐用法: 使用transaction ============
    def create(self, data_dict: dict[str, Any]) -> T:
        """创建记录"""
        validated_data = self._validate_data(data_dict)

        with self._session_provider.transaction() as session:
            instance = self._data_model(**validated_data)
            session.add(instance)
            return instance

    def get_by_id(self, id_value: int) -> T | None:
        """获取记录"""
        with self._session_provider.transaction() as session:
            return session.get(self._data_model, id_value)

    # ============ 高级用法: 支持外部session ============
    def create_with_session(
        self,
        data_dict: dict[str, Any],
        session: Session,
    ) -> T:
        """在外部事务中创建记录"""
        validated_data = self._validate_data(data_dict)
        instance = self._data_model(**validated_data)
        session.add(instance)
        return instance

    # ============ 移除的内容 ============
    # ❌ 移除: session_scope() (使用session_provider.transaction())
    # ❌ 移除: self.db 属性 (使用session_provider)
    # ❌ 移除: execute_raw_sql() (应该用session.execute()或单独的QueryExecutor)
```

### 5.2 Phase 2: 引入工作单元模式（推荐）

```python
# xtsqlorm/uow.py
class UnitOfWork:
    """工作单元 - 管理一组相关操作的事务边界"""

    def __init__(self, session_factory: Callable[[], Session]):
        self._session_factory = session_factory
        self._session: Session | None = None

    def __enter__(self) -> "UnitOfWork":
        self._session = self._session_factory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self._session.close()

    @property
    def session(self) -> Session:
        if self._session is None:
            raise RuntimeError("UnitOfWork not started")
        return self._session

    def commit(self):
        self._session.commit()

    def rollback(self):
        self._session.rollback()

    def repository(self, model: type[T]) -> "Repository[T]":
        """获取特定模型的仓储"""
        return Repository(model, self.session)

# 使用示例
conn = SqlConnection(db_key='default')

with UnitOfWork(conn.get_session) as uow:
    user_repo = uow.repository(User)
    order_repo = uow.repository(Order)

    user = user_repo.get_by_id(1)
    order = order_repo.create({'user_id': user.id, 'amount': 100})

    # 自动提交所有更改
```

### 5.3 Phase 3: 完整的分层架构（长期目标）

```
xtsqlorm/
├── core/
│   ├── engine.py          # 连接引擎管理
│   ├── session.py         # Session工厂和管理
│   └── protocols.py       # 抽象协议定义
├── patterns/
│   ├── uow.py            # 工作单元模式
│   └── repository.py     # 仓储模式
├── orm/
│   ├── operations.py     # 基础ORM操作
│   └── query_builder.py  # 查询构建器
└── utils/
    ├── validators.py     # 数据验证
    └── exporters.py      # 数据导出
```

---

## 6. 迁移路径

### 向后兼容的渐进式重构

#### Step 1: 保留旧接口，添加新接口

```python
class SqlConnection:
    # 新接口（推荐）
    def get_session(self) -> Session:
        return self._session_factory()

    @contextmanager
    def transaction(self):
        session = self.get_session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    # 旧接口（标记为废弃，但仍可用）
    @property
    @deprecated("使用 get_session() 替代")
    def session(self) -> Session:
        if self._session is None:
            self._session = self._session_factory()
        return self._session

    @deprecated("使用 transaction() 上下文管理器替代")
    def commit(self):
        if self._session:
            self._session.commit()
```

#### Step 2: 文档和示例更新

```python
# 旧用法（仍然支持）
ops = OrmOperations(User, SqlConnection())
user = ops.get_by_id(1)

# 新用法（推荐）
conn = SqlConnection()
with conn.transaction() as session:
    user = session.get(User, 1)

# 或使用工作单元
with UnitOfWork(conn.get_session) as uow:
    user_repo = uow.repository(User)
    user = user_repo.get_by_id(1)
```

#### Step 3: 逐步迁移并删除旧代码

---

## 7. 总结

### 当前设计评分

| 维度            | 评分     | 说明                     |
| --------------- | -------- | ------------------------ |
| 单一职责        | ⭐⭐     | SqlConnection 职责过多   |
| 开闭原则        | ⭐⭐⭐   | 扩展性尚可，但修改风险高 |
| 里氏替换        | ⭐⭐     | 缺乏抽象层，难以替换     |
| 接口隔离        | ⭐⭐     | 接口过于庞大             |
| 依赖倒置        | ⭐       | 依赖具体类而非抽象       |
| DB-API 2.0 对齐 | ⭐⭐⭐   | 部分符合，但概念混淆     |
| **总体评分**    | **⭐⭐** | **需要重构**             |

### 核心建议

1. **🔴 高优先级**:

    - 拆分 SqlConnection 的职责
    - 引入抽象接口（SessionProvider）
    - 移除全局 session 属性

2. **🟡 中优先级**:

    - 实现工作单元模式
    - 统一事务管理逻辑
    - 改进异步实现

3. **🟢 低优先级**:
    - 移除单例模式
    - 完善文档和示例
    - 性能优化

### 最终建议的架构

```python
# 简洁、清晰、符合现代设计原则的架构

# 1. 连接层 - 只负责连接
connection = ConnectionManager(url='...')

# 2. 会话层 - 管理事务边界
with connection.transaction() as session:
    # 3. 仓储层 - 业务友好的接口
    user_repo = Repository(User, session)
    user = user_repo.get_by_id(1)
    user.name = 'New Name'
    user_repo.save(user)
    # 自动提交

# 或使用工作单元模式
with UnitOfWork(connection) as uow:
    user_repo = uow.repository(User)
    order_repo = uow.repository(Order)

    user = user_repo.get_by_id(1)
    order = order_repo.create({...})
    # 自动提交所有更改
```

这样的设计：

-   ✅ 职责清晰，每个类只做一件事
-   ✅ 易于测试和 mock
-   ✅ 符合 SOLID 原则
-   ✅ 对齐 DB-API 2.0 精神
-   ✅ 扩展性强，易于维护
