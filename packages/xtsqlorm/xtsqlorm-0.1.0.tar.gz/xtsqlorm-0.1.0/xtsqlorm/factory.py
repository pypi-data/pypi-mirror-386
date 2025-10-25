#!/usr/bin/env python3
"""
==============================================================
Description  : 工厂函数模块 - 提供便捷的对象创建接口
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-24 19:00:00
Github       : https://github.com/sandorn/xtsqlorm

本模块提供工厂函数,简化对象创建流程:

同步工厂函数:
- create_connection_manager: 创建连接管理器
- create_session_provider: 创建会话提供者
- create_repository: 创建仓储对象
- create_orm_operations: 创建ORM操作对象

异步工厂函数:
- create_async_connection_manager: 创建异步连接管理器
- create_async_session_provider: 创建异步会话提供者
- create_async_repository: 创建异步仓储对象

设计理念:
- 简化创建流程
- 统一参数接口
- 自动依赖注入
- 类型安全保证
==============================================================
"""

from __future__ import annotations

from typing import Any

from .engine import ConnectionManager
from .operations import OrmOperations
from .protocols import IAsyncConnectionManager, IAsyncRepository, IAsyncSessionProvider, IConnectionManager, ISessionProvider
from .repository import Repository
from .session import SessionProvider


def create_connection_manager(
    db_key: str = 'default',
    url: str | None = None,
    pool_size: int = 5,
    max_overflow: int = 10,
    pool_timeout: int = 30,
    pool_recycle: int = 3600,
    echo: bool = False,
    **kwargs: Any,
) -> ConnectionManager:
    """创建连接管理器

    创建并返回一个ConnectionManager实例,用于管理数据库连接池。

    Args:
        db_key: 数据库配置键,用于从配置文件获取连接信息,默认'default'
        url: 数据库连接URL,如果提供则优先使用此URL
        pool_size: 连接池大小,默认5
        max_overflow: 最大溢出连接数,默认10
        pool_timeout: 连接超时时间(秒),默认30
        pool_recycle: 连接回收时间(秒),默认3600(1小时)
        echo: 是否打印SQL日志,默认False
        **kwargs: 其他SQLAlchemy引擎参数

    Returns:
        ConnectionManager: 连接管理器实例

    Example:
        >>> # 使用默认配置
        >>> conn_mgr = create_connection_manager()
        >>> # 指定数据库键
        >>> conn_mgr = create_connection_manager(db_key='mysql_db')
        >>> # 直接指定URL
        >>> conn_mgr = create_connection_manager(url='mysql+mysqlconnector://user:pass@localhost/db')
    """
    return ConnectionManager(
        db_key=db_key,
        url=url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        echo=echo,
        **kwargs,
    )


def create_session_provider(
    connection_manager: IConnectionManager | None = None,
    db_key: str = 'default',
    **kwargs: Any,
) -> SessionProvider:
    """创建会话提供者

    创建并返回一个SessionProvider实例,用于管理Session和事务。

    Args:
        connection_manager: 连接管理器实例,如果为None则自动创建
        db_key: 当connection_manager为None时,用于创建ConnectionManager的数据库配置键
        **kwargs: 当connection_manager为None时,传递给create_connection_manager的其他参数

    Returns:
        SessionProvider: 会话提供者实例

    Example:
        >>> # 自动创建连接管理器
        >>> provider = create_session_provider()
        >>> # 使用现有连接管理器
        >>> conn_mgr = create_connection_manager()
        >>> provider = create_session_provider(connection_manager=conn_mgr)
        >>> # 指定数据库键
        >>> provider = create_session_provider(db_key='mysql_db')
    """
    if connection_manager is None:
        connection_manager = create_connection_manager(db_key=db_key, **kwargs)
    return SessionProvider(connection_manager)


def create_repository[T](
    model: type[T],
    session_provider: ISessionProvider | None = None,
    db_key: str = 'default',
    **kwargs: Any,
) -> Repository[T]:
    """创建仓储对象

    创建并返回一个Repository实例,提供标准的CRUD操作。

    Type Parameters:
        T: ORM模型类型

    Args:
        model: ORM模型类
        session_provider: 会话提供者实例,如果为None则自动创建
        db_key: 当session_provider为None时,用于创建SessionProvider的数据库配置键
        **kwargs: 当session_provider为None时,传递给create_session_provider的其他参数

    Returns:
        Repository[T]: 仓储实例

    Example:
        >>> from xtsqlorm import User
        >>> # 自动创建session_provider
        >>> user_repo = create_repository(User)
        >>> # 使用现有session_provider
        >>> provider = create_session_provider()
        >>> user_repo = create_repository(User, session_provider=provider)
        >>> # 指定数据库键
        >>> user_repo = create_repository(User, db_key='mysql_db')
    """
    if session_provider is None:
        session_provider = create_session_provider(db_key=db_key, **kwargs)
    return Repository(model, session_provider)


def create_orm_operations[T](
    model: type[T],
    session_provider: ISessionProvider | None = None,
    validator_model: Any | None = None,
    cache_enabled: bool = True,
    db_key: str = 'default',
    **kwargs: Any,
) -> OrmOperations[T]:
    """创建ORM操作对象

    创建并返回一个OrmOperations实例,提供基础CRUD和高级功能。

    Type Parameters:
        T: ORM模型类型

    Args:
        model: ORM模型类
        session_provider: 会话提供者实例,如果为None则自动创建
        validator_model: Pydantic验证模型(可选)
        cache_enabled: 是否启用查询缓存,默认True
        db_key: 当session_provider为None时,用于创建SessionProvider的数据库配置键
        **kwargs: 当session_provider为None时,传递给create_session_provider的其他参数

    Returns:
        OrmOperations[T]: ORM操作对象

    Example:
        >>> from xtsqlorm import User
        >>> # 基础用法
        >>> ops = create_orm_operations(User)
        >>> user = ops.get_by_id(1)
        >>> # 指定数据库键
        >>> ops = create_orm_operations(User, db_key='mysql_db')
        >>> # 使用Pydantic验证
        >>> from pydantic import BaseModel
        >>> class UserValidator(BaseModel):
        ...     name: str
        ...     age: int
        >>> ops = create_orm_operations(User, validator_model=UserValidator, cache_enabled=True)
    """
    if session_provider is None:
        session_provider = create_session_provider(db_key=db_key, **kwargs)

    return OrmOperations(
        model,
        session_provider,
        validator_model=validator_model,
        cache_enabled=cache_enabled,
    )


# ============ 异步工厂函数 ============


def create_async_connection_manager(
    db_key: str = 'default',
    url: str | None = None,
    pool_size: int = 5,
    max_overflow: int = 10,
    pool_timeout: int = 30,
    pool_recycle: int = 3600,
    echo: bool = False,
    **kwargs: Any,
) -> IAsyncConnectionManager:
    """创建异步连接管理器

    创建并返回一个AsyncConnectionManager实例,用于管理异步数据库连接池。

    Args:
        db_key: 数据库配置键,用于从配置文件获取连接信息
        url: 数据库连接URL,如果提供则优先使用
        pool_size: 连接池大小,默认5
        max_overflow: 最大溢出连接数,默认10
        pool_timeout: 连接超时时间(秒),默认30
        pool_recycle: 连接回收时间(秒),默认3600(1小时)
        echo: 是否打印SQL日志,默认False
        **kwargs: 其他SQLAlchemy引擎参数

    Returns:
        IAsyncConnectionManager: 异步连接管理器实例

    Example:
        >>> # 使用默认配置
        >>> async_conn_mgr = create_async_connection_manager()
        >>> # 指定数据库键
        >>> async_conn_mgr = create_async_connection_manager(db_key='mysql_db')
        >>> # 直接指定URL
        >>> async_conn_mgr = create_async_connection_manager(url='mysql+aiomysql://user:pass@localhost/db')
    """
    from .async_engine import AsyncConnectionManager

    return AsyncConnectionManager(
        db_key=db_key,
        url=url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        echo=echo,
        **kwargs,
    )


def create_async_session_provider(
    connection_manager: IAsyncConnectionManager | None = None,
    db_key: str = 'default',
    url: str | None = None,
    **kwargs: Any,
) -> IAsyncSessionProvider:
    """创建异步会话提供者

    创建并返回一个AsyncSessionProvider实例,用于管理异步Session和事务。

    Args:
        connection_manager: 异步连接管理器实例,如果为None则自动创建
        db_key: 当connection_manager为None时,用于创建AsyncConnectionManager的数据库配置键
        url: 当connection_manager为None时,用于创建AsyncConnectionManager的数据库URL
        **kwargs: 当connection_manager为None时,传递给create_async_connection_manager的其他参数

    Returns:
        IAsyncSessionProvider: 异步会话提供者实例

    Example:
        >>> # 自动创建异步连接管理器
        >>> async_provider = create_async_session_provider()
        >>> # 使用现有异步连接管理器
        >>> async_conn_mgr = create_async_connection_manager()
        >>> async_provider = create_async_session_provider(connection_manager=async_conn_mgr)
        >>> # 指定数据库键
        >>> async_provider = create_async_session_provider(db_key='mysql_db')
    """
    from .async_session import AsyncSessionProvider

    if connection_manager is None:
        connection_manager = create_async_connection_manager(db_key=db_key, url=url, **kwargs)
    return AsyncSessionProvider(connection_manager)


def create_async_repository[T](
    model: type[T],
    session_provider: IAsyncSessionProvider | None = None,
    db_key: str = 'default',
    url: str | None = None,
    **kwargs: Any,
) -> IAsyncRepository[T]:
    """创建异步仓储对象

    创建并返回一个AsyncRepository实例,提供标准异步CRUD操作。

    Args:
        model: ORM模型类
        session_provider: 异步会话提供者实例,如果为None则自动创建
        db_key: 当session_provider为None时,用于创建AsyncSessionProvider的数据库配置键
        url: 当session_provider为None时,用于创建AsyncSessionProvider的数据库URL
        **kwargs: 当session_provider为None时,传递给create_async_session_provider的其他参数

    Returns:
        IAsyncRepository[T]: 异步仓储实例

    Example:
        >>> # 自动创建依赖
        >>> user_repo = create_async_repository(User)
        >>> # 使用现有异步会话提供者
        >>> async_provider = create_async_session_provider()
        >>> user_repo = create_async_repository(User, session_provider=async_provider)
        >>> # 指定数据库键
        >>> user_repo = create_async_repository(User, db_key='mysql_db')
    """
    from .async_repository import AsyncRepository

    if session_provider is None:
        session_provider = create_async_session_provider(db_key=db_key, url=url, **kwargs)
    return AsyncRepository(model, session_provider)


# ============ 便捷别名(简化导入)============

# 同步简短的函数名
create_conn_mgr = create_connection_manager
create_provider = create_session_provider
create_repo = create_repository
create_ops = create_orm_operations

# 异步简短的函数名
create_async_conn_mgr = create_async_connection_manager
create_async_provider = create_async_session_provider
create_async_repo = create_async_repository


__all__ = (
    # 同步简短别名
    'create_conn_mgr',
    'create_ops',
    'create_provider',
    'create_repo',
    # 同步标准名称
    'create_connection_manager',
    'create_orm_operations',
    'create_repository',
    'create_session_provider',
    # 异步简短别名
    'create_async_conn_mgr',
    'create_async_provider',
    'create_async_repo',
    # 异步标准名称
    'create_async_connection_manager',
    'create_async_repository',
    'create_async_session_provider',
)
