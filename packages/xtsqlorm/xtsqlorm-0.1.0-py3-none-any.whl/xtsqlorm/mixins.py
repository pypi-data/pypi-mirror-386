#!/usr/bin/env python3
"""
==============================================================
Description  : SQLAlchemy ORM混入类定义
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-23 16:00:00
Github       : https://github.com/sandorn/xtsqlorm

本模块提供各种ORM混入类,包括:
- IdMixin: ID字段混入
- TimestampMixin: 时间戳字段混入
- SoftDeleteMixin: 软删除功能混入
- VersionedMixin: 版本控制混入
- UTCTimeMixin: UTC时间工具混入
==============================================================
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import DateTime, Integer, delete, select, text
from sqlalchemy.orm import Mapped, mapped_column

# ============ 异常定义 ============


class MixinError(Exception):
    """Mixin操作相关的异常.

    当ItemMixin的字典风格操作失败时抛出此异常。

    Example:
        >>> class MyModel(ItemMixin):
        ...     pass
        >>> obj = MyModel()
        >>> try:
        ...     value = obj['nonexistent_key']
        ... except MixinError as e:
        ...     print(f'Error: {e}')
    """

    pass


# ============ 字段类型混入类 ============


class UTCTimeMixin:
    """UTC时间工具混入类

    提供时区感知的时间处理工具方法,确保所有时间操作都基于UTC时区,避免时区问题。
    主要用于数据库模型中统一时间处理逻辑,确保跨时区应用的数据一致性。
    """

    @staticmethod
    def utc_now() -> datetime:
        """获取当前UTC时间"""
        return datetime.now(UTC)

    @staticmethod
    def utc_today() -> datetime:
        """获取UTC当天的开始时间"""
        now = datetime.now(UTC)
        return datetime(now.year, now.month, now.day, tzinfo=UTC)

    @staticmethod
    def days_ago(days: int) -> datetime:
        """获取days天前的UTC时间"""
        return datetime.now(UTC) - timedelta(days=days)

    @staticmethod
    def hours_ago(hours: int) -> datetime:
        """获取hours小时前的UTC时间"""
        return datetime.now(UTC) - timedelta(hours=hours)


class IdMixin:
    """ID字段混入类

    提供数据库表的主键ID字段定义,简化主键字段的重复定义。
    通过混入方式使用,可以与其他混入类组合,构建完整的数据模型。
    """

    id: Mapped[int] = mapped_column(Integer, primary_key=True)


class TimestampMixin:
    """时间戳字段混入类

    提供创建时间和更新时间字段定义,确保所有时间戳都使用UTC时区。
    通过数据库默认值和自动更新机制,维护记录的时间信息,无需手动设置。
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text('UTC_TIMESTAMP()'),  # MySQL兼容的UTC时间戳
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text('UTC_TIMESTAMP()'),
        onupdate=text('UTC_TIMESTAMP()'),  # MySQL兼容的UTC时间戳
    )


class SoftDeleteMixin:
    """软删除混入类 - 时区感知版本

    提供逻辑删除功能,通过标记删除时间而非物理删除记录,实现数据的可恢复性。
    包含软删除、恢复、查询活跃/已删除记录等完整功能,并支持永久清理过期删除记录。
    """

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment='软删除时间戳(UTC时区)')

    def soft_delete(self) -> None:
        """执行软删除操作,使用UTC时间标记删除

        将记录标记为已删除状态,但不从数据库中物理删除,便于数据恢复和历史查询。
        自动使用当前UTC时间作为删除时间戳。
        """
        self.deleted_at = datetime.now(UTC)

    def restore(self) -> None:
        """恢复已软删除的记录

        清除删除时间戳,将记录恢复为活跃状态,适用于误删除等场景。
        """
        self.deleted_at = None

    @property
    def is_deleted(self) -> bool:
        """检查记录是否已被软删除

        Returns:
            bool: 如果记录已被软删除则返回True,否则返回False
        """
        return self.deleted_at is not None

    @property
    def deletion_age_days(self) -> float | None:
        """获取记录被删除的天数(如未删除则返回None)

        Returns:
            float | None: 记录被删除的天数,未删除时返回None
        """
        if not self.deleted_at:
            return None
        return (datetime.now(UTC) - self.deleted_at).total_seconds() / 86400

    # 类方法查询
    @classmethod
    def get_active(cls, session: Any) -> Any:
        """获取所有活跃(未删除)的记录

        Args:
            session: SQLAlchemy会话对象

        Returns:
            sqlalchemy.ScalarResult: 活跃记录的结果集
        """
        return session.scalars(select(cls).where(cls.deleted_at.is_(None)))

    @classmethod
    def get_deleted(cls, session: Any) -> Any:
        """获取所有已软删除的记录

        Args:
            session: SQLAlchemy会话对象

        Returns:
            sqlalchemy.ScalarResult: 已删除记录的结果集
        """
        return session.scalars(select(cls).where(cls.deleted_at.is_not(None)))

    @classmethod
    def get_all_including_deleted(cls, session: Any) -> Any:
        """获取所有记录(包括活跃和已删除的记录)

        Args:
            session: SQLAlchemy会话对象

        Returns:
            sqlalchemy.ScalarResult: 所有记录的结果集
        """
        return session.scalars(select(cls))

    @classmethod
    def permanent_delete_old_records(cls, session: Any, days: int = 30) -> int:
        """永久删除超过指定天数的软删除记录

        用于清理历史软删除数据,释放数据库空间。默认清理30天前的删除记录。

        Args:
            session: SQLAlchemy会话对象
            days: 保留天数,超过该天数的软删除记录将被永久删除,默认为30天

        Returns:
            int: 永久删除的记录数量
        """

        cutoff_date = datetime.now(UTC) - timedelta(days=days)

        result = session.execute(delete(cls).where(cls.deleted_at.is_not(None), cls.deleted_at < cutoff_date))
        session.commit()
        return result.rowcount


class VersionedMixin:
    """版本控制混入类

    提供乐观锁功能,防止并发更新冲突。通过版本号机制,确保在多用户环境下数据的一致性。
    当多个用户同时修改同一条记录时,只有第一个提交的修改会成功,后续修改将失败。

    注意: 使用字段名 version 而非 version_id 以保持简洁性和一致性。
    """

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='版本号用于乐观锁')

    def increment_version(self) -> None:
        """手动增加版本号

        在更新记录前调用此方法,确保版本号正确递增,维持乐观锁的有效性。
        """
        self.version += 1


__all__ = ['IdMixin', 'SoftDeleteMixin', 'TimestampMixin', 'UTCTimeMixin', 'VersionedMixin']
