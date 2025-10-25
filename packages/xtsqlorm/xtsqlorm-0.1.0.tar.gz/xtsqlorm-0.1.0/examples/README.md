# xtsqlorm 示例集合

本目录包含 **xtsqlorm** 的完整示例代码，覆盖所有核心功能。

## 📚 示例列表

### 基础示例

#### [01. 基础同步 CRUD 操作](example_01_basic_sync.py)

**难度**: ⭐
**涵盖功能**:

-   Repository 基础 CRUD
-   工厂函数使用
-   三种使用模式对比
-   外部事务管理

**适合人群**: 新手入门

**运行方式**:

```bash
python examples/example_01_basic_sync.py
```

---

#### [02. 高级 ORM 操作](example_02_advanced_operations.py)

**难度**: ⭐⭐
**涵盖功能**:

-   分页查询
-   条件查询
-   统计分析
-   批量操作
-   数据导出（Pandas）
-   原生 SQL 执行
-   查询缓存

**适合人群**: 有一定基础的开发者

**运行方式**:

```bash
python examples/example_02_advanced_operations.py
```

---

#### [03. 表反射和动态模型](example_03_table_reflection.py)

**难度**: ⭐⭐
**涵盖功能**:

-   反射现有数据库表
-   动态创建模型类
-   表复制功能
-   生成模型文件（sqlacodegen）
-   探索表元数据

**适合人群**: 需要处理动态表结构的开发者

**运行方式**:

```bash
python examples/example_03_table_reflection.py
```

---

### 进阶示例

#### [04. Mixin 和自定义类型](example_04_mixins_and_types.py)

**难度**: ⭐⭐
**涵盖功能**:

-   IdMixin - 自增主键
-   TimestampMixin - 时间戳
-   SoftDeleteMixin - 软删除
-   VersionedMixin - 版本控制
-   UTCTimeMixin - UTC 时间
-   JsonEncodedDict - JSON 类型
-   UTCDateTime - UTC 时间类型
-   EnumType - 枚举类型

**适合人群**: 需要使用高级模型特性的开发者

**运行方式**:

```bash
python examples/example_04_mixins_and_types.py
```

---

#### [05. 数据验证](example_05_data_validation.py)

**难度**: ⭐⭐
**涵盖功能**:

-   Pydantic 数据验证
-   OrmOperations 集成验证
-   内置验证器使用
-   自定义验证逻辑

**适合人群**: 需要严格数据验证的项目

**运行方式**:

```bash
python examples/example_05_data_validation.py
```

---

#### [06. 事务管理和工作单元](example_06_transactions.py)

**难度**: ⭐⭐⭐
**涵盖功能**:

-   基础事务管理
-   事务回滚
-   UnitOfWork 工作单元模式
-   复杂事务场景
-   嵌套事务
-   手动事务控制

**适合人群**: 处理复杂业务逻辑的开发者

**运行方式**:

```bash
python examples/example_06_transactions.py
```

---

### 综合示例

#### [07. 完整工作流](example_07_complete_workflow.py)

**难度**: ⭐⭐⭐
**涵盖功能**:

-   用户注册（含数据验证）
-   用户登录（含密码验证）
-   更新用户信息
-   分页查询用户列表
-   数据统计和导出
-   业务逻辑层设计
-   完整的错误处理

**适合人群**: 需要完整应用示例的开发者

**运行方式**:

```bash
python examples/example_07_complete_workflow.py
```

---

#### [08. 表管理](example_08_table_management.py)

**难度**: ⭐⭐
**涵盖功能**:

-   检查表是否存在
-   创建表（如果不存在）
-   删除表
-   批量创建多个表
-   列出所有表
-   实际应用场景

**适合人群**: 需要动态管理数据库表的开发者

**运行方式**:

```bash
python examples/example_08_table_management.py
```

---

### 异步示例

#### [异步功能完整演示](examples_async.py)

**难度**: ⭐⭐⭐
**涵盖功能**:

-   AsyncConnectionManager - 异步连接管理
-   AsyncSessionProvider - 异步会话管理
-   AsyncRepository - 异步仓储
-   reflect_table_async - 异步表反射
-   异步 CRUD 操作
-   异步分页查询
-   三种异步使用模式

**适合人群**: 需要异步支持的高性能应用

**运行方式**:

```bash
python examples/examples_async.py
```

---

## 🎯 快速开始

### 1. 安装依赖

确保已安装 xtsqlorm 及其依赖：

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

在 `xtsqlorm/cfg.py` 中配置数据库连接信息：

```python
db_config = {
    'default': {
        'driver': 'mysql',
        'host': 'localhost',
        'port': 3306,
        'user': 'your_user',
        'password': 'your_password',
        'database': 'your_database',
    }
}
```

### 3. 准备测试数据

示例代码使用 `users` 表，请确保数据库中存在该表：

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    nickname VARCHAR(50),
    avatar VARCHAR(255),
    last_login_at DATETIME,
    login_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 4. 运行示例

选择一个示例文件运行：

```bash
# 从基础开始
python examples/example_01_basic_sync.py

# 或者运行完整工作流
python examples/example_07_complete_workflow.py
```

---

## 📖 学习路径

推荐的学习顺序：

1. **新手入门**:

    - `example_01_basic_sync.py` - 理解基础 CRUD
    - `example_03_table_reflection.py` - 学习表反射

2. **进阶学习**:

    - `example_02_advanced_operations.py` - 掌握高级查询
    - `example_04_mixins_and_types.py` - 使用 Mixin 和自定义类型
    - `example_05_data_validation.py` - 实现数据验证

3. **高级应用**:
    - `example_06_transactions.py` - 理解事务管理
    - `example_07_complete_workflow.py` - 完整应用设计
    - `examples_async.py` - 异步编程

---

## 🔧 常见问题

### Q: 示例代码提示 "表不存在"？

A: 请先创建测试表，参考上面的 SQL 语句。

### Q: 如何修改数据库配置？

A: 编辑 `xtsqlorm/cfg.py` 文件中的数据库配置。

### Q: 示例代码中的某些操作没有实际执行？

A: 为了安全，部分写操作（CREATE/UPDATE/DELETE）只展示代码，不实际执行。如需测试，请取消注释。

### Q: 异步示例运行失败？

A: 确保安装了异步驱动（如 `aiomysql`），并且数据库 URL 使用异步驱动前缀。

---

## 📝 补充说明

### 代码风格

-   所有示例遵循 PEP 8 规范
-   使用类型注解提高代码可读性
-   详细的注释和文档字符串

### 示例特点

-   ✅ 可运行的完整代码
-   ✅ 详细的功能说明
-   ✅ 真实的应用场景
-   ✅ 最佳实践演示
-   ✅ 错误处理示例

### 扩展学习

-   查看 `xtsqlorm` 源码了解实现细节
-   参考官方文档获取更多信息
-   在实际项目中实践应用

---

## 🤝 贡献

欢迎提交更多示例！

如果您有好的示例想法，请：

1. Fork 项目
2. 创建新的示例文件
3. 提交 Pull Request

---

## 📞 支持

如有问题，请提交 Issue 或联系：

-   Email: sandorn@live.cn
-   GitHub: https://github.com/sandorn/xtsqlorm

---

**Happy Coding! 🎉**
