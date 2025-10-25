#!/usr/bin/env python3
"""
==============================================================
Description  : XT-SQLORM主模块初始化
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-24 15:00:00
Github       : https://github.com/sandorn/xtsqlorm

XT-SQLORM是一个基于SQLAlchemy的ORM框架,采用扁平化架构设计

核心架构:

同步架构:
- protocols: 抽象接口定义
- engine: 连接引擎管理
- session: 会话和事务管理
- repository: 通用仓储模式
- uow: 工作单元模式
- operations: 高级ORM操作

异步架构:
- async_engine: 异步连接引擎管理
- async_session: 异步会话和事务管理
- async_repository: 异步通用仓储模式

设计原则:
- 职责清晰
- 易于测试
- 松耦合
==============================================================
"""

from __future__ import annotations

__version__ = '0.1.0'

# ============ 异步架构组件 ============
from .async_engine import AsyncConnectionManager
from .async_repository import AsyncRepository
from .async_session import AsyncSessionFactory, AsyncSessionProvider

# ============ 基类和模型 ============
from .base import Base, BaseModel, ItemMixin, ModelExt

# ============ 核心架构组件 ============
from .engine import ConnectionManager

# ============ 工厂函数 ============
from .factory import (
    create_async_conn_mgr,
    create_async_connection_manager,
    create_async_provider,
    create_async_repo,
    create_async_repository,
    create_async_session_provider,
    create_conn_mgr,
    create_connection_manager,
    create_ops,
    create_orm_operations,
    create_provider,
    create_repo,
    create_repository,
    create_session_provider,
)

# ============ Mixin类 ============
from .mixins import IdMixin, MixinError, SoftDeleteMixin, TimestampMixin, UTCTimeMixin, VersionedMixin

# ============ ORM操作 ============
from .operations import AsyncOrmOperations, OrmOperations
from .protocols import IAsyncConnectionManager, IAsyncRepository, IAsyncSessionProvider, IConnectionManager, IRepository, ISessionProvider
from .repository import Repository
from .session import SessionFactory, SessionProvider

# ============ 表工具 ============
from .table_utils import generate_model_file, get_or_create_table_model, reflect_table, reflect_table_async

# ============ 自定义类型 ============
from .types import EnumType, JsonEncodedDict, UTCDateTime
from .uow import UnitOfWork

# ============ 验证工具 ============
from .validators import (
    ValidationError,
    validate_chinese_id_card,
    validate_datetime,
    validate_dict,
    validate_email,
    validate_enum,
    validate_in_choices,
    validate_ip,
    validate_json,
    validate_length,
    validate_password_strength,
    validate_pattern,
    validate_phone,
    validate_range,
    validate_required,
    validate_type,
    validate_url,
    validate_username,
)

__all__ = (
    # ============ 版本信息 ============
    '__version__',
    # ============ 同步抽象接口 ============
    'IConnectionManager',
    'IRepository',
    'ISessionProvider',
    # ============ 异步抽象接口 ============
    'IAsyncConnectionManager',
    'IAsyncRepository',
    'IAsyncSessionProvider',
    # ============ 同步核心组件 ============
    'ConnectionManager',
    'Repository',
    'SessionFactory',
    'SessionProvider',
    'UnitOfWork',
    # ============ 异步核心组件 ============
    'AsyncConnectionManager',
    'AsyncRepository',
    'AsyncSessionFactory',
    'AsyncSessionProvider',
    # ============ ORM操作 ============
    'AsyncOrmOperations',
    'OrmOperations',
    # ============ 同步工厂函数 ============
    'create_connection_manager',
    'create_orm_operations',
    'create_repository',
    'create_session_provider',
    # 同步工厂函数简短别名
    'create_conn_mgr',
    'create_ops',
    'create_provider',
    'create_repo',
    # ============ 异步工厂函数 ============
    'create_async_connection_manager',
    'create_async_repository',
    'create_async_session_provider',
    # 异步工厂函数简短别名
    'create_async_conn_mgr',
    'create_async_provider',
    'create_async_repo',
    # ============ 表工具 ============
    'generate_model_file',
    'get_or_create_table_model',
    'reflect_table',
    'reflect_table_async',
    # ============ 基类 ============
    'Base',
    'BaseModel',
    'ItemMixin',
    'ModelExt',
    # ============ 自定义类型 ============
    'EnumType',
    'JsonEncodedDict',
    'UTCDateTime',
    # ============ Mixin类 ============
    'IdMixin',
    'MixinError',
    'SoftDeleteMixin',
    'TimestampMixin',
    'UTCTimeMixin',
    'VersionedMixin',
    # ============ 验证函数 ============
    'ValidationError',
    'validate_chinese_id_card',
    'validate_datetime',
    'validate_dict',
    'validate_email',
    'validate_enum',
    'validate_in_choices',
    'validate_ip',
    'validate_json',
    'validate_length',
    'validate_password_strength',
    'validate_pattern',
    'validate_phone',
    'validate_range',
    'validate_required',
    'validate_type',
    'validate_url',
    'validate_username',
)
