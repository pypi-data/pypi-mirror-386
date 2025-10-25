#!/usr/bin/env python3
"""
==============================================================
Description  : 抽象接口定义 - 所有核心组件的契约
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-24 18:30:00
Github       : https://github.com/sandorn/xtsqlorm

本模块定义了xtsqlorm的核心抽象接口,遵循依赖倒置原则:

同步接口:
- IConnectionManager: 连接管理器接口
- ISessionProvider: 会话提供者接口
- IRepository: 仓储接口

异步接口:
- IAsyncConnectionManager: 异步连接管理器接口
- IAsyncSessionProvider: 异步会话提供者接口
- IAsyncRepository: 异步仓储接口

使用这些接口可以实现松耦合、易测试的架构设计
==============================================================
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Generator  # noqa: F401 - 用于文档字符串类型引用
from contextlib import asynccontextmanager, contextmanager  # noqa: F401 - 用于文档字符串示例
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
    from sqlalchemy.orm import Session


class IConnectionManager(ABC):
    """连接管理器接口 - 只负责连接层面的操作

    职责:
    - 提供SQLAlchemy引擎访问
    - 测试数据库连接
    - 释放连接资源

    实现类: ConnectionManager
    """

    @property
    @abstractmethod
    def engine(self) -> Engine:
        """获取SQLAlchemy引擎对象

        Returns:
            Engine: SQLAlchemy引擎实例
        """
        pass

    @abstractmethod
    def ping(self) -> bool:
        """测试数据库连接是否正常

        Returns:
            bool: 连接正常返回True,否则返回False
        """
        pass

    @abstractmethod
    def dispose(self) -> None:
        """释放所有数据库连接资源"""
        pass


class ISessionProvider(ABC):
    """会话提供者接口 - 负责Session创建和事务管理

    职责:
    - 创建Session实例
    - 提供事务上下文管理器
    - 统一事务边界管理

    实现类: SessionProvider
    """

    @abstractmethod
    def create_session(self) -> Session:
        """创建新的Session实例

        Returns:
            Session: 新创建的数据库会话对象

        Note:
            调用者需要负责关闭返回的session
        """
        pass

    @abstractmethod
    @contextmanager
    def transaction(self) -> Generator[Session]:
        """事务上下文管理器

        自动管理事务的完整生命周期:
        - 开始: 创建Session
        - 成功: 提交事务
        - 失败: 回滚事务
        - 结束: 关闭Session

        Yields:
            Session: 数据库会话对象

        Example:
            >>> with session_provider.transaction() as session:
            ...     user = User(name='Alice')
            ...     session.add(user)
            ...     # 自动提交
        """
        pass


class IRepository[T](ABC):
    """仓储接口 - 定义标准CRUD操作

    职责:
    - 定义统一的数据访问接口
    - 封装数据访问细节
    - 提供业务友好的API

    实现类: Repository

    Type Parameters:
        T: ORM模型类型
    """

    @abstractmethod
    def get_by_id(self, id_value: int) -> T | None:
        """根据ID获取记录

        Args:
            id_value: 记录ID

        Returns:
            T | None: 查询到的模型对象,不存在则返回None
        """
        pass

    @abstractmethod
    def create(self, data: dict[str, Any]) -> T:
        """创建新记录

        Args:
            data: 记录数据字典

        Returns:
            T: 创建的模型对象
        """
        pass

    @abstractmethod
    def update(self, id_value: int, data: dict[str, Any]) -> T | None:
        """更新记录

        Args:
            id_value: 记录ID
            data: 要更新的数据字典

        Returns:
            T | None: 更新后的模型对象,不存在则返回None
        """
        pass

    @abstractmethod
    def delete(self, id_value: int) -> bool:
        """删除记录

        Args:
            id_value: 记录ID

        Returns:
            bool: 删除成功返回True,记录不存在返回False
        """
        pass


# ============ 异步接口定义 ============


class IAsyncConnectionManager(ABC):
    """异步连接管理器接口 - 只负责异步连接层面的操作

    职责:
    - 提供SQLAlchemy异步引擎访问
    - 测试异步数据库连接
    - 释放异步连接资源

    实现类: AsyncConnectionManager
    """

    @property
    @abstractmethod
    def engine(self) -> AsyncEngine:
        """获取SQLAlchemy异步引擎对象

        Returns:
            AsyncEngine: SQLAlchemy异步引擎实例
        """
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """测试异步数据库连接是否正常

        Returns:
            bool: 连接正常返回True,否则返回False
        """
        pass

    @abstractmethod
    async def dispose(self) -> None:
        """释放所有异步数据库连接资源"""
        pass


class IAsyncSessionProvider(ABC):
    """异步会话提供者接口 - 负责AsyncSession创建和异步事务管理

    职责:
    - 创建AsyncSession实例
    - 提供异步事务上下文管理器
    - 统一异步事务边界管理

    实现类: AsyncSessionProvider
    """

    @abstractmethod
    def create_session(self) -> AsyncSession:
        """创建新的AsyncSession实例

        Returns:
            AsyncSession: 新创建的异步数据库会话对象

        Note:
            调用者需要负责关闭返回的session
        """
        pass

    @abstractmethod
    def transaction(self) -> Any:
        """异步事务上下文管理器

        自动管理异步事务的完整生命周期:
        - 开始: 创建AsyncSession
        - 成功: 提交事务
        - 失败: 回滚事务
        - 结束: 关闭Session

        Returns:
            AsyncGenerator[AsyncSession, None]: 异步上下文管理器,yield AsyncSession对象

        Note:
            - 实现类应该使用 @asynccontextmanager 装饰器
            - 返回类型为 AsyncGenerator[AsyncSession, None]
            - 必须使用 async with 语法调用此方法

        Implementation:
            实现类应该这样定义::

                @asynccontextmanager
                async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
                    session = self.create_session()
                    try:
                        yield session
                        await session.commit()
                    except Exception:
                        await session.rollback()
                        raise
                    finally:
                        await session.close()

        Example:
            >>> async with session_provider.transaction() as session:
            ...     user = User(name='Alice')
            ...     session.add(user)
            ...     # 自动提交
        """
        ...


class IAsyncRepository[T](ABC):
    """异步仓储接口 - 定义标准异步CRUD操作

    职责:
    - 定义统一的异步数据访问接口
    - 封装异步数据访问细节
    - 提供业务友好的异步API

    实现类: AsyncRepository

    Type Parameters:
        T: ORM模型类型
    """

    @abstractmethod
    async def get_by_id(self, id_value: int) -> T | None:
        """根据ID异步获取记录

        Args:
            id_value: 记录ID

        Returns:
            T | None: 查询到的模型对象,不存在则返回None
        """
        pass

    @abstractmethod
    async def create(self, data: dict[str, Any]) -> T:
        """异步创建新记录

        Args:
            data: 记录数据字典

        Returns:
            T: 创建的模型对象
        """
        pass

    @abstractmethod
    async def update(self, id_value: int, data: dict[str, Any]) -> T | None:
        """异步更新记录

        Args:
            id_value: 记录ID
            data: 要更新的数据字典

        Returns:
            T | None: 更新后的模型对象,不存在则返回None
        """
        pass

    @abstractmethod
    async def delete(self, id_value: int) -> bool:
        """异步删除记录

        Args:
            id_value: 记录ID

        Returns:
            bool: 删除成功返回True,记录不存在返回False
        """
        pass


__all__ = (
    # 异步接口
    'IAsyncConnectionManager',
    'IAsyncRepository',
    'IAsyncSessionProvider',
    # 同步接口
    'IConnectionManager',
    'IRepository',
    'ISessionProvider',
)
