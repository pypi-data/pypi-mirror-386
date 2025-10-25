# !/usr/bin/env python3
"""
==============================================================
Description  : 数据库表工具函数模块
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-23 16:45:00
Github       : https://github.com/sandorn/xtsqlorm

本模块提供数据库表操作的工具函数,包括:
- reflect_table: 同步反射表结构
- reflect_table_async: 异步反射表结构
- get_or_create_table_model: 智能获取或创建表模型(支持反射和复制两种模式)
- generate_model_file: 生成模型文件
==============================================================
"""

from __future__ import annotations

import re
import subprocess  # noqa: S404
from typing import TYPE_CHECKING, Any, overload

from sqlalchemy import Table, inspect
from xtlog import mylog as log

from .base import BaseModel
from .cfg import connect_str

if TYPE_CHECKING:
    from .engine import ConnectionManager

    # 注意: 异步部分暂未完全整合到新架构,保留类型引用
    AsyncSqlConnection = Any


def validate_sql_identifier(identifier: str, identifier_type: str = '标识符') -> None:
    """验证SQL标识符(表名、列名等)的有效性,防止SQL注入和命令注入

    Args:
        identifier: 要验证的标识符
        identifier_type: 标识符类型描述,用于错误消息,默认为'标识符'

    Raises:
        ValueError: 当标识符无效时

    Example:
        >>> validate_sql_identifier('users')  # 有效
        >>> validate_sql_identifier('user_table_2024')  # 有效
        >>> validate_sql_identifier('users; DROP TABLE')  # 抛出 ValueError
    """
    # 只允许字母、数字、下划线,防止SQL注入和命令注入
    if not identifier or not isinstance(identifier, str) or not re.match(r'^[a-zA-Z0-9_]+$', identifier):
        raise ValueError(f'无效的{identifier_type}: {identifier}, {identifier_type}只能包含字母、数字和下划线')


def build_safe_command_args(base_url: str, tablename: str, output_file: str, **kwargs: Any) -> list[str]:
    """构建安全的命令参数列表,用于执行sqlacodegen等外部命令

    Args:
        base_url: 数据库连接URL
        tablename: 表名
        output_file: 输出文件路径
        **kwargs: 额外的命令参数,布尔值参数传递为标志,其他值参数传递为键值对

    Returns:
        list[str]: 安全的命令参数列表

    Example:
        >>> args = build_safe_command_args('mysql://user:pass@localhost/db', 'users', 'output.py', noindent=True, schema='public')
        >>> # 返回: ['sqlacodegen', 'mysql://...', '--tables', 'users',
        >>> #        '--outfile=output.py', '--noindent', '--schema=public']
    """
    # 构建基础命令参数
    cmd_args = ['sqlacodegen', base_url, '--tables', tablename, f'--outfile={output_file}']

    # 添加额外的sqlacodegen参数
    for key, value in kwargs.items():
        # 验证参数名,防止注入
        if not re.match(r'^[a-zA-Z0-9_-]+$', key):
            log.warning(f'build_safe_command_args | 跳过无效参数名: {key}')
            continue

        if value is True:
            # 布尔标志参数
            cmd_args.append(f'--{key}')
        elif value is not False and value is not None:
            # 键值对参数,对值进行安全处理
            safe_value = str(value).replace('\\', '').replace("'", '').replace('"', '')
            cmd_args.append(f'--{key}={safe_value}')

    return cmd_args


def execute_command_safely(cmd_args: list[str], mask_credentials: bool = True, echo: bool = False) -> subprocess.CompletedProcess:
    """安全执行外部命令并返回结果

    不使用shell=True以提高安全性,避免shell注入攻击。
    支持在日志中隐藏敏感信息(如数据库密码)。

    Args:
        cmd_args: 命令参数列表(已经过安全验证)
        mask_credentials: 是否在日志中隐藏URL中的凭据信息,默认为True
        echo: 是否打印命令详情到日志,默认为False

    Returns:
        subprocess.CompletedProcess: 命令执行结果对象

    Example:
        >>> result = execute_command_safely(['sqlacodegen', 'mysql://user:pass@localhost/db', '--tables', 'users'], echo=True)
        >>> # 日志输出: 执行命令: sqlacodegen mysql://user:********@localhost/db --tables users
        >>> result.returncode
        0
    """
    if echo:
        # 构建用于日志显示的安全命令字符串
        safe_cmd = []
        for arg in cmd_args:
            if mask_credentials and '://' in arg and '@' in arg:
                # 隐藏URL中的密码信息
                parts = arg.split('://')
                if len(parts) == 2:
                    credentials_and_rest = parts[1].split('@')
                    if len(credentials_and_rest) > 1:
                        # 提取用户名,隐藏密码
                        credentials = credentials_and_rest[0]
                        if ':' in credentials:
                            username = credentials.split(':')[0]
                            safe_cmd.append(f'{parts[0]}://{username}:********@{credentials_and_rest[1]}')
                        else:
                            safe_cmd.append(arg)
                    else:
                        safe_cmd.append(arg)
                else:
                    safe_cmd.append(arg)
            else:
                safe_cmd.append(arg)

        log.info(f'execute_command_safely | 执行命令: {" ".join(safe_cmd)}')
    # 执行命令,不使用shell=True以提高安全性
    # 注意:调用方应确保cmd_args已经过安全验证
    return subprocess.run(cmd_args, capture_output=True, text=True, check=False)  # noqa: S603


# ============ 函数重载签名定义 ============
@overload
def get_or_create_table_model(
    source_table_name: str,
    db_conn: ConnectionManager | None = None,
    new_table_name: None = None,
    table_args: None = None,
    **conn_kwargs: Any,
) -> type[BaseModel]:
    """仅反射现有表模型(new_table_name 为 None)"""
    ...


@overload
def get_or_create_table_model(
    source_table_name: str,
    db_conn: ConnectionManager | None = None,
    *,
    new_table_name: str,
    table_args: dict[str, Any] | None = None,
    **conn_kwargs: Any,
) -> type[BaseModel]:
    """复制表结构创建新表模型(new_table_name 为 str)"""
    ...


# ============ 实际实现 ============
def get_or_create_table_model(
    source_table_name: str,
    db_conn: ConnectionManager | None = None,
    new_table_name: str | None = None,
    table_args: dict[str, Any] | None = None,
    **conn_kwargs: Any,
) -> type[BaseModel]:
    """
    智能获取或创建表模型(支持两种模式)

    根据 new_table_name 参数自动选择工作模式:
    - 模式1(反射): new_table_name=None 时,仅反射现有表返回模型类
    - 模式2(复制): new_table_name=str 时,复制表结构创建新表并返回模型类

    Args:
        source_table_name: 源表名
        db_conn: 数据库连接对象,如果为None则创建新连接
        new_table_name: 新表名。为None时仅反射;提供字符串时复制创建新表
        table_args: 表参数字典,用于修改表结构(仅在复制模式下有效)
        **conn_kwargs: 如果没有提供db_conn,这些参数将传递给create_sqlconnection

    Returns:
        表对应的模型类

    Raises:
        ValueError: 当参数无效或表不存在时
        SQLAlchemyError: 当表操作过程中发生SQL错误时
        Exception: 当发生其他意外错误时

    Examples:
        >>> # 模式1: 仅反射现有表
        >>> UserModel = get_or_create_table_model('users', db_key='default')
        >>> print(UserModel.__tablename__)  # 'users'

        >>> # 模式2: 复制表结构创建新表
        >>> BackupModel = get_or_create_table_model('users', new_table_name='users_backup', db_key='default')
        >>> print(BackupModel.__tablename__)  # 'users_backup'

        >>> # 模式2: 复制并修改表结构
        >>> ModifiedModel = get_or_create_table_model('users', new_table_name='users_v2', table_args={'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}, db_key='default')
    """
    from xtsqlorm.factory import create_connection_manager

    # 确保有有效的数据库连接
    if db_conn is None:
        db_conn = create_connection_manager(**conn_kwargs)
    assert db_conn is not None, '数据库连接创建失败,请检查配置文件或连接参数'

    # ========== 模式1: 仅反射现有表 ==========
    if new_table_name is None:
        log.info(f'{get_or_create_table_model.__name__} | 模式1: 反射现有表 {source_table_name}')
        return reflect_table(source_table_name, db_conn)

    # ========== 模式2: 复制表结构创建新表 ==========
    log.info(f'{get_or_create_table_model.__name__} | 模式2: 复制表 {source_table_name} -> {new_table_name}')

    # 检查源表是否存在
    inspector = inspect(db_conn.engine)
    if not inspector.has_table(source_table_name):
        raise ValueError(f'数据库中不存在源表: {source_table_name}')

    # 创建新表前,先确保表不存在(避免索引冲突)
    from sqlalchemy import MetaData, text

    with db_conn.engine.begin() as conn:
        conn.execute(text(f'DROP TABLE IF EXISTS `{new_table_name}`'))

    # 清理元数据中的旧表信息(如果存在)
    if new_table_name in BaseModel.metadata.tables:
        BaseModel.metadata.remove(BaseModel.metadata.tables[new_table_name])
        log.info(f'get_or_create_table_model | 已清理元数据中的旧表: {new_table_name}')

    # 创建独立的元数据对象来加载源表(避免索引名冲突)
    temp_metadata = MetaData()
    source_table = Table(
        source_table_name,
        temp_metadata,
        autoload_with=db_conn.engine,
    )
    log.info(f'get_or_create_table_model | 已加载源表结构: {source_table_name}')

    # 复制表结构到BaseModel的元数据中
    # 注意: SQLAlchemy的to_metadata方法要求schema参数不能为None,如果源表没有schema则省略
    if source_table.schema is not None:
        new_table = source_table.to_metadata(
            BaseModel.metadata,
            name=new_table_name,
            schema=source_table.schema,
        )
    else:
        new_table = source_table.to_metadata(
            BaseModel.metadata,
            name=new_table_name,
        )

    # 应用额外的表参数(如果提供)
    if table_args:
        for key, value in table_args.items():
            setattr(new_table, key, value)
        log.info(f'get_or_create_table_model | 已应用表参数: {table_args}')

    # 创建新表
    try:
        new_table.create(bind=db_conn.engine, checkfirst=False)
        log.success(f'get_or_create_table_model | 成功创建新表: {new_table_name}')
    except Exception as e:
        log.error(f'get_or_create_table_model | 创建表失败: {e}')
        # 尝试再次清理并重试
        with db_conn.engine.begin() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS `{new_table_name}`'))
        raise

    # 创建模型类
    model_name = new_table_name.title().replace('_', '')
    table_model = type(
        model_name,
        (BaseModel,),
        {
            '__table__': new_table,
            '__tablename__': new_table_name,
        },
    )

    log.success(f'get_or_create_table_model | 成功创建模型类: {model_name} (表: {new_table_name})')
    return table_model


def reflect_table(
    source_table_name: str,
    db_conn: ConnectionManager | None = None,
    **conn_kwargs: Any,
) -> type[BaseModel]:
    """
    反射数据库中已存在的表并创建对应的模型类

    通过SQLAlchemy的反射机制,动态创建一个与数据库中现有表结构匹配的模型类。

    Args:
        source_table_name: 数据库中已存在的表名
        db_conn: 数据库连接对象,如果为None则创建新连接
        **conn_kwargs: 如果没有提供db_conn,这些参数将传递给create_sqlconnection

    Returns:
        与指定表结构匹配的模型类

    Raises:
        ValueError: 当表名不存在或连接无效时
        SQLAlchemyError: 当反射过程中发生SQL错误时
        Exception: 当发生其他意外错误时
    """
    # 延迟导入以避免循环依赖
    from xtsqlorm.factory import create_connection_manager

    # 确保有有效的数据库连接
    if db_conn is None:
        db_conn = create_connection_manager(**conn_kwargs)
    assert db_conn is not None, '数据库连接创建失败,请检查配置文件或连接参数'

    # 检查源表是否存在
    inspector = inspect(db_conn.engine)
    assert inspector.has_table(source_table_name), f'数据库中不存在源表: {source_table_name}'

    # 只反射指定的表以提高性能
    log.info(f'reflect_table | 正在反射数据库表: {source_table_name}')
    BaseModel.metadata.reflect(bind=db_conn.engine, only=[source_table_name])

    # 获取源表对象
    source_table = BaseModel.metadata.tables[source_table_name]

    # 创建模型类,继承自BaseModel
    model_name = source_table_name.title().replace('_', '')
    table_model = type(
        model_name,
        (BaseModel,),
        {
            '__table__': source_table,
            '__tablename__': source_table_name,
        },
    )
    log.success(f'reflect_table | 成功反射表: {source_table_name},创建模型类: {model_name}')

    return table_model


async def reflect_table_async(
    source_table_name: str,
    db_conn: Any | None = None,
    **conn_kwargs: Any,
) -> type[BaseModel]:
    """
    异步反射数据库中已存在的表并创建对应的模型类

    通过SQLAlchemy的异步反射机制,动态创建一个与数据库中现有表结构匹配的模型类。

    Args:
        source_table_name: 数据库中已存在的表名
        db_conn: 异步数据库连接对象(AsyncConnectionManager)
        **conn_kwargs: 如果没有提供db_conn,这些参数将传递给create_async_connection_manager

    Returns:
        与指定表结构匹配的模型类

    Raises:
        ValueError: 当表名不存在或连接无效时
        SQLAlchemyError: 当反射过程中发生SQL错误时
        Exception: 当发生其他意外错误时

    Example:
        >>> # 使用默认配置
        >>> user_model = await reflect_table_async('users', db_key='default')
        >>> print(user_model.__tablename__)
        >>> # 使用自定义连接
        >>> async_conn_mgr = create_async_connection_manager(db_key='default')
        >>> order_model = await reflect_table_async('orders', db_conn=async_conn_mgr)
        >>> await async_conn_mgr.dispose()  # 手动清理资源
    """
    from xtsqlorm.factory import create_async_connection_manager

    # 确保有有效的异步数据库连接
    should_dispose = False
    if db_conn is None:
        db_conn = create_async_connection_manager(**conn_kwargs)
        should_dispose = True  # 标记需要自动清理
    assert db_conn is not None, '异步数据库连接创建失败,请检查配置文件或连接参数'

    try:
        # 注意: 在异步环境中不能直接使用同步的 inspector.has_table()
        # 直接进行反射,如果表不存在会自动抛出异常
        log.info(f'reflect_table_async | 正在异步反射数据库表: {source_table_name}')

        # 使用异步引擎的 run_sync 方法进行反射
        async with db_conn.engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: BaseModel.metadata.reflect(sync_conn, only=[source_table_name]))

        # 获取源表对象
        source_table = BaseModel.metadata.tables[source_table_name]

        # 创建模型类,继承自BaseModel
        model_name = source_table_name.title().replace('_', '')
        table_model = type(
            model_name,
            (BaseModel,),
            {
                '__table__': source_table,
                '__tablename__': source_table_name,
            },
        )

        log.success(f'reflect_table_async | 成功异步反射表: {source_table_name},创建模型类: {model_name}')
        return table_model

    finally:
        # 如果是函数内部创建的连接,需要自动清理
        if should_dispose:
            await db_conn.dispose()


def generate_model_file(
    tablename: str,
    db_key: str = 'default',
    url: str | None = None,
    output_file: str | None = None,
    echo: bool = False,
    **kwargs: Any,
) -> int:
    """
    使用sqlacodegen将数据库表转换为SQLAlchemy模型类文件

    调用外部sqlacodegen工具,根据数据库连接信息和表名生成对应的SQLAlchemy模型类
    代码文件,支持自定义输出路径和额外的sqlacodegen参数。

    Args:
        tablename: 要转换的数据库表名
        db_key: 数据库配置键,用于从配置文件中获取连接信息,默认为'default'
        url: 数据库连接URL,如果提供此参数,将优先使用此URL而非从配置文件获取
        output_file: 输出文件路径,默认为None(使用tablename_db.py)
        echo: 是否打印详细执行信息,默认为False
        **kwargs: 传递给sqlacodegen的额外参数,格式为key=value

    Returns:
        命令执行结果的返回码,0表示成功

    Raises:
        ValueError: 当表名无效或无法获取数据库连接URL时
        FileNotFoundError: 当sqlacodegen工具未安装时
        Exception: 当执行过程中发生其他错误时
    """
    try:
        # 输入验证
        validate_sql_identifier(tablename, '表名')

        # 获取数据库连接URL
        if not url:
            url = connect_str(db_key)

        # 确定输出文件路径
        if output_file is None:
            output_file = f'{tablename}_dbmodel.py'

        # 构建命令参数列表
        cmd_args = build_safe_command_args(url, tablename, output_file, **kwargs)
        log.info(f'generate_model_file | 构建命令参数列表: {cmd_args}')
        # 执行命令
        result = execute_command_safely(cmd_args, mask_credentials=True, echo=echo)

        # 记录命令输出和结果
        if result.stdout and echo:
            log.info(f'enerate_model_file | 命令输出: {result.stdout.strip()}')

        if result.stderr:
            log.warning(f'enerate_model_file | 命令错误输出: {result.stderr.strip()}')

        if result.returncode == 0:
            log.success(f'enerate_model_file | 成功生成模型文件: {output_file}')
        else:
            log.error(f'enerate_model_file | 生成模型文件失败,返回码: {result.returncode}')

        return result.returncode

    except FileNotFoundError as e:
        raise FileNotFoundError('sqlacodegen工具未安装,请使用 pip install sqlacodegen 进行安装') from e

    except Exception as err:
        raise Exception(f'生成模型文件时发生错误: {err!s}') from err


__all__ = [
    'generate_model_file',
    'get_or_create_table_model',
    'reflect_table',
    'reflect_table_async',
]
