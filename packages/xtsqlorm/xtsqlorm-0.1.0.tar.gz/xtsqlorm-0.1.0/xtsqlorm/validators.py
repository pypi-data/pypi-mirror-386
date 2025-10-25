#!/usr/bin/env python3
"""
==============================================================
Description  : 数据验证工具模块
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-24 23:58:00
Github       : https://github.com/sandorn/xtsqlorm

本模块提供各种数据验证工具函数,用于验证数据库字段的合法性,
包括邮箱、手机号、日期时间、JSON、枚举值、URL、IP地址等常见数据类型的验证。

主要功能:
- 基础验证: required, length, range, type
- 格式验证: email, phone, url, ip, pattern
- 数据验证: datetime, json, dict, enum
- 高级验证: password_strength, username, id_card, choices
==============================================================
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from datetime import datetime
from enum import Enum
from typing import Any
from urllib.parse import urlparse


class ValidationError(Exception):
    """验证错误异常类

    当数据验证失败时抛出,包含详细的错误信息和验证失败的字段信息。
    """

    def __init__(self, message: str, field: str | None = None, value: Any = None) -> None:
        """初始化验证错误

        Args:
            message: 错误消息
            field: 验证失败的字段名(可选)
            value: 验证失败的值(可选)
        """
        self.message = message
        self.field = field
        self.value = value
        super().__init__(message)

    def __str__(self) -> str:
        """格式化错误信息"""
        if self.field:
            return f"字段 '{self.field}' 验证失败: {self.message} (值: {self.value})"
        return f'验证失败: {self.message}'


def validate_dict(value: Any, field: str | None = None) -> Any:
    """验证JsonEncodedDict类型

    Args:
        value: 要验证的值
        field: 字段名(用于错误消息)

    Returns:
        Any: 验证通过的值

    Raises:
        ValidationError: 如果值不是JsonEncodedDict类型
    """
    if value is not None and not isinstance(value, dict):
        raise ValidationError('值不是字典类型', field, value)
    return value


def validate_email(email: str, field: str | None = None) -> str:
    """验证邮箱地址格式

    Args:
        email: 要验证的邮箱地址
        field: 字段名(用于错误消息)

    Returns:
        str: 验证通过的邮箱地址

    Raises:
        ValidationError: 如果邮箱格式无效
    """
    if not email:
        raise ValidationError('邮箱地址不能为空', field, email)

    # 简单的邮箱格式验证
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError('邮箱格式无效', field, email)

    return email


def validate_phone(phone: str, field: str | None = None) -> str:
    """验证手机号格式(支持中国大陆手机号)

    Args:
        phone: 要验证的手机号
        field: 字段名(用于错误消息)

    Returns:
        str: 验证通过的手机号

    Raises:
        ValidationError: 如果手机号格式无效
    """
    if not phone:
        raise ValidationError('手机号不能为空', field, phone)

    # 中国大陆手机号验证(1开头,11位数字)
    pattern = r'^1[3-9]\d{9}$'
    if not re.match(pattern, phone):
        raise ValidationError('手机号格式无效', field, phone)

    return phone


def validate_datetime(dt_str: str, field: str | None = None) -> datetime:
    """验证日期时间字符串并转换为datetime对象

    Args:
        dt_str: 日期时间字符串
        field: 字段名(用于错误消息)

    Returns:
        datetime: 解析后的datetime对象

    Raises:
        ValidationError: 如果日期时间格式无效
    """
    if not dt_str:
        raise ValidationError('日期时间不能为空', field, dt_str)

    try:
        # 尝试解析ISO格式日期时间
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except (ValueError, TypeError) as e:
        raise ValidationError('日期时间格式无效', field, dt_str) from e


def validate_json(json_str: str, field: str | None = None) -> dict | list:
    """验证JSON字符串并解析为Python对象

    Args:
        json_str: JSON字符串
        field: 字段名(用于错误消息)

    Returns:
        dict | list: 解析后的Python对象

    Raises:
        ValidationError: 如果JSON格式无效
    """
    if not json_str:
        raise ValidationError('JSON字符串不能为空', field, json_str)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValidationError('JSON格式无效', field, json_str) from e


def validate_enum(value: Any, enum_class: type[Enum], field: str | None = None) -> Enum:
    """验证值是否为有效的枚举值

    Args:
        value: 要验证的值
        enum_class: 枚举类
        field: 字段名(用于错误消息)

    Returns:
        Enum: 验证通过的枚举值

    Raises:
        ValidationError: 如果值不是有效的枚举值
    """
    if value is None:
        raise ValidationError('枚举值不能为空', field, value)

    try:
        if isinstance(value, str):
            return enum_class(value)
        if isinstance(value, int):
            # 尝试通过值查找枚举
            for enum_member in enum_class:
                if enum_member.value == value:
                    return enum_member
            raise ValueError
        return enum_class(value)
    except (ValueError, TypeError) as e:
        valid_values = [e.value for e in enum_class]
        raise ValidationError(f'无效的枚举值,有效值为: {valid_values}', field, value) from e


def validate_required(value: Any, field: str | None = None) -> Any:
    """验证值是否为非空

    Args:
        value: 要验证的值
        field: 字段名(用于错误消息)

    Returns:
        Any: 验证通过的值

    Raises:
        ValidationError: 如果值为空
    """
    if value is None or value == '':
        raise ValidationError('该字段为必填项', field, value)
    return value


def validate_length(value: str, min_len: int | None = None, max_len: int | None = None, field: str | None = None) -> str:
    """验证字符串长度

    Args:
        value: 要验证的字符串
        min_len: 最小长度(可选)
        max_len: 最大长度(可选)
        field: 字段名(用于错误消息)

    Returns:
        str: 验证通过的字符串

    Raises:
        ValidationError: 如果长度不符合要求
    """
    if value is None:
        raise ValidationError('字符串不能为空', field, value)

    length = len(value)

    if min_len is not None and length < min_len:
        raise ValidationError(f'长度不能小于 {min_len} 个字符', field, value)

    if max_len is not None and length > max_len:
        raise ValidationError(f'长度不能超过 {max_len} 个字符', field, value)

    return value


def validate_range(value: int | float, min_val: int | float | None = None, max_val: int | float | None = None, field: str | None = None) -> int | float:
    """验证数值范围

    Args:
        value: 要验证的数值
        min_val: 最小值(可选)
        max_val: 最大值(可选)
        field: 字段名(用于错误消息)

    Returns:
        int | float: 验证通过的数值

    Raises:
        ValidationError: 如果数值不在指定范围内

    Example:
        >>> validate_range(25, min_val=0, max_val=150, field='age')
        25
        >>> validate_range(200, min_val=0, max_val=150, field='age')
        ValidationError: 字段 'age' 验证失败: 值不能超过 150 (值: 200)
    """
    if value is None:
        raise ValidationError('数值不能为空', field, value)

    if min_val is not None and value < min_val:
        raise ValidationError(f'值不能小于 {min_val}', field, value)

    if max_val is not None and value > max_val:
        raise ValidationError(f'值不能超过 {max_val}', field, value)

    return value


def validate_url(url: str, field: str | None = None, *, require_https: bool = False) -> str:
    """验证URL格式

    Args:
        url: 要验证的URL
        field: 字段名(用于错误消息)
        require_https: 是否要求HTTPS协议

    Returns:
        str: 验证通过的URL

    Raises:
        ValidationError: 如果URL格式无效

    Example:
        >>> validate_url('https://example.com')
        'https://example.com'
        >>> validate_url('http://example.com', require_https=True)
        ValidationError: URL必须使用HTTPS协议
    """
    if not url:
        raise ValidationError('URL不能为空', field, url)

    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValueError
        if require_https and result.scheme != 'https':
            raise ValidationError('URL必须使用HTTPS协议', field, url)
    except Exception as e:
        raise ValidationError('URL格式无效', field, url) from e

    return url


def validate_ip(ip: str, field: str | None = None, *, version: int | None = None) -> str:
    """验证IP地址格式

    Args:
        ip: 要验证的IP地址
        field: 字段名(用于错误消息)
        version: IP版本(4或6,None表示都接受)

    Returns:
        str: 验证通过的IP地址

    Raises:
        ValidationError: 如果IP格式无效

    Example:
        >>> validate_ip('192.168.1.1')
        '192.168.1.1'
        >>> validate_ip('2001:0db8:85a3::8a2e:0370:7334')
        '2001:0db8:85a3::8a2e:0370:7334'
    """
    if not ip:
        raise ValidationError('IP地址不能为空', field, ip)

    # IPv4 验证
    ipv4_pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    # IPv6 验证(简化版)
    ipv6_pattern = r'^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:))$'

    is_ipv4 = bool(re.match(ipv4_pattern, ip))
    is_ipv6 = bool(re.match(ipv6_pattern, ip))

    if version == 4 and not is_ipv4:
        raise ValidationError('不是有效的IPv4地址', field, ip)

    if version == 6 and not is_ipv6:
        raise ValidationError('不是有效的IPv6地址', field, ip)

    if version is None and not (is_ipv4 or is_ipv6):
        raise ValidationError('IP地址格式无效', field, ip)

    return ip


def validate_pattern(value: str, pattern: str, field: str | None = None, *, error_message: str | None = None) -> str:
    """使用自定义正则表达式验证字符串

    Args:
        value: 要验证的字符串
        pattern: 正则表达式模式
        field: 字段名(用于错误消息)
        error_message: 自定义错误消息

    Returns:
        str: 验证通过的字符串

    Raises:
        ValidationError: 如果字符串不匹配模式

    Example:
        >>> validate_pattern('ABC123', r'^[A-Z]{3}\\d{3}$', 'code')
        'ABC123'
        >>> validate_pattern('abc123', r'^[A-Z]{3}\\d{3}$', 'code')
        ValidationError: 字段 'code' 验证失败: 格式不匹配指定模式
    """
    if not value:
        raise ValidationError('值不能为空', field, value)

    if not re.match(pattern, value):
        msg = error_message or '格式不匹配指定模式'
        raise ValidationError(msg, field, value)

    return value


def validate_in_choices(value: Any, choices: Sequence[Any], field: str | None = None) -> Any:
    """验证值是否在指定选项中

    Args:
        value: 要验证的值
        choices: 有效选项列表
        field: 字段名(用于错误消息)

    Returns:
        Any: 验证通过的值

    Raises:
        ValidationError: 如果值不在选项中

    Example:
        >>> validate_in_choices('red', ['red', 'green', 'blue'], 'color')
        'red'
        >>> validate_in_choices('yellow', ['red', 'green', 'blue'], 'color')
        ValidationError: 字段 'color' 验证失败: 值必须是以下选项之一: ['red', 'green', 'blue']
    """
    if value not in choices:
        raise ValidationError(f'值必须是以下选项之一: {list(choices)}', field, value)
    return value


def validate_type(value: Any, expected_type: type | tuple[type, ...], field: str | None = None) -> Any:
    """验证值的类型

    Args:
        value: 要验证的值
        expected_type: 期望的类型或类型元组
        field: 字段名(用于错误消息)

    Returns:
        Any: 验证通过的值

    Raises:
        ValidationError: 如果类型不匹配

    Example:
        >>> validate_type(123, int, 'age')
        123
        >>> validate_type('123', int, 'age')
        ValidationError: 字段 'age' 验证失败: 期望类型为 int, 实际类型为 str
    """
    if not isinstance(value, expected_type):
        if isinstance(expected_type, tuple):
            type_names = ' 或 '.join(t.__name__ for t in expected_type)
            msg = f'期望类型为 {type_names}, 实际类型为 {type(value).__name__}'
        else:
            msg = f'期望类型为 {expected_type.__name__}, 实际类型为 {type(value).__name__}'
        raise ValidationError(msg, field, value)
    return value


def validate_password_strength(
    password: str,
    field: str | None = None,
    *,
    min_length: int = 8,
    require_digit: bool = True,
    require_upper: bool = True,
    require_lower: bool = True,
    require_special: bool = False,
) -> str:
    """验证密码强度

    Args:
        password: 要验证的密码
        field: 字段名(用于错误消息)
        min_length: 最小长度
        require_digit: 是否要求包含数字
        require_upper: 是否要求包含大写字母
        require_lower: 是否要求包含小写字母
        require_special: 是否要求包含特殊字符

    Returns:
        str: 验证通过的密码

    Raises:
        ValidationError: 如果密码强度不足

    Example:
        >>> validate_password_strength('StrongPass123')
        'StrongPass123'
        >>> validate_password_strength('weak')
        ValidationError: 密码长度至少为8个字符
    """
    if not password:
        raise ValidationError('密码不能为空', field, password)

    errors = []

    if len(password) < min_length:
        errors.append(f'密码长度至少为{min_length}个字符')

    if require_digit and not any(c.isdigit() for c in password):
        errors.append('密码必须包含至少一个数字')

    if require_upper and not any(c.isupper() for c in password):
        errors.append('密码必须包含至少一个大写字母')

    if require_lower and not any(c.islower() for c in password):
        errors.append('密码必须包含至少一个小写字母')

    if require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append('密码必须包含至少一个特殊字符')

    if errors:
        raise ValidationError('; '.join(errors), field, password)

    return password


def validate_username(
    username: str,
    field: str | None = None,
    *,
    min_length: int = 3,
    max_length: int = 32,
    allow_special: bool = False,
) -> str:
    """验证用户名格式

    Args:
        username: 要验证的用户名
        field: 字段名(用于错误消息)
        min_length: 最小长度
        max_length: 最大长度
        allow_special: 是否允许特殊字符(._-)

    Returns:
        str: 验证通过的用户名

    Raises:
        ValidationError: 如果用户名格式无效

    Example:
        >>> validate_username('user_123')
        'user_123'
        >>> validate_username('u')
        ValidationError: 用户名长度必须在3到32个字符之间
    """
    if not username:
        raise ValidationError('用户名不能为空', field, username)

    if not (min_length <= len(username) <= max_length):
        raise ValidationError(f'用户名长度必须在{min_length}到{max_length}个字符之间', field, username)

    if allow_special:
        pattern = r'^[a-zA-Z0-9._-]+$'
        error_msg = '用户名只能包含字母、数字和特殊字符(._-)'
    else:
        pattern = r'^[a-zA-Z0-9]+$'
        error_msg = '用户名只能包含字母和数字'

    if not re.match(pattern, username):
        raise ValidationError(error_msg, field, username)

    return username


def validate_chinese_id_card(id_card: str, field: str | None = None) -> str:
    """验证中国身份证号码格式(18位)

    Args:
        id_card: 要验证的身份证号码
        field: 字段名(用于错误消息)

    Returns:
        str: 验证通过的身份证号码

    Raises:
        ValidationError: 如果身份证号码格式无效

    Example:
        >>> validate_chinese_id_card('110101199001011234')
        '110101199001011234'
    """
    if not id_card:
        raise ValidationError('身份证号码不能为空', field, id_card)

    # 18位身份证号码格式验证
    pattern = r'^\d{17}[\dXx]$'
    if not re.match(pattern, id_card):
        raise ValidationError('身份证号码格式无效(应为18位)', field, id_card)

    # 校验码验证
    factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_codes = '10X98765432'

    try:
        sum_value = sum(int(id_card[i]) * factors[i] for i in range(17))
        check_code = check_codes[sum_value % 11]

        if id_card[17].upper() != check_code:
            raise ValidationError('身份证号码校验码无效', field, id_card)
    except (ValueError, IndexError) as e:
        raise ValidationError('身份证号码格式无效', field, id_card) from e

    return id_card


# 导出所有验证函数
__all__ = [
    'ValidationError',
    'validate_chinese_id_card',
    'validate_datetime',
    'validate_dict',
    'validate_email',
    'validate_enum',
    'validate_in_choices',
    'validate_ip',
    'validate_json',
    'validate_length',
    'validate_password_strength',
    'validate_pattern',
    'validate_phone',
    'validate_range',
    'validate_required',
    'validate_type',
    'validate_url',
    'validate_username',
]
