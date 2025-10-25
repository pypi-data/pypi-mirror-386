#!/usr/bin/env python3
"""
==============================================================
Description  : 会话和事务管理 - 统一的Session创建和事务控制
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-24 15:00:00
Github       : https://github.com/sandorn/xtsqlorm

本模块提供会话和事务管理功能:
- SessionFactory: Session工厂,负责创建Session实例
- SessionProvider: 会话提供者,统一的事务管理

设计原则:
- 事务边界清晰(使用上下文管理器)
- Session生命周期明确
- 自动提交和回滚
==============================================================
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session, scoped_session, sessionmaker
from xtlog import mylog

from .protocols import IConnectionManager, ISessionProvider

if TYPE_CHECKING:
    pass


class SessionFactory:
    """Session工厂 - 负责创建Session实例

    封装了SQLAlchemy的sessionmaker,提供统一的Session创建接口。
    支持创建普通Session和线程安全的ScopedSession。

    Example:
        >>> factory = SessionFactory(connection_manager)
        >>> session = factory.create_session()
        >>> # 使用session...
        >>> session.close()
    """

    def __init__(self, connection_manager: IConnectionManager):
        """初始化Session工厂

        Args:
            connection_manager: 连接管理器实例
        """
        self._connection_manager = connection_manager
        self._session_factory = sessionmaker(
            bind=connection_manager.engine,
            autoflush=True,
            expire_on_commit=True,
        )
        self._scoped_factory = scoped_session(self._session_factory)

    def create_session(self) -> Session:
        """创建新的Session实例

        Returns:
            Session: 新创建的Session对象

        Note:
            调用者需要负责关闭返回的session
        """
        return self._session_factory()

    def create_scoped_session(self) -> Session:
        """创建线程安全的Session

        Returns:
            Session: 线程安全的Session对象

        Note:
            ScopedSession会在每个线程中维护独立的Session实例
        """
        return self._scoped_factory()


class SessionProvider(ISessionProvider):
    """会话提供者 - 统一的事务管理

    职责:
    - 提供Session创建接口
    - 管理事务边界(commit/rollback)
    - 提供事务上下文管理器

    推荐用法:
        >>> provider = SessionProvider(connection_manager)
        >>> # 自动事务管理(推荐)
        >>> with provider.transaction() as session:
        ...     user = session.get(User, 1)
        ...     user.name = 'New Name'
        ...     # 自动提交
        >>> # 手动管理(不推荐)
        >>> session = provider.create_session()
        >>> try:
        ...     # 操作数据库
        ...     session.commit()
        >>> except:
        ...     session.rollback()
        >>> finally:
        ...     session.close()
    """

    def __init__(self, connection_manager: IConnectionManager):
        """初始化会话提供者

        Args:
            connection_manager: 连接管理器实例
        """
        self._connection_manager = connection_manager
        self._session_factory = SessionFactory(connection_manager)
        mylog.success('SessionProvider | 会话提供者已初始化')

    def __str__(self) -> str:
        """字符串表示"""
        return f'SessionProvider({self._connection_manager})'

    def create_session(self) -> Session:
        """创建新的Session实例

        Returns:
            Session: 新创建的Session对象

        Note:
            调用者需要负责关闭返回的session

        Example:
            >>> provider = SessionProvider(connection_manager)
            >>> session = provider.create_session()
            >>> try:
            ...     # 使用session
            ...     session.commit()
            >>> finally:
            ...     session.close()
        """
        return self._session_factory.create_session()

    @contextmanager
    def transaction(self) -> Generator[Session]:
        """事务上下文管理器(推荐用法)

        自动管理事务的完整生命周期:
        - 开始: 创建Session
        - 成功: 提交事务
        - 失败: 回滚事务
        - 结束: 关闭Session

        Yields:
            Session: 数据库会话对象

        Example:
            >>> provider = SessionProvider(connection_manager)
            >>> # 简单操作
            >>> with provider.transaction() as session:
            ...     user = User(name='Alice')
            ...     session.add(user)
            ...     # 自动提交
            >>> # 查询操作
            >>> with provider.transaction() as session:
            ...     user = session.get(User, 1)
            ...     print(user.name)
            >>> # 更新操作
            >>> with provider.transaction() as session:
            ...     user = session.get(User, 1)
            ...     user.name = 'Bob'
            ...     # 自动提交
            >>> # 异常自动回滚
            >>> try:
            ...     with provider.transaction() as session:
            ...         user = User(name='Invalid')
            ...         session.add(user)
            ...         raise ValueError('测试异常')
            ... except ValueError:
            ...     pass  # 事务已自动回滚
        """
        session = self.create_session()
        try:
            mylog.debug('SessionProvider | 事务开始')
            yield session
            session.commit()
            mylog.success('SessionProvider | 事务提交成功')
        except Exception as e:
            session.rollback()
            mylog.error(f'SessionProvider | 事务回滚: {e}')
            raise
        finally:
            session.close()
            mylog.debug('SessionProvider | 会话已关闭')


__all__ = ['SessionFactory', 'SessionProvider']
