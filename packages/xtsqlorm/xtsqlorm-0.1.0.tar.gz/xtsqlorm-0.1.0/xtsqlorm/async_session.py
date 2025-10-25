#!/usr/bin/env python3
"""
==============================================================
Description  : 异步会话和事务管理 - 统一的AsyncSession创建和事务控制
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-24 16:35:00
Github       : https://github.com/sandorn/xtsqlorm

本模块提供异步会话和事务管理功能:
- AsyncSessionFactory: 异步Session工厂,负责创建AsyncSession实例
- AsyncSessionProvider: 异步会话提供者,统一的异步事务管理

设计原则:
- 异步事务边界清晰(使用异步上下文管理器)
- AsyncSession生命周期明确
- 自动提交和回滚
==============================================================
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session, async_sessionmaker
from xtlog import mylog

from .protocols import IAsyncConnectionManager, IAsyncSessionProvider

if TYPE_CHECKING:
    pass


class AsyncSessionFactory:
    """异步Session工厂 - 负责创建AsyncSession实例

    封装了SQLAlchemy的async_sessionmaker,提供统一的AsyncSession创建接口。
    支持创建普通AsyncSession和线程安全的ScopedAsyncSession。

    Example:
        >>> factory = AsyncSessionFactory(async_connection_manager)
        >>> session = factory.create_session()
        >>> # 使用session...
        >>> await session.close()
    """

    def __init__(self, connection_manager: IAsyncConnectionManager):
        """初始化异步Session工厂

        Args:
            connection_manager: 异步连接管理器实例
        """
        self._connection_manager = connection_manager
        self._session_factory = async_sessionmaker(
            bind=connection_manager.engine,
            class_=AsyncSession,
            autoflush=True,
            expire_on_commit=True,
        )
        self._scoped_factory = async_scoped_session(
            self._session_factory,
            scopefunc=lambda: 0,  # 简单的scope function,异步环境中需要更复杂的逻辑
        )

    def create_session(self) -> AsyncSession:
        """创建新的AsyncSession实例

        Returns:
            AsyncSession: 新创建的AsyncSession对象

        Note:
            调用者需要负责关闭返回的session
        """
        return self._session_factory()

    def create_scoped_session(self) -> AsyncSession:
        """创建线程安全的AsyncSession

        Returns:
            AsyncSession: 线程安全的AsyncSession对象

        Note:
            ScopedAsyncSession会在每个线程中维护独立的AsyncSession实例
        """
        return self._scoped_factory()


class AsyncSessionProvider(IAsyncSessionProvider):
    """异步会话提供者 - 统一的异步事务管理

    职责:
    - 提供AsyncSession创建接口
    - 管理异步事务边界(commit/rollback)
    - 提供异步事务上下文管理器

    推荐用法:
        >>> provider = AsyncSessionProvider(async_connection_manager)
        >>> # 自动事务管理(推荐)
        >>> async with provider.transaction() as session:
        ...     user = session.get(User, 1)
        ...     user.name = 'New Name'
        ...     # 自动提交
        >>> # 手动管理(不推荐)
        >>> session = provider.create_session()
        >>> try:
        ...     # 操作数据库
        ...     await session.commit()
        >>> except:
        ...     await session.rollback()
        >>> finally:
        ...     await session.close()
    """

    def __init__(self, connection_manager: IAsyncConnectionManager):
        """初始化异步会话提供者

        Args:
            connection_manager: 异步连接管理器实例
        """
        self._connection_manager = connection_manager
        self._session_factory = AsyncSessionFactory(connection_manager)
        mylog.success('AsyncSessionProvider | 异步会话提供者已初始化')

    def __str__(self) -> str:
        """字符串表示"""
        return f'AsyncSessionProvider({self._connection_manager})'

    def create_session(self) -> AsyncSession:
        """创建新的AsyncSession实例

        Returns:
            AsyncSession: 新创建的AsyncSession对象

        Note:
            调用者需要负责关闭返回的session

        Example:
            >>> provider = AsyncSessionProvider(async_connection_manager)
            >>> session = provider.create_session()
            >>> try:
            ...     # 使用session
            ...     await session.commit()
            >>> finally:
            ...     await session.close()
        """
        return self._session_factory.create_session()

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession]:
        """异步事务上下文管理器(推荐用法)

        自动管理异步事务的完整生命周期:
        - 开始: 创建AsyncSession
        - 成功: 提交事务
        - 失败: 回滚事务
        - 结束: 关闭Session

        Yields:
            AsyncSession: 异步数据库会话对象

        Example:
            >>> provider = AsyncSessionProvider(async_connection_manager)
            >>> # 简单操作
            >>> async with provider.transaction() as session:
            ...     user = User(name='Alice')
            ...     session.add(user)
            ...     # 自动提交
            >>> # 查询操作
            >>> async with provider.transaction() as session:
            ...     result = await session.get(User, 1)
            ...     print(result.name)
            >>> # 更新操作
            >>> async with provider.transaction() as session:
            ...     user = await session.get(User, 1)
            ...     user.name = 'Bob'
            ...     # 自动提交
            >>> # 异常自动回滚
            >>> try:
            ...     async with provider.transaction() as session:
            ...         user = User(name='Invalid')
            ...         session.add(user)
            ...         raise ValueError('测试异常')
            ... except ValueError:
            ...     pass  # 事务已自动回滚
        """
        session = self.create_session()
        try:
            mylog.debug('AsyncSessionProvider | 异步事务开始')
            yield session
            await session.commit()
            mylog.success('AsyncSessionProvider | 异步事务提交成功')
        except Exception as e:
            await session.rollback()
            mylog.error(f'AsyncSessionProvider | 异步事务回滚: {e}')
            raise
        finally:
            await session.close()
            mylog.debug('AsyncSessionProvider | 异步会话已关闭')


__all__ = ['AsyncSessionFactory', 'AsyncSessionProvider']
