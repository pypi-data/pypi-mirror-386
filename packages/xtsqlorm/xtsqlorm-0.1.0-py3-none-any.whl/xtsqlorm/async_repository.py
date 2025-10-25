#!/usr/bin/env python3
"""
==============================================================
Description  : 异步通用仓储模式 - 标准的异步CRUD操作实现
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-24 16:40:00
Github       : https://github.com/sandorn/xtsqlorm

本模块提供异步通用仓储模式实现:
- AsyncRepository[T]: 异步通用仓储基类,提供标准异步CRUD操作

设计原则:
- 统一的异步数据访问接口
- 自动异步事务管理
- 易于测试(依赖抽象接口)
- 可扩展(子类可添加特定方法)
==============================================================
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from xtlog import mylog as log

from .protocols import IAsyncRepository, IAsyncSessionProvider

if TYPE_CHECKING:
    pass


class AsyncRepository[T](IAsyncRepository[T]):
    """异步通用仓储基类 - 提供标准异步CRUD操作

    优势:
    - 统一的异步数据访问接口
    - 自动异步事务管理
    - 易于测试(依赖抽象接口)
    - 可扩展(子类可添加特定方法)

    Type Parameters:
        T: ORM模型类型

    使用示例:
        >>> # 创建异步仓储
        >>> from xtsqlorm import User
        >>> user_repo = AsyncRepository(User, async_session_provider)
        >>> # 异步CRUD操作(自动事务)
        >>> user = await user_repo.get_by_id(1)
        >>> new_user = await user_repo.create({'name': 'Alice', 'email': 'alice@example.com'})
        >>> updated = await user_repo.update(1, {'name': 'Bob'})
        >>> deleted = await user_repo.delete(1)
        >>> # 查询所有
        >>> all_users = await user_repo.get_all(limit=10)
        >>> count = await user_repo.count()
    """

    def __init__(
        self,
        model: type[T],
        session_provider: IAsyncSessionProvider,
    ):
        """初始化异步仓储

        Args:
            model: ORM模型类
            session_provider: 异步会话提供者(实现IAsyncSessionProvider接口)
        """
        self._model = model
        self._session_provider = session_provider
        self._model_name = model.__name__
        log.success(f'AsyncRepository[{self._model_name}] | 异步仓储已初始化')

    def __str__(self) -> str:
        """字符串表示"""
        return f'AsyncRepository[{self._model_name}]'

    def __repr__(self) -> str:
        """详细表示"""
        return f'AsyncRepository(model={self._model_name}, provider={self._session_provider})'

    # ============ 基础异步CRUD操作(自动事务管理) ============

    async def get_by_id(self, id_value: int) -> T | None:
        """根据ID异步获取记录(自动事务)

        Args:
            id_value: 记录ID

        Returns:
            T | None: 查询到的模型对象,不存在则返回None

        Example:
            >>> user = await user_repo.get_by_id(1)
            >>> if user:
            ...     print(f'找到用户: {user.name}')
        """
        async with self._session_provider.transaction() as session:
            instance = await session.get(self._model, id_value)
            if instance:
                await session.refresh(instance)
                session.expunge(instance)
            return instance

    async def create(self, data: dict[str, Any]) -> T:
        """异步创建记录(自动事务)

        Args:
            data: 记录数据字典

        Returns:
            T: 创建的模型对象

        Example:
            >>> user = await user_repo.create({'name': 'Alice', 'email': 'alice@example.com'})
            >>> print(f'创建用户ID: {user.id}')
        """
        async with self._session_provider.transaction() as session:
            instance = self._model(**data)
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
            session.expunge(instance)
            return instance

    async def update(self, id_value: int, data: dict[str, Any]) -> T | None:
        """异步更新记录(自动事务)

        Args:
            id_value: 记录ID
            data: 要更新的数据字典

        Returns:
            T | None: 更新后的模型对象,不存在则返回None

        Example:
            >>> updated_user = await user_repo.update(1, {'name': 'Bob'})
            >>> if updated_user:
            ...     print(f'更新成功: {updated_user.name}')
        """
        async with self._session_provider.transaction() as session:
            instance = await session.get(self._model, id_value)
            if instance:
                for key, value in data.items():
                    setattr(instance, key, value)
                await session.flush()
                await session.refresh(instance)
                session.expunge(instance)
            return instance

    async def delete(self, id_value: int) -> bool:
        """异步删除记录(自动事务)

        Args:
            id_value: 记录ID

        Returns:
            bool: 删除成功返回True,记录不存在返回False

        Example:
            >>> if await user_repo.delete(1):
            ...     print('删除成功')
            ... else:
            ...     print('记录不存在')
        """
        async with self._session_provider.transaction() as session:
            instance = await session.get(self._model, id_value)
            if instance:
                await session.delete(instance)
                return True
            return False

    # ============ 批量异步查询操作 ============

    async def get_all(self, limit: int | None = None, offset: int | None = None) -> list[T]:
        """异步获取所有记录

        Args:
            limit: 限制返回数量
            offset: 跳过记录数

        Returns:
            list[T]: 模型对象列表

        Example:
            >>> # 获取所有用户
            >>> all_users = await user_repo.get_all()
            >>> # 分页查询
            >>> page_users = await user_repo.get_all(limit=10, offset=20)
        """
        async with self._session_provider.transaction() as session:
            stmt = select(self._model)
            if offset:
                stmt = stmt.offset(offset)
            if limit:
                stmt = stmt.limit(limit)
            result = await session.execute(stmt)
            instances = list(result.scalars().all())
            # 在session关闭前刷新所有实例，确保数据被加载
            for instance in instances:
                await session.refresh(instance)
            # 将对象从session中"expunge"，使其变为独立对象
            for instance in instances:
                session.expunge(instance)
            return instances

    async def count(self) -> int:
        """异步统计记录总数

        Returns:
            int: 记录总数

        Example:
            >>> total = await user_repo.count()
            >>> print(f'共有 {total} 条记录')
        """
        async with self._session_provider.transaction() as session:
            stmt = select(func.count()).select_from(self._model)
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def exists(self, id_value: int) -> bool:
        """异步检查记录是否存在

        Args:
            id_value: 记录ID

        Returns:
            bool: 存在返回True,否则返回False

        Example:
            >>> if await user_repo.exists(1):
            ...     print('用户存在')
        """
        async with self._session_provider.transaction() as session:
            stmt = select(func.count()).select_from(self._model).where(self._model.id == id_value)  # type: ignore[attr-defined]
            result = await session.execute(stmt)
            count = result.scalar() or 0
            return count > 0

    # ============ 高级用法: 外部异步事务管理 ============

    async def get_by_id_in_session(self, id_value: int, session: AsyncSession) -> T | None:
        """在指定session中异步获取记录(外部事务)

        使用场景: 需要在同一异步事务中执行多个操作

        Args:
            id_value: 记录ID
            session: 外部提供的AsyncSession对象

        Returns:
            T | None: 查询到的模型对象,不存在则返回None

        Example:
            >>> async with session_provider.transaction() as session:
            ...     user = await user_repo.get_by_id_in_session(1, session)
            ...     order = await order_repo.create_in_session({'user_id': user.id, 'amount': 100}, session)
            ...     # 统一提交
        """
        return await session.get(self._model, id_value)

    async def create_in_session(self, data: dict[str, Any], session: AsyncSession) -> T:
        """在指定session中异步创建记录(外部事务)

        Args:
            data: 记录数据字典
            session: 外部提供的AsyncSession对象

        Returns:
            T: 创建的模型对象
        """
        instance = self._model(**data)
        session.add(instance)
        return instance

    async def update_in_session(self, id_value: int, data: dict[str, Any], session: AsyncSession) -> T | None:
        """在指定session中异步更新记录(外部事务)

        Args:
            id_value: 记录ID
            data: 要更新的数据字典
            session: 外部提供的AsyncSession对象

        Returns:
            T | None: 更新后的模型对象,不存在则返回None
        """
        instance = await session.get(self._model, id_value)
        if instance:
            for key, value in data.items():
                setattr(instance, key, value)
        return instance

    async def delete_in_session(self, id_value: int, session: AsyncSession) -> bool:
        """在指定session中异步删除记录(外部事务)

        Args:
            id_value: 记录ID
            session: 外部提供的AsyncSession对象

        Returns:
            bool: 删除成功返回True,记录不存在返回False
        """
        instance = await session.get(self._model, id_value)
        if instance:
            await session.delete(instance)
            return True
        return False


__all__ = ['AsyncRepository']
