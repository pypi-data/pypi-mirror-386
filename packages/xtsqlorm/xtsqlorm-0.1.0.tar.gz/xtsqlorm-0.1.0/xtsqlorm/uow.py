#!/usr/bin/env python3
"""
==============================================================
Description  : 工作单元模式 - 管理复杂事务边界
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-24 15:00:00
Github       : https://github.com/sandorn/xtsqlorm

本模块提供工作单元模式实现:
- UnitOfWork: 工作单元,管理一组相关操作的事务边界

适用场景:
- 需要在一个事务中操作多个表
- 复杂的业务逻辑需要明确的事务边界
- 多个仓储需要共享同一个事务
==============================================================
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from xtlog import mylog as log

from .protocols import ISessionProvider
from .repository import Repository

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class UnitOfWork:
    """工作单元 - 管理一组相关操作的事务边界

    工作单元模式(Unit of Work Pattern)用于:
    - 管理多个仓储的事务一致性
    - 确保所有操作在同一个事务中
    - 提供明确的事务边界

    优势:
    - 事务边界清晰
    - 多表操作原子性
    - 业务逻辑内聚

    使用示例:
        >>> # 创建工作单元
        >>> from xtsqlorm import UnitOfWork, create_session_provider
        >>> provider = create_session_provider(db_key='default')
        >>> # 在同一事务中操作多个表
        >>> with UnitOfWork(provider) as uow:
        ...     # 获取多个仓储
        ...     user_repo = uow.repository(User)
        ...     order_repo = uow.repository(Order)
        ...
        ...     # 在同一事务中执行多个操作
        ...     user = user_repo.get_by_id_in_session(1, uow.session)
        ...     order = order_repo.create_in_session({'user_id': user.id, 'amount': 100, 'status': 'pending'}, uow.session)
        ...
        ...     # 所有操作自动提交
        >>> # 异常时自动回滚
        >>> try:
        ...     with UnitOfWork(provider) as uow:
        ...         user_repo = uow.repository(User)
        ...         user = user_repo.create_in_session({'name': 'Invalid'}, uow.session)
        ...         raise ValueError('测试异常')
        ... except ValueError:
        ...     pass  # 所有操作已自动回滚
    """

    def __init__(self, session_provider: ISessionProvider):
        """初始化工作单元

        Args:
            session_provider: 会话提供者实例
        """
        self._session_provider = session_provider
        self._session: Session | None = None
        self._repositories: dict[type, Repository] = {}
        log.debug('UnitOfWork | 工作单元已创建')

    def __enter__(self) -> UnitOfWork:
        """进入上下文管理器

        Returns:
            UnitOfWork: 工作单元实例
        """
        self._session = self._session_provider.create_session()
        log.info('UnitOfWork | 工作单元事务开始')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器

        自动提交或回滚事务,并关闭session。

        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常追踪
        """
        if self._session:
            try:
                if exc_type is None:
                    self._session.commit()
                    log.success('UnitOfWork | 工作单元事务提交成功')
                else:
                    self._session.rollback()
                    log.warning(f'UnitOfWork | 工作单元事务回滚: {exc_type.__name__}')
            finally:
                self._session.close()
                log.debug('UnitOfWork | 工作单元已关闭')

    @property
    def session(self) -> Session:
        """获取当前事务的session

        Returns:
            Session: 当前工作单元的session对象

        Raises:
            RuntimeError: 如果工作单元未启动

        Example:
            >>> with UnitOfWork(provider) as uow:
            ...     session = uow.session
            ...     user = session.get(User, 1)
        """
        if self._session is None:
            raise RuntimeError('UnitOfWork未启动,请在with语句中使用')
        return self._session

    def repository[T](self, model: type[T]) -> Repository[T]:
        """获取指定模型的仓储

        为每个模型类创建一个仓储实例,该仓储使用当前工作单元的session。
        仓储实例会被缓存,同一个模型类在同一个工作单元中只会创建一次。

        Args:
            model: ORM模型类

        Returns:
            Repository[T]: 模型对应的仓储实例

        Example:
            >>> with UnitOfWork(provider) as uow:
            ...     user_repo = uow.repository(User)
            ...     order_repo = uow.repository(Order)
            ...
            ...     # 使用仓储操作数据
            ...     user = user_repo.get_by_id_in_session(1, uow.session)
            ...     order = order_repo.create_in_session({...}, uow.session)
        """
        # 检查是否已创建该模型的仓储
        if model in self._repositories:
            return self._repositories[model]

        # 创建一个临时的session_provider,返回当前UoW的session
        class _UoWSessionProvider(ISessionProvider):
            """工作单元内部的Session提供者

            这个内部类确保所有仓储操作都使用同一个session
            """

            def __init__(self, session: Session):
                self._session = session

            def create_session(self) -> Session:
                return self._session

            @contextmanager
            def transaction(self):
                # UoW内部不创建新事务,直接使用当前session
                yield self._session

        # 创建仓储实例
        provider = _UoWSessionProvider(self.session)
        repo = Repository(model, provider)

        # 缓存仓储实例
        self._repositories[model] = repo

        log.debug(f'UnitOfWork | 创建仓储: {model.__name__}')
        return repo

    def commit(self):
        """显式提交事务

        通常不需要手动调用,退出上下文管理器时会自动提交。
        此方法用于需要在工作单元中途提交的场景。

        Example:
            >>> with UnitOfWork(provider) as uow:
            ...     user_repo = uow.repository(User)
            ...     user = user_repo.create_in_session({'name': 'Alice'}, uow.session)
            ...     uow.commit()  # 手动提交
            ...     # 继续其他操作...
        """
        if self._session:
            self._session.commit()
            log.info('UnitOfWork | 手动提交事务')

    def rollback(self):
        """显式回滚事务

        通常不需要手动调用,异常时会自动回滚。
        此方法用于需要在工作单元中途回滚的场景。

        Example:
            >>> with UnitOfWork(provider) as uow:
            ...     user_repo = uow.repository(User)
            ...     user = user_repo.create_in_session({'name': 'Alice'}, uow.session)
            ...     # 发现问题,需要回滚
            ...     uow.rollback()
        """
        if self._session:
            self._session.rollback()
            log.warning('UnitOfWork | 手动回滚事务')


__all__ = ['UnitOfWork']
