#!/usr/bin/env python3
"""
==============================================================
Description  : 通用仓储模式 - 标准的CRUD操作实现
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-24 15:00:00
Github       : https://github.com/sandorn/xtsqlorm

本模块提供通用仓储模式实现:
- Repository[T]: 通用仓储基类,提供标准CRUD操作

设计原则:
- 统一的数据访问接口
- 自动事务管理
- 易于测试(依赖抽象接口)
- 可扩展(子类可添加特定方法)
==============================================================
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session
from xtlog import mylog as log

from .protocols import IRepository, ISessionProvider

if TYPE_CHECKING:
    pass


class Repository[T](IRepository[T]):
    """通用仓储基类 - 提供标准CRUD操作

    优势:
    - 统一的数据访问接口
    - 自动事务管理
    - 易于测试(依赖抽象接口)
    - 可扩展(子类可添加特定方法)

    Type Parameters:
        T: ORM模型类型

    使用示例:
        >>> # 创建仓储
        >>> from xtsqlorm import User
        >>> user_repo = Repository(User, session_provider)
        >>> # CRUD操作(自动事务)
        >>> user = user_repo.get_by_id(1)
        >>> new_user = user_repo.create({'name': 'Alice', 'email': 'alice@example.com'})
        >>> updated = user_repo.update(1, {'name': 'Bob'})
        >>> deleted = user_repo.delete(1)
        >>> # 查询所有
        >>> all_users = user_repo.get_all(limit=10)
        >>> count = user_repo.count()
    """

    def __init__(
        self,
        model: type[T],
        session_provider: ISessionProvider,
    ):
        """初始化仓储

        Args:
            model: ORM模型类
            session_provider: 会话提供者(实现ISessionProvider接口)
        """
        self._model = model
        self._session_provider = session_provider
        self._model_name = model.__name__
        log.success(f'Repository[{self._model_name}] | 仓储已初始化')

    def __str__(self) -> str:
        """字符串表示"""
        return f'Repository[{self._model_name}]'

    def __repr__(self) -> str:
        """详细表示"""
        return f'Repository(model={self._model_name}, provider={self._session_provider})'

    # ============ 基础CRUD操作(自动事务管理)============

    def get_by_id(self, id_value: int) -> T | None:
        """根据ID获取记录(自动事务)

        Args:
            id_value: 记录ID

        Returns:
            T | None: 查询到的模型对象,不存在则返回None

        Example:
            >>> user = user_repo.get_by_id(1)
            >>> if user:
            ...     print(f'找到用户: {user.name}')
        """
        with self._session_provider.transaction() as session:
            instance = session.get(self._model, id_value)
            if instance:
                session.refresh(instance)
                session.expunge(instance)
            return instance

    def create(self, data: dict[str, Any]) -> T:
        """创建记录(自动事务)

        Args:
            data: 记录数据字典

        Returns:
            T: 创建的模型对象

        Example:
            >>> user = user_repo.create({'name': 'Alice', 'email': 'alice@example.com'})
            >>> print(f'创建用户ID: {user.id}')
        """
        with self._session_provider.transaction() as session:
            instance = self._model(**data)
            session.add(instance)
            session.flush()
            session.refresh(instance)
            session.expunge(instance)
            return instance

    def update(self, id_value: int, data: dict[str, Any]) -> T | None:
        """更新记录(自动事务)

        Args:
            id_value: 记录ID
            data: 要更新的数据字典

        Returns:
            T | None: 更新后的模型对象,不存在则返回None

        Example:
            >>> updated_user = user_repo.update(1, {'name': 'Bob'})
            >>> if updated_user:
            ...     print(f'更新成功: {updated_user.name}')
        """
        with self._session_provider.transaction() as session:
            instance = session.get(self._model, id_value)
            if instance:
                for key, value in data.items():
                    setattr(instance, key, value)
                session.flush()
                session.refresh(instance)
                session.expunge(instance)
            return instance

    def delete(self, id_value: int) -> bool:
        """删除记录(自动事务)

        Args:
            id_value: 记录ID

        Returns:
            bool: 删除成功返回True,记录不存在返回False

        Example:
            >>> if user_repo.delete(1):
            ...     print('删除成功')
            ... else:
            ...     print('记录不存在')
        """
        with self._session_provider.transaction() as session:
            instance = session.get(self._model, id_value)
            if instance:
                session.delete(instance)
                return True
            return False

    # ============ 批量查询操作 ============

    def get_all(self, limit: int | None = None, offset: int | None = None) -> list[T]:
        """获取所有记录

        Args:
            limit: 限制返回数量
            offset: 跳过记录数

        Returns:
            list[T]: 模型对象列表

        Example:
            >>> # 获取所有用户
            >>> all_users = user_repo.get_all()
            >>> # 分页查询
            >>> page_users = user_repo.get_all(limit=10, offset=20)
        """
        with self._session_provider.transaction() as session:
            query = session.query(self._model)
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            results = query.all()
            # 分离对象，允许在事务外访问
            for instance in results:
                session.refresh(instance)
                session.expunge(instance)
            return results

    def count(self) -> int:
        """统计记录总数

        Returns:
            int: 记录总数

        Example:
            >>> total = user_repo.count()
            >>> print(f'共有 {total} 条记录')
        """
        with self._session_provider.transaction() as session:
            return session.query(self._model).count()

    def exists(self, id_value: int) -> bool:
        """检查记录是否存在

        Args:
            id_value: 记录ID

        Returns:
            bool: 存在返回True,否则返回False

        Example:
            >>> if user_repo.exists(1):
            ...     print('用户存在')
        """
        with self._session_provider.transaction() as session:
            return session.query(self._model).filter(self._model.id == id_value).count() > 0  # type: ignore[attr-defined]

    # ============ 高级用法: 外部事务管理 ============

    def get_by_id_in_session(self, id_value: int, session: Session) -> T | None:
        """在指定session中获取记录(外部事务)

        使用场景: 需要在同一事务中执行多个操作

        Args:
            id_value: 记录ID
            session: 外部提供的Session对象

        Returns:
            T | None: 查询到的模型对象,不存在则返回None

        Example:
            >>> with session_provider.transaction() as session:
            ...     user = user_repo.get_by_id_in_session(1, session)
            ...     order = order_repo.create_in_session({'user_id': user.id, 'amount': 100}, session)
            ...     # 统一提交
        """
        return session.get(self._model, id_value)

    def create_in_session(self, data: dict[str, Any], session: Session) -> T:
        """在指定session中创建记录(外部事务)

        Args:
            data: 记录数据字典
            session: 外部提供的Session对象

        Returns:
            T: 创建的模型对象
        """
        instance = self._model(**data)
        session.add(instance)
        return instance

    def update_in_session(self, id_value: int, data: dict[str, Any], session: Session) -> T | None:
        """在指定session中更新记录(外部事务)

        Args:
            id_value: 记录ID
            data: 要更新的数据字典
            session: 外部提供的Session对象

        Returns:
            T | None: 更新后的模型对象,不存在则返回None
        """
        instance = session.get(self._model, id_value)
        if instance:
            for key, value in data.items():
                setattr(instance, key, value)
        return instance

    def delete_in_session(self, id_value: int, session: Session) -> bool:
        """在指定session中删除记录(外部事务)

        Args:
            id_value: 记录ID
            session: 外部提供的Session对象

        Returns:
            bool: 删除成功返回True,记录不存在返回False
        """
        instance = session.get(self._model, id_value)
        if instance:
            session.delete(instance)
            return True
        return False


__all__ = ['Repository']
