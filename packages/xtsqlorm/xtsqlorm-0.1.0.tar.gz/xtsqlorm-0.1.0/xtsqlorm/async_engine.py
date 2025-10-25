#!/usr/bin/env python3
"""
==============================================================
Description  : 异步连接引擎管理 - 纯粹的异步连接池和引擎管理
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-24 16:30:00
Github       : https://github.com/sandorn/xtsqlorm

本模块提供异步数据库连接引擎管理功能:
- AsyncConnectionManager: 异步连接管理器,只负责异步连接层面的操作

职责边界:
✅ 负责: 创建异步引擎、管理连接池、测试连接、释放资源
❌ 不负责: Session管理、事务管理、SQL执行
==============================================================
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from xtlog import mylog

from .cfg import connect_str
from .protocols import IAsyncConnectionManager


class AsyncConnectionManager(IAsyncConnectionManager):
    """异步连接管理器 - 只负责异步连接池和引擎管理

    职责:
    - 创建和管理SQLAlchemy异步引擎
    - 管理异步连接池配置
    - 测试异步连接状态
    - 释放异步连接资源

    不负责:
    - ❌ Session管理(由AsyncSessionProvider负责)
    - ❌ 事务管理(由AsyncSessionProvider负责)
    - ❌ SQL执行(由AsyncSession直接执行)

    Example:
        >>> # 创建异步连接管理器
        >>> async_conn_mgr = AsyncConnectionManager(db_key='default')
        >>> # 测试连接
        >>> if await async_conn_mgr.ping():
        ...     print('连接正常')
        >>> # 获取引擎
        >>> engine = async_conn_mgr.engine
        >>> # 释放资源
        >>> await async_conn_mgr.dispose()
    """

    def __init__(
        self,
        db_key: str = 'default',
        url: str | None = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False,
        **kwargs: Any,
    ):
        """初始化异步连接管理器

        Args:
            db_key: 数据库配置键,用于从配置文件获取连接信息
            url: 数据库连接URL,如果提供则优先使用(需要是异步驱动URL)
            pool_size: 连接池大小,默认5
            max_overflow: 最大溢出连接数,默认10
            pool_timeout: 连接超时时间(秒),默认30
            pool_recycle: 连接回收时间(秒),默认3600(1小时)
            echo: 是否打印SQL日志,默认False
            **kwargs: 其他SQLAlchemy引擎参数
        """
        if not url:
            url = connect_str(db_key, odbc='async')

        self._engine = create_async_engine(
            url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            echo=echo,
            pool_pre_ping=True,  # 自动检测失效连接
            **kwargs,
        )
        mylog.success(f'AsyncConnectionManager | 异步引擎已初始化: {self._engine.url}')

    def __str__(self) -> str:
        """字符串表示"""
        return f'AsyncConnectionManager({self._engine.url})'

    def __repr__(self) -> str:
        """详细表示"""
        return f'AsyncConnectionManager(url={self._engine.url!r})'

    @property
    def engine(self) -> AsyncEngine:
        """获取SQLAlchemy异步引擎对象

        Returns:
            AsyncEngine: SQLAlchemy异步引擎实例
        """
        return self._engine

    async def ping(self) -> bool:
        """测试异步数据库连接是否正常

        Returns:
            bool: 连接正常返回True,否则返回False

        Example:
            >>> async_conn_mgr = AsyncConnectionManager(db_key='default')
            >>> if await async_conn_mgr.ping():
            ...     print('异步数据库连接正常')
        """
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text('SELECT 1'))
            return True
        except Exception as e:
            mylog.error(f'AsyncConnectionManager@ping | 异步连接测试失败: {e}')
            return False

    async def dispose(self) -> None:
        """释放所有异步数据库连接资源

        关闭异步连接池中的所有连接,释放资源。
        通常在应用程序关闭时调用。

        Example:
            >>> async_conn_mgr = AsyncConnectionManager()
            >>> # ... 使用连接 ...
            >>> await async_conn_mgr.dispose()  # 应用关闭时释放资源
        """
        if hasattr(self, '_engine'):
            await self._engine.dispose()
            mylog.info('AsyncConnectionManager@dispose | 异步连接资源已释放')

    @property
    def pool_status(self) -> dict[str, Any]:
        """获取异步连接池状态信息

        Returns:
            dict: 连接池状态信息
                - size: 连接池大小
                - checked_out: 已签出的连接数
                - overflow: 溢出连接数
                - checked_in: 已签入的连接数

        Example:
            >>> async_conn_mgr = AsyncConnectionManager()
            >>> status = async_conn_mgr.pool_status
            >>> print(f'连接池大小: {status["size"]}')
            >>> print(f'活跃连接数: {status["checked_out"]}')
        """
        if not hasattr(self, '_engine'):
            return {}

        pool = getattr(self._engine, 'pool', None)
        if pool is None:
            return {}

        status = {}
        # 使用公共属性/方法,避免依赖私有API
        for k, attr in [
            ('size', 'size'),
            ('checked_out', 'checkedout'),
            ('overflow', 'overflow'),
            ('checked_in', 'checkedin'),
        ]:
            func = getattr(pool, attr, None)
            if callable(func):
                try:
                    status[k] = func()
                except Exception:
                    status[k] = None
            else:
                status[k] = None
        return status


__all__ = ['AsyncConnectionManager']
