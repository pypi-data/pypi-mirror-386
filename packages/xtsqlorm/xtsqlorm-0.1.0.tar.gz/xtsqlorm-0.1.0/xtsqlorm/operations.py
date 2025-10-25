#!/usr/bin/env python3
"""
==============================================================
Description  : ORM操作类 - 在Repository基础上添加高级功能
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-24 18:45:00
Github       : https://github.com/sandorn/xtsqlorm

本模块提供ORM操作类,在Repository基础上扩展高级功能:
- OrmOperations: 同步ORM操作(继承Repository,添加高级功能)
- AsyncOrmOperations: 异步ORM操作(组合AsyncRepository,添加高级功能)

设计模式:
- OrmOperations: 继承模式(Inheritance) - 直接继承Repository
- AsyncOrmOperations: 组合模式(Composition) - 委托给AsyncRepository
  (组合模式避免循环依赖,同时保持接口一致性)

高级功能包括:
- 数据验证(Pydantic集成)
- 查询缓存
- 分页查询
- 批量操作
- 统计分析
- 数据导出(Pandas)
- 原生SQL执行
==============================================================
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

import pandas as pd
from pydantic import BaseModel as PydanticModel, ValidationError
from sqlalchemy import and_, func, or_, text
from sqlalchemy.orm import Query
from xtlog import mylog as log

from .protocols import IAsyncSessionProvider, ISessionProvider
from .repository import Repository

if TYPE_CHECKING:
    pass

# ============ 同步操作类 ============


class OrmOperations[T](Repository[T]):
    """ORM操作类 - 继承Repository,添加高级功能

    继承自Repository,在标准CRUD操作基础上提供:
    - 数据验证(Pydantic集成)
    - 查询缓存
    - 分页查询
    - 批量操作优化
    - 统计分析
    - 数据导出(Pandas)
    - 原生SQL执行
    - 复杂条件查询

    Type Parameters:
        T: ORM模型类型

    使用示例:
        >>> # 创建ORM操作对象
        >>> from xtsqlorm import create_orm_operations, User
        >>> ops = create_orm_operations(User, db_key='default')
        >>> # 使用基础CRUD(继承自Repository)
        >>> user = ops.get_by_id(1)
        >>> new_user = ops.create({'name': 'Alice'})
        >>> # 使用高级功能
        >>> page_data, total = ops.get_paginated(page=1, page_size=10)
        >>> stats = ops.get_field_stats('age')
        >>> df = ops.export_to_dataframe()
    """

    def __init__(
        self,
        model: type[T],
        session_provider: ISessionProvider,
        validator_model: type[PydanticModel] | None = None,
        cache_enabled: bool = True,
    ):
        """初始化ORM操作类

        Args:
            model: ORM模型类
            session_provider: 会话提供者(实现ISessionProvider接口)
            validator_model: Pydantic验证模型(可选)
            cache_enabled: 是否启用查询缓存,默认True
        """
        super().__init__(model, session_provider)
        self._validator_model = validator_model
        self._cache_enabled = cache_enabled
        self._query_cache: dict[str, Any] = {}
        log.success(f'OrmOperations[{self._model_name}] | ORM操作对象已初始化')

    # ============ 数据验证 ============

    def _validate_data(self, data_dict: dict[str, Any]) -> dict[str, Any]:
        """使用Pydantic模型验证数据

        Args:
            data_dict: 要验证的数据字典

        Returns:
            dict: 验证后的数据字典

        Raises:
            ValueError: 数据验证失败
        """
        if self._validator_model:
            try:
                validated_data = self._validator_model(**data_dict)
                return validated_data.dict(exclude_unset=True)
            except ValidationError as e:
                log.error(f'OrmOperations[{self._model_name}] | 数据验证失败: {e}')
                raise ValueError(f'数据验证失败: {e}') from e
        return data_dict

    # ============ 缓存管理 ============

    def clear_cache(self) -> None:
        """清空查询缓存

        在执行创建、更新、删除操作后,应调用此方法清除缓存。

        Example:
            >>> ops.create({'name': 'Alice'})
            >>> ops.clear_cache()  # 清除缓存
        """
        self._query_cache.clear()
        log.debug(f'OrmOperations[{self._model_name}] | 缓存已清空')

    # ============ 重写基础CRUD方法(添加缓存和验证)============

    def get_by_id(self, id_value: int) -> T | None:
        """根据ID获取记录(带缓存)

        重写Repository的方法,添加缓存支持。

        Args:
            id_value: 记录ID

        Returns:
            T | None: 查询到的模型对象,不存在则返回None
        """
        if self._cache_enabled:
            cache_key = f'id_{id_value}'
            if cache_key in self._query_cache:
                log.debug(f'OrmOperations[{self._model_name}] | 从缓存获取: {cache_key}')
                return self._query_cache[cache_key]

        result = super().get_by_id(id_value)

        if self._cache_enabled and result:
            cache_key = f'id_{id_value}'
            self._query_cache[cache_key] = result

        return result

    def create(self, data: dict[str, Any]) -> T:
        """创建记录(带验证)

        重写Repository的方法,添加数据验证和缓存清理。

        Args:
            data: 记录数据字典

        Returns:
            T: 创建的模型对象
        """
        validated_data = self._validate_data(data)
        result = super().create(validated_data)

        if self._cache_enabled:
            self.clear_cache()

        return result

    def update(self, id_value: int, data: dict[str, Any]) -> T | None:
        """更新记录(带验证)

        重写Repository的方法,添加数据验证和缓存清理。

        Args:
            id_value: 记录ID
            data: 要更新的数据字典

        Returns:
            T | None: 更新后的模型对象,不存在则返回None
        """
        validated_data = self._validate_data(data)
        result = super().update(id_value, validated_data)

        if self._cache_enabled:
            self.clear_cache()

        return result

    def delete(self, id_value: int) -> bool:
        """删除记录(带缓存清理)

        重写Repository的方法,添加缓存清理。

        Args:
            id_value: 记录ID

        Returns:
            bool: 删除成功返回True,记录不存在返回False
        """
        result = super().delete(id_value)

        if self._cache_enabled and result:
            self.clear_cache()

        return result

    # ============ 高级查询方法 ============

    def get_one(self, where_dict: dict[str, Any] | None = None) -> T | None:
        """获取符合条件的单条记录

        Args:
            where_dict: 查询条件字典

        Returns:
            T | None: 查询到的模型对象,不存在则返回None

        Example:
            >>> user = ops.get_one({'email': 'alice@example.com'})
        """
        with self._session_provider.transaction() as session:
            query = session.query(self._model)
            if where_dict:
                query = query.filter_by(**where_dict)
            instance = query.first()
            if instance:
                session.refresh(instance)
                session.expunge(instance)
            return instance

    def get_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        where_dict: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_dir: Literal['asc', 'desc'] = 'asc',
    ) -> tuple[list[T], int]:
        """分页查询记录

        Args:
            page: 页码,从1开始
            page_size: 每页记录数
            where_dict: 查询条件字典
            order_by: 排序字段名
            order_dir: 排序方向,'asc'或'desc'

        Returns:
            tuple: (查询到的模型对象列表, 总记录数)

        Example:
            >>> results, total = ops.get_paginated(page=1, page_size=10, where_dict={'status': 'active'}, order_by='created_at', order_dir='desc')
            >>> print(f'第1页: {len(results)}条, 总共: {total}条')
        """
        with self._session_provider.transaction() as session:
            # 构建基础查询
            query = session.query(self._model)
            if where_dict:
                query = query.filter_by(**where_dict)

            # 计算总记录数
            total_count = query.count()

            # 排序
            if order_by:
                order_field = getattr(self._model, order_by)
                query = query.order_by(order_field.desc()) if order_dir == 'desc' else query.order_by(order_field)

            # 分页
            offset = (page - 1) * page_size
            result = query.offset(offset).limit(page_size).all()

            # 分离对象，允许在事务外访问
            for instance in result:
                session.refresh(instance)
                session.expunge(instance)

            return result, total_count

    def advanced_query(
        self,
        filters: list[Any] | None = None,
        order_by: list[Any] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Query:
        """构建高级查询

        Args:
            filters: SQLAlchemy过滤条件列表
            order_by: SQLAlchemy排序字段列表
            limit: 限制返回数量
            offset: 跳过记录数

        Returns:
            Query: SQLAlchemy Query对象

        Example:
            >>> from sqlalchemy import and_
            >>> query = ops.advanced_query(filters=[User.age > 18, User.status == 'active'], order_by=[User.created_at.desc()], limit=10)
            >>> results = query.all()
        """
        with self._session_provider.transaction() as session:
            query = session.query(self._model)

            if filters:
                query = query.filter(*filters)
            if order_by:
                query = query.order_by(*order_by)
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)

            return query

    def filter_by_conditions(
        self,
        conditions: list[dict[str, Any]],
        limit: int | None = None,
    ) -> list[T]:
        """多条件查询,支持复杂OR逻辑

        Args:
            conditions: 条件字典列表,多个字典之间为OR关系,字典内为AND关系
            limit: 限制返回的记录数量

        Returns:
            list[T]: 查询结果列表

        Example:
            >>> # 查询: (name='Alice' AND age=25) OR (name='Bob' AND age=30)
            >>> results = ops.filter_by_conditions([{'name': 'Alice', 'age': 25}, {'name': 'Bob', 'age': 30}])
        """
        with self._session_provider.transaction() as session:
            query = session.query(self._model)

            if conditions:
                or_conditions = []
                for condition in conditions:
                    and_conditions = []
                    for key, value in condition.items():
                        and_conditions.append(getattr(self._model, key) == value)
                    if and_conditions:
                        or_conditions.append(and_(*and_conditions))

                if or_conditions:
                    query = query.filter(or_(*or_conditions))

            if limit is not None:
                query = query.limit(limit)

            results = query.all()

            # 分离对象，允许在事务外访问
            for instance in results:
                session.refresh(instance)
                session.expunge(instance)

            return results

    # ============ 批量操作 ============

    def bulk_create(self, data_list: list[dict[str, Any]]) -> list[T]:
        """批量创建记录

        Args:
            data_list: 记录数据字典列表

        Returns:
            list[T]: 创建的模型对象列表

        Example:
            >>> users = ops.bulk_create([{'name': 'Alice', 'age': 25}, {'name': 'Bob', 'age': 30}])
        """
        with self._session_provider.transaction() as session:
            # 验证数据并创建实例
            validated_data_list = [self._validate_data(data) for data in data_list]
            instances = [self._model(**data) for data in validated_data_list]

            # 批量添加
            session.add_all(instances)
            session.flush()

            # 刷新并分离实例
            for instance in instances:
                session.refresh(instance)
                session.expunge(instance)

            if self._cache_enabled:
                self.clear_cache()

            return instances

    def bulk_create_optimized(
        self,
        data_list: list[dict[str, Any]],
        batch_size: int = 1000,
    ) -> list[T]:
        """优化的批量创建(分批提交)

        适用于大量数据插入,分批刷新避免内存问题。

        Args:
            data_list: 记录数据字典列表
            batch_size: 每批次大小

        Returns:
            list[T]: 创建的模型对象列表
        """
        instances = []

        with self._session_provider.transaction() as session:
            for i in range(0, len(data_list), batch_size):
                batch_data = data_list[i : i + batch_size]
                batch_instances = [self._model(**self._validate_data(data)) for data in batch_data]
                session.add_all(batch_instances)
                instances.extend(batch_instances)

                # 分批刷新,避免内存问题
                if i % batch_size == 0:
                    session.flush()

        if self._cache_enabled:
            self.clear_cache()

        return instances

    def bulk_update(
        self,
        data_list: list[dict[str, Any]],
        id_key: str = 'id',
    ) -> int:
        """批量更新记录

        Args:
            data_list: 更新数据字典列表,每个字典必须包含id_key字段
            id_key: 用于定位记录的字段名,默认为'id'

        Returns:
            int: 更新的记录数量

        Example:
            >>> count = ops.bulk_update([{'id': 1, 'name': 'Alice Updated'}, {'id': 2, 'name': 'Bob Updated'}])
        """
        updated_count = 0

        with self._session_provider.transaction() as session:
            for data in data_list:
                if id_key not in data:
                    continue

                id_value = data[id_key]
                update_data = {k: v for k, v in data.items() if k != id_key}

                instance = session.get(self._model, id_value)
                if instance:
                    for key, value in update_data.items():
                        setattr(instance, key, value)
                    updated_count += 1

        if self._cache_enabled and updated_count > 0:
            self.clear_cache()

        return updated_count

    # ============ 统计分析 ============

    def get_field_stats(self, field_name: str) -> dict[str, Any]:
        """获取字段统计信息

        Args:
            field_name: 字段名

        Returns:
            dict: 统计信息,包括count, min, max, avg

        Example:
            >>> stats = ops.get_field_stats('age')
            >>> print(f'平均年龄: {stats["avg"]}')
        """
        with self._session_provider.transaction() as session:
            field = getattr(self._model, field_name)

            stats = session.query(func.count(field), func.min(field), func.max(field), func.avg(field)).first()

            return {
                'count': stats[0] if stats else 0,
                'min': stats[1] if stats and len(stats) > 1 else None,
                'max': stats[2] if stats and len(stats) > 2 else None,
                'avg': float(stats[3]) if stats and len(stats) > 3 and stats[3] else 0.0,
            }

    # ============ 数据导出 ============

    def export_to_dataframe(
        self,
        columns: list[str] | None = None,
        filters: list[Any] | None = None,
    ) -> pd.DataFrame:
        """导出到Pandas DataFrame

        Args:
            columns: 要导出的列名列表,None表示导出所有列
            filters: SQLAlchemy过滤条件列表

        Returns:
            pd.DataFrame: Pandas DataFrame对象

        Example:
            >>> df = ops.export_to_dataframe(columns=['name', 'age'], filters=[User.age > 18])
            >>> df.to_csv('users.csv')
        """
        with self._session_provider.transaction() as session:
            if columns:
                query_columns = [getattr(self._model, col) for col in columns]
                query = session.query(*query_columns)
            else:
                query = session.query(self._model)

            if filters:
                query = query.filter(*filters)

            return pd.read_sql(query.statement, session.bind)

    def pd_get_dict(self) -> list[dict[str, Any]] | bool:
        """使用Pandas读取表数据并返回字典列表

        Returns:
            list[dict] | bool: 数据字典列表,如果没有数据则返回False

        Example:
            >>> data = ops.pd_get_dict()
            >>> if data:
            ...     print(f'读取了 {len(data)} 条记录')
        """
        with self._session_provider.transaction() as session:
            try:
                table_name = self._model.__tablename__  # type: ignore[attr-defined]
                result = pd.read_sql_table(table_name, con=session.bind)
                data_dict = result.to_dict(orient='records')

                if data_dict:
                    return data_dict

                log.warning(f'OrmOperations[{self._model_name}] | 表中没有数据')
                return False
            except Exception as e:
                log.error(f'OrmOperations[{self._model_name}] | Pandas读取失败: {e}')
                raise

    def pd_get_list(self, columns: list[str]) -> list[list[Any]] | bool:
        """使用Pandas读取表指定列并返回去重后的列表

        Args:
            columns: 要读取的列名列表

        Returns:
            list[list] | bool: 列表数据,如果没有数据则返回False

        Example:
            >>> data = ops.pd_get_list(['name', 'email'])
            >>> if data:
            ...     for name, email in data:
            ...         print(f'{name}: {email}')
        """
        with self._session_provider.transaction() as session:
            try:
                table_name = self._model.__tablename__  # type: ignore[attr-defined]
                result = pd.read_sql_table(table_name, con=session.bind)
                pd_list = result[columns].drop_duplicates().values.tolist()

                if pd_list:
                    return pd_list

                log.warning(f'OrmOperations[{self._model_name}] | 表中没有数据')
                return False
            except Exception as e:
                log.error(f'OrmOperations[{self._model_name}] | Pandas读取失败: {e}')
                raise

    # ============ 原生SQL执行 ============

    def execute_raw_sql(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """执行原生SQL语句

        Args:
            sql: SQL查询语句
            params: SQL参数绑定

        Returns:
            Any: 查询结果

        Example:
            >>> result = ops.execute_raw_sql('SELECT * FROM users WHERE age > :age', {'age': 18})
        """
        with self._session_provider.transaction() as session:
            return session.execute(text(sql), params or {})

    def from_statement(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
    ) -> list[T]:
        """执行原生SQL语句查询并映射到ORM模型

        Args:
            sql: 原生SQL查询语句
            params: SQL参数字典

        Returns:
            list[T]: 查询结果列表

        Example:
            >>> users = ops.from_statement('SELECT * FROM users WHERE age > :age', {'age': 18})
        """
        with self._session_provider.transaction() as session:
            sql_text = text(sql)
            query = session.query(self._model).from_statement(sql_text)  # type: ignore[arg-type]

            results = query.params(**params).all() if params else query.all()

            # 分离对象，允许在事务外访问
            for instance in results:
                session.refresh(instance)
                session.expunge(instance)

            return results


# ============ 异步操作类 ============


class AsyncOrmOperations[T]:
    """异步ORM操作类 - 委托AsyncRepository,添加高级功能

    通过组合AsyncRepository,在标准异步CRUD操作基础上提供:
    - 数据验证(Pydantic集成)
    - 查询缓存
    - 分页查询
    - 批量操作优化
    - 统计分析
    - 数据导出(Pandas)
    - 原生SQL执行
    - 复杂条件查询

    Type Parameters:
        T: ORM模型类型

    设计模式:
        使用组合模式(Composition)而非继承,在需要时委托给AsyncRepository实例。
        这样可以避免循环依赖,同时保持接口一致性。

    使用示例:
        >>> # 创建异步ORM操作对象
        >>> from xtsqlorm import AsyncOrmOperations
        >>> from xtsqlorm import create_async_session_provider, reflect_table_async
        >>> # 1. 反射表模型
        >>> user_model = await reflect_table_async('users', db_key='default')
        >>> # 2. 创建会话提供者
        >>> async_provider = create_async_session_provider(db_key='default')
        >>> # 3. 创建ORM操作对象
        >>> async_ops = AsyncOrmOperations(user_model, async_provider)
        >>> # 使用基础异步CRUD(委托给AsyncRepository)
        >>> user = await async_ops.get_by_id(1)
        >>> new_user = await async_ops.create({'name': 'Alice'})
        >>> # 使用高级功能
        >>> page_data, total = await async_ops.get_paginated(page=1, page_size=10)
        >>> stats = await async_ops.get_field_stats('age')
        >>> df = await async_ops.export_to_dataframe()
    """

    def __init__(
        self,
        model: type[T],
        session_provider: IAsyncSessionProvider,
        validator_model: type[PydanticModel] | None = None,
        cache_enabled: bool = True,
    ):
        """初始化异步ORM操作类

        Args:
            model: ORM模型类
            session_provider: 异步会话提供者(实现IAsyncSessionProvider接口),必需参数
            validator_model: Pydantic验证模型(可选)
            cache_enabled: 是否启用查询缓存,默认True

        Note:
            与同步版本OrmOperations保持一致,使用组合模式委托给AsyncRepository。
            session_provider是必需的,不能为None。
        """
        # 初始化属性
        self._model = model
        self._session_provider = session_provider
        self._model_name = model.__name__

        # 高级功能属性
        self._validator_model = validator_model
        self._cache_enabled = cache_enabled
        self._query_cache: dict[str, Any] = {}
        log.success(f'AsyncOrmOperations[{self._model_name}] | 异步ORM操作对象已初始化')

    # ============ 数据验证 ============

    def _validate_data(self, data_dict: dict[str, Any]) -> dict[str, Any]:
        """使用Pydantic模型验证数据

        Args:
            data_dict: 要验证的数据字典

        Returns:
            dict: 验证后的数据字典

        Raises:
            ValueError: 数据验证失败
        """
        if self._validator_model:
            try:
                validated_data = self._validator_model(**data_dict)
                return validated_data.dict(exclude_unset=True)
            except ValidationError as e:
                log.error(f'AsyncOrmOperations[{self._model_name}] | 数据验证失败: {e}')
                raise ValueError(f'数据验证失败: {e}') from e
        return data_dict

    # ============ 缓存管理 ============

    def clear_cache(self) -> None:
        """清空查询缓存

        在执行创建、更新、删除操作后,应调用此方法清除缓存。

        Example:
            >>> await async_ops.create({'name': 'Alice'})
            >>> async_ops.clear_cache()  # 清除缓存
        """
        self._query_cache.clear()
        log.debug(f'AsyncOrmOperations[{self._model_name}] | 缓存已清空')

    # ============ 基础异步CRUD操作(委托给AsyncRepository)============

    async def get_by_id(self, id_value: int) -> T | None:
        """根据ID异步获取记录(带缓存)

        委托给AsyncRepository,添加缓存支持。

        Args:
            id_value: 记录ID

        Returns:
            T | None: 查询到的模型对象,不存在则返回None
        """
        if self._cache_enabled:
            cache_key = f'id_{id_value}'
            if cache_key in self._query_cache:
                log.debug(f'AsyncOrmOperations[{self._model_name}] | 从缓存获取: {cache_key}')
                return self._query_cache[cache_key]

        # 委托给AsyncRepository
        from .async_repository import AsyncRepository

        repo = AsyncRepository(self._model, self._session_provider)
        result = await repo.get_by_id(id_value)

        if self._cache_enabled and result:
            cache_key = f'id_{id_value}'
            self._query_cache[cache_key] = result

        return result

    async def create(self, data: dict[str, Any]) -> T:
        """异步创建记录(带验证)

        委托给AsyncRepository,添加数据验证和缓存清理。

        Args:
            data: 记录数据字典

        Returns:
            T: 创建的模型对象
        """
        validated_data = self._validate_data(data)

        from .async_repository import AsyncRepository

        repo = AsyncRepository(self._model, self._session_provider)
        result = await repo.create(validated_data)

        if self._cache_enabled:
            self.clear_cache()

        return result

    async def update(self, id_value: int, data: dict[str, Any]) -> T | None:
        """异步更新记录(带验证)

        委托给AsyncRepository,添加数据验证和缓存清理。

        Args:
            id_value: 记录ID
            data: 要更新的数据字典

        Returns:
            T | None: 更新后的模型对象,不存在则返回None
        """
        validated_data = self._validate_data(data)

        from .async_repository import AsyncRepository

        repo = AsyncRepository(self._model, self._session_provider)
        result = await repo.update(id_value, validated_data)

        if self._cache_enabled:
            self.clear_cache()

        return result

    async def delete(self, id_value: int) -> bool:
        """异步删除记录(带缓存清理)

        委托给AsyncRepository,添加缓存清理。

        Args:
            id_value: 记录ID

        Returns:
            bool: 删除成功返回True,记录不存在返回False
        """
        from .async_repository import AsyncRepository

        repo = AsyncRepository(self._model, self._session_provider)
        result = await repo.delete(id_value)

        if self._cache_enabled and result:
            self.clear_cache()

        return result

    async def get_all(self, limit: int | None = None, offset: int | None = None) -> list[T]:
        """异步获取所有记录

        委托给AsyncRepository。

        Args:
            limit: 限制返回数量
            offset: 跳过记录数

        Returns:
            list[T]: 模型对象列表
        """
        from .async_repository import AsyncRepository

        repo = AsyncRepository(self._model, self._session_provider)
        return await repo.get_all(limit=limit, offset=offset)

    async def count(self) -> int:
        """异步统计记录总数

        委托给AsyncRepository。

        Returns:
            int: 记录总数
        """
        from .async_repository import AsyncRepository

        repo = AsyncRepository(self._model, self._session_provider)
        return await repo.count()

    # ============ 高级异步查询方法 ============

    async def get_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        where_dict: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_dir: Literal['asc', 'desc'] = 'asc',
    ) -> tuple[list[T], int]:
        """异步分页查询记录

        Args:
            page: 页码,从1开始
            page_size: 每页记录数
            where_dict: 查询条件字典
            order_by: 排序字段名
            order_dir: 排序方向,'asc'或'desc'

        Returns:
            tuple: (查询到的模型对象列表, 总记录数)

        Example:
            >>> results, total = await async_ops.get_paginated(page=1, page_size=10, where_dict={'status': 'active'}, order_by='created_at', order_dir='desc')
            >>> print(f'第1页: {len(results)}条, 总共: {total}条')
        """
        from sqlalchemy import select

        async with self._session_provider.transaction() as session:
            # 构建基础查询
            stmt = select(self._model)
            if where_dict:
                for key, value in where_dict.items():
                    stmt = stmt.where(getattr(self._model, key) == value)

            # 计算总记录数
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total_result = await session.execute(count_stmt)
            total_count = total_result.scalar() or 0

            # 排序
            if order_by:
                order_field = getattr(self._model, order_by)
                stmt = stmt.order_by(order_field.desc() if order_dir == 'desc' else order_field)

            # 分页
            offset_value = (page - 1) * page_size
            stmt = stmt.offset(offset_value).limit(page_size)

            # 执行查询
            result = await session.execute(stmt)
            instances = list(result.scalars().all())

            # 刷新并expunge所有实例
            for instance in instances:
                await session.refresh(instance)
                session.expunge(instance)

            return instances, total_count

    # ============ 批量异步操作 ============

    async def bulk_create(self, data_list: list[dict[str, Any]]) -> list[T]:
        """批量异步创建记录

        Args:
            data_list: 记录数据字典列表

        Returns:
            list[T]: 创建的模型对象列表

        Example:
            >>> users = await async_ops.bulk_create([{'name': 'Alice', 'age': 25}, {'name': 'Bob', 'age': 30}])
        """
        async with self._session_provider.transaction() as session:
            # 验证数据并创建实例
            validated_data_list = [self._validate_data(data) for data in data_list]
            instances = [self._model(**data) for data in validated_data_list]

            # 批量添加
            session.add_all(instances)
            await session.flush()

            # 刷新实例
            for instance in instances:
                await session.refresh(instance)
                session.expunge(instance)

            if self._cache_enabled:
                self.clear_cache()

            return instances

    # ============ 统计分析 ============

    async def get_field_stats(self, field_name: str) -> dict[str, Any]:
        """异步获取字段统计信息

        Args:
            field_name: 字段名

        Returns:
            dict: 统计信息,包括count, min, max, avg

        Example:
            >>> stats = await async_ops.get_field_stats('age')
            >>> print(f'平均年龄: {stats["avg"]}')
        """
        from sqlalchemy import select

        async with self._session_provider.transaction() as session:
            field = getattr(self._model, field_name)

            stmt = select(
                func.count(field),
                func.min(field),
                func.max(field),
                func.avg(field),
            )

            result = await session.execute(stmt)
            stats = result.first()

            return {
                'count': stats[0] if stats else 0,
                'min': stats[1] if stats and len(stats) > 1 else None,
                'max': stats[2] if stats and len(stats) > 2 else None,
                'avg': float(stats[3]) if stats and len(stats) > 3 and stats[3] else 0.0,
            }

    # ============ 数据导出 ============

    async def export_to_dataframe(
        self,
        columns: list[str] | None = None,
        filters: list[Any] | None = None,
    ) -> pd.DataFrame:
        """异步导出到Pandas DataFrame

        Args:
            columns: 要导出的列名列表,None表示导出所有列
            filters: SQLAlchemy过滤条件列表

        Returns:
            pd.DataFrame: Pandas DataFrame对象

        Example:
            >>> df = await async_ops.export_to_dataframe(columns=['name', 'age'], filters=[User.age > 18])
            >>> df.to_csv('users.csv')
        """
        from sqlalchemy import select

        async with self._session_provider.transaction() as session:
            if columns:
                query_columns = [getattr(self._model, col) for col in columns]
                stmt = select(*query_columns)
            else:
                stmt = select(self._model)

            if filters:
                stmt = stmt.where(*filters)

            # 执行查询并转换为DataFrame
            result = await session.execute(stmt)
            data = result.fetchall()

            # 构建DataFrame
            if columns:
                # 将数据转换为列表格式
                return pd.DataFrame([list(row) for row in data], columns=columns)  # type: ignore[arg-type]

            # 如果没有指定列,使用模型的所有列
            return pd.DataFrame([row._asdict() if hasattr(row, '_asdict') else dict(row._mapping) for row in data])

    # ============ 原生SQL执行 ============

    async def execute_raw_sql(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """异步执行原生SQL语句

        Args:
            sql: SQL查询语句
            params: SQL参数绑定

        Returns:
            Any: 查询结果

        Example:
            >>> result = await async_ops.execute_raw_sql('SELECT * FROM users WHERE age > :age', {'age': 18})
        """
        async with self._session_provider.transaction() as session:
            return await session.execute(text(sql), params or {})


__all__ = ['AsyncOrmOperations', 'OrmOperations']
