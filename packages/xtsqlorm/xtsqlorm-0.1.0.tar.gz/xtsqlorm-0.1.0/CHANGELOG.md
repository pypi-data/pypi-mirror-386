# Changelog

所有重要的项目变更都将记录在此文件中。

本项目遵循 [语义化版本 2.0.0](https://semver.org/lang/zh-CN/)。

---

## [0.1.0] - 2025-10-25

### 新增 ✨

-   **异步架构完整实现**

    -   新增 `AsyncConnectionManager` 异步连接管理
    -   新增 `AsyncSessionProvider` 异步会话管理
    -   新增 `AsyncRepository` 异步仓储模式
    -   新增 `AsyncOrmOperations` 异步高级操作
    -   新增 `reflect_table_async` 异步表反射

-   **增强的数据验证器**

    -   新增 `validate_url` URL 验证
    -   新增 `validate_ip` IP 地址验证
    -   新增 `validate_pattern` 正则模式验证
    -   新增 `validate_in_choices` 选项验证
    -   新增 `validate_type` 类型验证
    -   新增 `validate_password_strength` 密码强度验证
    -   新增 `validate_username` 用户名验证
    -   新增 `validate_chinese_id_card` 身份证验证

-   **工厂函数增强**
    -   新增 `create_async_connection_manager` 异步连接管理器工厂
    -   新增 `create_async_session_provider` 异步会话提供者工厂
    -   新增 `create_async_repository` 异步仓储工厂

### 改进 🚀

-   **代码质量提升**

    -   修复 93 处全角标点符号问题
    -   修复 2 个类型检查错误
    -   通过 Ruff 代码规范检查
    -   通过 basedPyright 类型检查
    -   代码质量评分从 4.3 提升到 4.8

-   **架构优化**

    -   实现完整的依赖注入模式
    -   优化资源生命周期管理
    -   改进异常处理机制
    -   统一接口设计

-   **性能优化**
    -   优化连接池配置
    -   改进查询缓存机制
    -   优化批量操作性能

### 修复 🐛

-   **异步资源管理**

    -   修复异步连接资源泄漏问题
    -   修复 `RuntimeError: Event loop is closed` 错误
    -   添加 `dispose()` 自动清理机制

-   **数据访问问题**

    -   修复 `DetachedInstanceError` 问题
    -   添加 `session.refresh()` 和 `session.expunge()`
    -   优化会话生命周期管理

-   **Mixin 问题**

    -   修复 `VersionedMixin` 的 `__mapper_args__` 问题
    -   统一字段命名 (`version_id` → `version`)
    -   修复 `IdMixin` 字段命名 (`ID` → `id`)

-   **Pydantic 兼容性**
    -   迁移到 Pydantic V2 API
    -   修复 `@validator` → `@field_validator`
    -   修复 `.dict()` → `.model_dump()`

### 文档 📚

-   **新增文档**

    -   新增 `CODE_QUALITY_REPORT.md` 代码质量分析报告
    -   新增 `CODE_OPTIMIZATION_COMPLETE.md` 优化完成总结
    -   新增 `ASYNC_EXAMPLES_FIX_COMPLETE.md` 异步示例修复文档
    -   新增 8+ 完整示例文件

-   **文档改进**
    -   完善所有公共 API 的 docstring
    -   添加详细的使用示例
    -   更新架构设计文档
    -   优化代码注释

### 配置 ⚙️

-   **Ruff 配置优化**
    -   添加针对示例代码的规则豁免
    -   配置 `pyproject.toml` 完善
    -   优化代码格式化规则

---

## [0.2.7] - 2025-10-20

### 改进 🚀

-   **架构重构**

    -   实现平面化架构设计
    -   拆分 `connection.py` 为 `engine.py` 和 `session.py`
    -   拆分 `models.py` 为 `base.py`, `types.py`, `mixins.py`
    -   优化模块职责划分

-   **工具函数增强**
    -   新增 `table_utils.py` 表工具模块
    -   新增 `sql_builder.py` SQL 构建模块
    -   优化 `reflect_table` 实现

### 修复 🐛

-   修复表反射的索引名冲突问题
-   修复 SQL 注入安全问题
-   优化表复制逻辑

---

## [0.2.6] - 2025-10-15

### 新增 ✨

-   **Repository 模式**

    -   实现标准 Repository 接口
    -   添加 Unit of Work 模式
    -   支持事务管理

-   **Mixin 增强**
    -   新增 `SoftDeleteMixin` 软删除
    -   新增 `VersionedMixin` 乐观锁
    -   新增 `UTCTimeMixin` UTC 时间

### 改进 🚀

-   优化连接池管理
-   改进错误处理
-   完善类型注解

---

## [0.2.5] - 2025-10-10

### 新增 ✨

-   **数据验证**

    -   集成 Pydantic 验证
    -   添加内置验证器
    -   支持自定义验证规则

-   **查询增强**
    -   添加分页查询
    -   支持字段统计
    -   实现查询缓存

### 改进 🚀

-   优化批量操作性能
-   改进文档字符串
-   完善示例代码

---

## [0.2.0] - 2025-10-01

### 新增 ✨

-   **基础功能**

    -   实现基础 CRUD 操作
    -   支持 MySQL 数据库
    -   添加连接池管理

-   **模型定义**
    -   实现 `BaseModel` 基类
    -   添加 `IdMixin` 主键混入
    -   添加 `TimestampMixin` 时间戳混入

### 初始版本 🎉

-   项目初始化
-   基础架构搭建
-   核心功能实现

---

## 版本说明

### 版本号格式

采用语义化版本 `MAJOR.MINOR.PATCH`:

-   **MAJOR**: 不兼容的 API 修改
-   **MINOR**: 向后兼容的功能性新增
-   **PATCH**: 向后兼容的问题修正

### 变更类型

-   ✨ **新增**: 新功能
-   🚀 **改进**: 功能改进或性能优化
-   🐛 **修复**: Bug 修复
-   📚 **文档**: 文档更新
-   ⚙️ **配置**: 配置文件更新
-   🎉 **里程碑**: 重要版本发布

---

**维护者**: sandorn <sandorn@live.cn>  
**最后更新**: 2025-10-25
