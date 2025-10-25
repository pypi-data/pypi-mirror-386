# !/usr/bin/env python3
"""
==============================================================
示例 05: 数据验证
==============================================================

本示例演示:
1. 使用 Pydantic 进行数据验证
2. 使用内置基础验证器 (required, length, range, email, phone, datetime)
3. 使用格式验证器 (url, ip, pattern, username, password_strength)
4. 使用高级验证器 (type, choices, chinese_id_card)
5. OrmOperations 的验证功能
6. 实际应用场景示例
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel as PydanticModel, Field, field_validator

from xtsqlorm import (
    ValidationError,
    create_orm_operations,
    validate_chinese_id_card,
    validate_datetime,
    validate_email,
    validate_in_choices,
    validate_ip,
    validate_length,
    validate_password_strength,
    validate_pattern,
    validate_phone,
    validate_range,
    validate_required,
    validate_type,
    validate_url,
    validate_username,
)


def print_section(title: str):
    """打印分隔线"""
    print(f'\n{"=" * 60}')
    print(f'{title}')
    print('=' * 60)


# ============ 定义 Pydantic 验证模型 ============


class UserValidator(PydanticModel):
    """用户数据验证模型"""

    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)
    phone: str | None = None
    age: int | None = Field(None, ge=0, le=150)

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        """验证邮箱格式"""
        import re

        if not v:
            raise ValueError('邮箱不能为空')
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('邮箱格式无效')
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone_number(cls, v):
        """验证手机号"""
        if v and not v.isdigit():
            raise ValueError('手机号必须是数字')
        if v and len(v) != 11:
            raise ValueError('手机号必须是11位')
        return v

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """验证密码强度"""
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        if not any(c.isalpha() for c in v):
            raise ValueError('密码必须包含至少一个字母')
        return v


# ============ 示例函数 ============


def example_1_pydantic_validation():
    """示例 1: 使用 Pydantic 验证"""
    print_section('示例 1: 使用 Pydantic 验证')

    print('有效数据:')
    try:
        valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'pass123',
            'phone': '13800138000',
            'age': 25,
        }
        user = UserValidator(**valid_data)
        print(f'✅ 验证通过: {user.model_dump()}')
    except Exception as e:
        print(f'❌ 验证失败: {e}')

    print('\n无效数据 - 用户名太短:')
    try:
        invalid_data = {
            'username': 'ab',  # 太短
            'email': 'test@example.com',
            'password': 'pass123',
        }
        user = UserValidator(**invalid_data)
    except Exception as e:
        print(f'❌ 验证失败: {e}')

    print('\n无效数据 - 邮箱格式错误:')
    try:
        invalid_data = {
            'username': 'testuser',
            'email': 'invalid-email',  # 格式错误
            'password': 'pass123',
        }
        user = UserValidator(**invalid_data)
    except Exception as e:
        print(f'❌ 验证失败: {e}')


def example_2_orm_with_validation():
    """示例 2: OrmOperations 集成 Pydantic 验证"""
    print_section('示例 2: OrmOperations 集成验证')

    from user import UserModel

    # 创建带验证的 ORM 操作对象
    ops = create_orm_operations(
        UserModel,
        db_key='default',
        validator_model=UserValidator,  # 指定验证模型
    )

    print('使用验证模型创建 ORM 操作对象')
    print('创建/更新操作时会自动验证数据\n')

    # 测试有效数据
    print('【测试有效数据】')
    try:
        import time

        timestamp = int(time.time())

        valid_user = ops.create({
            'username': f'valid_user_{timestamp}',
            'email': f'valid_{timestamp}@example.com',
            'password': 'pass123456',
        })
        print(f'✅ 验证通过, 创建成功: ID={valid_user.id}')  # type: ignore[attr-defined]

        # 清理测试数据
        ops.delete(valid_user.id)  # type: ignore[attr-defined]
        print('   已清理测试数据')
    except Exception as e:
        print(f'⚠️  操作失败: {e}')

    # 测试无效数据
    print('\n【测试无效数据】')
    try:
        ops.create({
            'username': 'ab',  # 太短
            'email': 'invalid',  # 格式错误
            'password': '123',  # 太短
        })
        print('❌ 意外: 验证应该失败但却成功了')
    except ValueError as e:
        print(f'✅ 验证失败(符合预期): {e}')
    except Exception as e:
        print(f'⚠️  其他错误: {e}')


def example_3_built_in_validators():
    """示例 3: 使用内置验证器"""
    print_section('示例 3: 使用内置验证器')

    # validate_required
    print('validate_required - 必填验证:')
    try:
        validate_required('test', '用户名')
        print('   ✅ 通过')
    except ValidationError as e:
        print(f'   ❌ 失败: {e}')

    try:
        validate_required('', '用户名')
    except ValidationError as e:
        print(f'   ❌ 空值失败: {e}')

    # validate_length
    print('\nvalidate_length - 长度验证:')
    try:
        validate_length('testuser', min_len=3, max_len=50, field='用户名')
        print('   ✅ 长度合法')
    except ValidationError as e:
        print(f'   ❌ 失败: {e}')

    try:
        validate_length('ab', min_len=3, max_len=50, field='用户名')
    except ValidationError as e:
        print(f'   ❌ 太短: {e}')

    # validate_email
    print('\nvalidate_email - 邮箱验证:')
    try:
        validate_email('test@example.com')
        print('   ✅ 邮箱格式正确')
    except ValidationError as e:
        print(f'   ❌ 失败: {e}')

    try:
        validate_email('invalid-email')
    except ValidationError as e:
        print(f'   ❌ 格式错误: {e}')

    # validate_phone
    print('\nvalidate_phone - 手机号验证:')
    try:
        validate_phone('13800138000')
        print('   ✅ 手机号格式正确')
    except ValidationError as e:
        print(f'   ❌ 失败: {e}')

    try:
        validate_phone('12345')
    except ValidationError as e:
        print(f'   ❌ 格式错误: {e}')

    # validate_range
    print('\nvalidate_range - 范围验证:')
    try:
        validate_range(25, min_val=0, max_val=150, field='年龄')
        print('   ✅ 年龄在范围内')
    except ValidationError as e:
        print(f'   ❌ 失败: {e}')

    try:
        validate_range(200, min_val=0, max_val=150, field='年龄')
    except ValidationError as e:
        print(f'   ❌ 超出范围: {e}')

    # validate_datetime
    print('\nvalidate_datetime - 日期时间验证:')
    try:
        validate_datetime(datetime.now().isoformat(), field='创建时间')
        print('   ✅ 日期时间格式正确')
    except ValidationError as e:
        print(f'   ❌ 失败: {e}')

    try:
        validate_datetime('not-a-date', field='创建时间')
    except ValidationError as e:
        print(f'   ❌ 格式错误: {e}')


def example_4_custom_validation():
    """示例 4: 自定义验证逻辑"""
    print_section('示例 4: 自定义验证逻辑')

    def validate_user_data(data: dict) -> dict:
        """自定义用户数据验证"""
        errors = []

        # 用户名验证
        if 'username' not in data:
            errors.append('缺少用户名')
        elif len(data['username']) < 3:
            errors.append('用户名至少3个字符')

        # 邮箱验证
        if 'email' not in data:
            errors.append('缺少邮箱')
        elif '@' not in data['email']:
            errors.append('邮箱格式错误')

        # 密码验证
        if 'password' not in data:
            errors.append('缺少密码')
        elif len(data['password']) < 6:
            errors.append('密码至少6个字符')

        if errors:
            raise ValidationError('; '.join(errors))

        return data

    # 测试自定义验证
    print('测试自定义验证函数:\n')

    print('有效数据:')
    try:
        valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
        }
        result = validate_user_data(valid_data)
        print(f'✅ 验证通过: {result}\n')
    except ValidationError as e:
        print(f'❌ 验证失败: {e}\n')

    print('无效数据:')
    try:
        invalid_data = {
            'username': 'ab',  # 太短
            'email': 'invalid',  # 无@符号
            'password': '123',  # 太短
        }
        result = validate_user_data(invalid_data)
    except ValidationError as e:
        print(f'❌ 验证失败: {e}')


def example_5_format_validators():
    """示例 5: 格式验证器 (URL, IP, Pattern)"""
    print_section('示例 5: 格式验证器')

    # validate_url
    print('validate_url - URL验证:')
    try:
        result = validate_url('https://example.com')
        print(f'   ✅ 有效URL: {result}')
    except ValidationError as e:
        print(f'   ❌ 失败: {e}')

    try:
        validate_url('not-a-url', field='网站')
    except ValidationError as e:
        print(f'   ❌ 无效URL: {e.message}')

    # require_https
    try:
        validate_url('http://example.com', field='安全网站', require_https=True)
    except ValidationError as e:
        print(f'   ❌ 要求HTTPS: {e.message}')

    # validate_ip
    print('\nvalidate_ip - IP地址验证:')
    try:
        result = validate_ip('192.168.1.1')
        print(f'   ✅ 有效IPv4: {result}')
    except ValidationError as e:
        print(f'   ❌ 失败: {e}')

    try:
        validate_ip('256.256.256.256', field='服务器IP')
    except ValidationError as e:
        print(f'   ❌ 无效IPv4: {e.message}')

    # validate_pattern
    print('\nvalidate_pattern - 自定义模式验证:')
    try:
        result = validate_pattern('ABC123', r'^[A-Z]{3}\d{3}$', 'code')
        print(f'   ✅ 匹配模式: {result}')
    except ValidationError as e:
        print(f'   ❌ 失败: {e}')

    try:
        validate_pattern('abc123', r'^[A-Z]{3}\d{3}$', '产品编码', error_message='格式必须是3个大写字母+3个数字')
    except ValidationError as e:
        print(f'   ❌ 不匹配: {e.message}')


def example_6_advanced_validators():
    """示例 6: 高级验证器 (Type, Choices, Username, Password)"""
    print_section('示例 6: 高级验证器')

    # validate_type
    print('validate_type - 类型验证:')
    try:
        result = validate_type(123, int, 'age')
        print(f'   ✅ 正确类型(int): {result}')
    except ValidationError as e:
        print(f'   ❌ 失败: {e}')

    try:
        validate_type('123', int, 'age')
    except ValidationError as e:
        print(f'   ❌ 类型错误: {e.message}')

    # validate_in_choices
    print('\nvalidate_in_choices - 选项验证:')
    try:
        result = validate_in_choices('active', ['active', 'inactive', 'pending'], 'status')
        print(f'   ✅ 有效选项: {result}')
    except ValidationError as e:
        print(f'   ❌ 失败: {e}')

    try:
        validate_in_choices('deleted', ['active', 'inactive', 'pending'], 'status')
    except ValidationError as e:
        print(f'   ❌ 无效选项: {e.message}')

    # validate_username
    print('\nvalidate_username - 用户名验证:')
    try:
        result = validate_username('user123')
        print(f'   ✅ 有效用户名: {result}')
    except ValidationError as e:
        print(f'   ❌ 失败: {e}')

    try:
        validate_username('ab', field='username')
    except ValidationError as e:
        print(f'   ❌ 太短: {e.message}')

    try:
        result = validate_username('user_name-123', allow_special=True)
        print(f'   ✅ 允许特殊字符: {result}')
    except ValidationError as e:
        print(f'   ❌ 失败: {e}')

    # validate_password_strength
    print('\nvalidate_password_strength - 密码强度验证:')
    try:
        result = validate_password_strength('StrongPass123')
        print(f'   ✅ 强密码: {result}')
    except ValidationError as e:
        print(f'   ❌ 失败: {e}')

    try:
        validate_password_strength('weak', field='password')
    except ValidationError as e:
        print(f'   ❌ 弱密码: {e.message}')

    try:
        result = validate_password_strength('Secure@Pass123', require_special=True)
        print(f'   ✅ 包含特殊字符: {result}')
    except ValidationError as e:
        print(f'   ❌ 失败: {e}')


def example_7_chinese_id_card():
    """示例 7: 中国身份证号码验证"""
    print_section('示例 7: 中国身份证号码验证')

    print('validate_chinese_id_card - 身份证验证:')
    print('   ⚠️  注意: 以下示例仅用于演示格式验证')

    # 格式验证
    try:
        validate_chinese_id_card('123456', field='id_card')
    except ValidationError as e:
        print(f'   ❌ 格式错误(长度): {e.message}')

    try:
        validate_chinese_id_card('12345678901234567A', field='id_card')
    except ValidationError as e:
        print(f'   ❌ 格式错误(字符): {e.message}')

    print('   i️  完整测试需要真实有效的身份证号码')


def example_8_real_world_scenarios():
    """示例 8: 实际应用场景"""
    print_section('示例 8: 实际应用场景')

    # 场景1: 用户注册表单验证
    print('【场景1: 用户注册表单验证】')

    def validate_registration_form(data: dict) -> dict:
        """验证用户注册表单"""
        errors = []

        try:
            validate_required(data.get('username'), 'username')
            validate_username(data['username'], min_length=4, max_length=20)
        except ValidationError as e:
            errors.append(f'用户名: {e.message}')

        try:
            validate_required(data.get('email'), 'email')
            validate_email(data['email'])
        except ValidationError as e:
            errors.append(f'邮箱: {e.message}')

        try:
            validate_required(data.get('password'), 'password')
            validate_password_strength(data['password'], min_length=8, require_upper=True, require_digit=True)
        except ValidationError as e:
            errors.append(f'密码: {e.message}')

        if data.get('phone'):
            try:
                validate_phone(data['phone'])
            except ValidationError as e:
                errors.append(f'手机号: {e.message}')

        if errors:
            raise ValidationError('; '.join(errors))

        return data

    # 测试有效注册
    try:
        valid_registration = {
            'username': 'newuser123',
            'email': 'newuser@example.com',
            'password': 'SecurePass123',
            'phone': '13800138000',
        }
        result = validate_registration_form(valid_registration)
        print(f'✅ 注册表单验证通过: {result["username"]}')
    except ValidationError as e:
        print(f'❌ 验证失败: {e}')

    # 测试无效注册
    try:
        invalid_registration = {
            'username': 'ab',  # 太短
            'email': 'invalid',  # 格式错误
            'password': 'weak',  # 弱密码
        }
        validate_registration_form(invalid_registration)
    except ValidationError as e:
        print(f'❌ 注册失败(符合预期): {e.message}')

    # 场景2: API请求参数验证
    print('\n【场景2: API请求参数验证】')

    def validate_api_request(data: dict) -> dict:
        """验证API请求参数"""
        # 验证必需参数
        validate_required(data.get('action'), 'action')
        validate_in_choices(data['action'], ['create', 'update', 'delete'], 'action')

        # 验证可选参数
        if 'callback_url' in data:
            validate_url(data['callback_url'], require_https=True)

        if 'timeout' in data:
            validate_type(data['timeout'], (int, float), 'timeout')
            validate_range(data['timeout'], min_val=1, max_val=300, field='timeout')

        if 'ip_whitelist' in data:
            for ip in data['ip_whitelist']:
                validate_ip(ip, version=4)

        return data

    # 测试有效API请求
    try:
        valid_api_request = {
            'action': 'create',
            'callback_url': 'https://api.example.com/callback',
            'timeout': 30,
            'ip_whitelist': ['192.168.1.1', '10.0.0.1'],
        }
        result = validate_api_request(valid_api_request)
        print(f'✅ API请求验证通过: action={result["action"]}')
    except ValidationError as e:
        print(f'❌ 验证失败: {e}')

    # 测试无效API请求
    try:
        invalid_api_request = {
            'action': 'invalid_action',  # 无效动作
            'timeout': 500,  # 超出范围
        }
        validate_api_request(invalid_api_request)
    except ValidationError as e:
        print(f'❌ API请求失败(符合预期): {e.message}')

    # 场景3: 配置文件验证
    print('\n【场景3: 配置文件验证】')

    def validate_config(config: dict) -> dict:
        """验证配置文件"""
        # 数据库配置
        if 'database' in config:
            db_config = config['database']
            validate_required(db_config.get('host'), 'database.host')
            validate_range(db_config.get('port', 3306), min_val=1, max_val=65535, field='database.port')
            validate_type(db_config.get('timeout', 30), (int, float), 'database.timeout')

        # 日志配置
        if 'logging' in config:
            log_config = config['logging']
            validate_in_choices(log_config.get('level', 'INFO'), ['DEBUG', 'INFO', 'WARNING', 'ERROR'], 'logging.level')

        return config

    # 测试有效配置
    try:
        valid_config = {
            'database': {
                'host': 'localhost',
                'port': 3306,
                'timeout': 30,
            },
            'logging': {
                'level': 'INFO',
            },
        }
        result = validate_config(valid_config)
        print(f'✅ 配置验证通过: database.host={result["database"]["host"]}')
    except ValidationError as e:
        print(f'❌ 验证失败: {e}')


def main():
    """主函数"""
    print('=' * 80)
    print('xtsqlorm 数据验证示例 - 完整版')
    print('=' * 80)

    # 基础示例
    example_1_pydantic_validation()
    example_2_orm_with_validation()
    example_3_built_in_validators()
    example_4_custom_validation()

    # 新增验证器示例
    example_5_format_validators()
    example_6_advanced_validators()
    example_7_chinese_id_card()
    example_8_real_world_scenarios()

    print('\n' + '=' * 80)
    print('🎉 所有示例运行完成! 共8个示例')
    print('=' * 80)
    print('\n提示: 本示例展示了18个验证器函数的使用方法')
    print('包括: 基础验证、格式验证、高级验证和实际应用场景')


if __name__ == '__main__':
    main()
