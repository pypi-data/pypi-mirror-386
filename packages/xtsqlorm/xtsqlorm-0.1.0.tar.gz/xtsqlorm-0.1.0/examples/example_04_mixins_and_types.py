# !/usr/bin/env python3
"""
==============================================================
示例 04: Mixin 和自定义类型使用
==============================================================

本示例演示:
1. 各种 Mixin 的使用
2. 自定义类型的使用
3. 组合多个 Mixin
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, Enum, Integer, String

from xtsqlorm import Base, BaseModel, EnumType, IdMixin, JsonEncodedDict, SoftDeleteMixin, TimestampMixin, UTCDateTime, UTCTimeMixin, VersionedMixin, create_repository


def print_section(title: str):
    """打印分隔线"""
    print(f'\n{"=" * 60}')
    print(f'{title}')
    print('=' * 60)


# ============ 定义演示类(不使用SQLAlchemy,仅演示Mixin功能)============

# 注意：这些类仅用于演示 Mixin 的方法功能,不涉及数据库操作


class DemoArticle:
    """演示文章类 - 手动模拟 Mixin 功能"""

    def __init__(self, title: str, content: str):
        self.title = title
        self.content = content
        self.id = None
        self.version = 0
        self.deleted_at = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self):
        self.deleted_at = datetime.now()

    def restore(self):
        self.deleted_at = None

    def increment_version(self):
        self.version += 1


class DemoConfig:
    """演示配置类 - 手动模拟类型功能"""

    def __init__(self, key: str, value: str | None = None, **kwargs):
        self.key = key
        self.value = value
        self.metadata_json = kwargs.get('metadata_json')
        self.expires_at = kwargs.get('expires_at')
        self.category = kwargs.get('category')


# ============ 示例函数 ============


def example_1_id_mixin():
    """示例 1: IdMixin - 自增主键"""
    print_section('示例 1: IdMixin - 自增主键')

    print('IdMixin 提供:')
    print('   - id: Integer, 主键, 自增')
    print('')
    print('使用示例:')
    print('   class MyModel(BaseModel, IdMixin):')
    print('       __tablename__ = "my_table"')
    print('       name = Column(String(100))')


def example_2_timestamp_mixin():
    """示例 2: TimestampMixin - 时间戳"""
    print_section('示例 2: TimestampMixin - 时间戳')

    print('TimestampMixin 提供:')
    print('   - created_at: 创建时间(自动设置)')
    print('   - updated_at: 更新时间(自动更新)')
    print('')
    print('DemoArticle 模拟了 TimestampMixin:')
    print(f'   - 有 created_at 字段: {hasattr(DemoArticle, "created_at")}')
    print(f'   - 有 updated_at 字段: {hasattr(DemoArticle, "updated_at")}')


def example_3_soft_delete_mixin():
    """示例 3: SoftDeleteMixin - 软删除"""
    print_section('示例 3: SoftDeleteMixin - 软删除')

    print('SoftDeleteMixin 提供:')
    print('   - deleted_at: 删除时间(NULL 表示未删除)')
    print('   - soft_delete(): 软删除方法')
    print('   - restore(): 恢复方法')
    print('   - is_deleted 属性: 是否已删除')
    print('')
    print('【实际演示】')

    # 创建测试对象
    article = DemoArticle(title='Test Article', content='Test Content')
    print(f'✅ 创建文章: {article.title}')
    print(f'   - is_deleted: {article.is_deleted}')
    print(f'   - deleted_at: {article.deleted_at}')

    # 软删除
    article.soft_delete()
    print('\n执行 soft_delete() 后:')
    print(f'   - is_deleted: {article.is_deleted}')
    print(f'   - deleted_at: {article.deleted_at}')

    # 恢复
    article.restore()
    print('\n执行 restore() 后:')
    print(f'   - is_deleted: {article.is_deleted}')
    print(f'   - deleted_at: {article.deleted_at}')


def example_4_versioned_mixin():
    """示例 4: VersionedMixin - 版本控制"""
    print_section('示例 4: VersionedMixin - 版本控制')

    print('VersionedMixin 提供:')
    print('   - version: 版本号(每次更新自增)')
    print('   - increment_version(): 增加版本号')
    print('')
    print('用于乐观锁实现,防止并发更新冲突')
    print('')
    print('【实际演示】')

    # 创建测试对象
    article = DemoArticle(title='Versioned Article', content='Content')
    print(f'✅ 创建文章: {article.title}')
    print(f'   - 初始版本号: {article.version}')

    # 增加版本号
    article.increment_version()
    print('\n执行 increment_version() 后:')
    print(f'   - 版本号: {article.version}')

    article.increment_version()
    print('\n再次执行 increment_version() 后:')
    print(f'   - 版本号: {article.version}')


def example_5_utc_time_mixin():
    """示例 5: UTCTimeMixin - UTC 时间"""
    print_section('示例 5: UTCTimeMixin - UTC 时间')

    print('UTCTimeMixin 提供:')
    print('   - created_at_utc: UTC 创建时间')
    print('   - updated_at_utc: UTC 更新时间')
    print('')
    print('说明:')
    print('   在实际使用中,继承 UTCTimeMixin 的模型会自动拥有这些字段')
    print('   时间会自动转换为 UTC 存储')


def example_6_json_encoded_dict():
    """示例 6: JsonEncodedDict - JSON 存储"""
    print_section('示例 6: JsonEncodedDict - JSON 存储')

    print('JsonEncodedDict 类型:')
    print('   - 自动将 Python dict 序列化为 JSON 字符串存储')
    print('   - 读取时自动反序列化为 Python dict')
    print('')
    print('【实际演示】')

    # 创建包含 JSON 数据的配置
    config = DemoConfig(
        key='app_settings',
        value='test_value',
        metadata_json={'theme': 'dark', 'language': 'zh-CN', 'features': ['f1', 'f2']},
    )
    print(f'✅ 创建配置: {config.key}')
    print(f'   - metadata_json 类型: {type(config.metadata_json)}')
    print(f'   - metadata_json 内容: {config.metadata_json}')

    # 访问 JSON 数据
    if config.metadata_json:
        print('\n访问 JSON 字段:')
        print(f'   - theme: {config.metadata_json.get("theme")}')
        print(f'   - language: {config.metadata_json.get("language")}')
        print(f'   - features: {config.metadata_json.get("features")}')


def example_7_utc_datetime():
    """示例 7: UTCDateTime - UTC 时间类型"""
    print_section('示例 7: UTCDateTime - UTC 时间类型')

    print('UTCDateTime 类型:')
    print('   - 自动处理时区转换')
    print('   - 存储为 UTC 时间')
    print('   - 读取时转换为本地时区(可选)')
    print('')
    print('【实际演示】')

    # 创建包含 UTC 时间的配置
    now = datetime.now()
    config = DemoConfig(key='token', value='test_token', expires_at=now)

    print(f'✅ 创建配置: {config.key}')
    print(f'   - 本地时间: {now}')
    print(f'   - expires_at: {config.expires_at}')
    print(f'   - expires_at 类型: {type(config.expires_at)}')


def example_8_enum_type():
    """示例 8: EnumType - 枚举类型"""
    print_section('示例 8: EnumType - 枚举类型')

    print('EnumType 类型:')
    print('   - 限制字段值为预定义的选项')
    print('   - 提供类型安全')
    print('')
    print('ConfigModel 的 category 字段:')
    print('   - 允许的值: ["system", "user", "app"]')
    print('')
    print('【实际演示】')

    # 创建有效的枚举值
    config1 = DemoConfig(key='sys_config', value='test', category='system')
    print(f'✅ 创建配置1: category={config1.category} (有效值)')

    config2 = DemoConfig(key='user_config', value='test', category='user')
    print(f'✅ 创建配置2: category={config2.category} (有效值)')

    config3 = DemoConfig(key='app_config', value='test', category='app')
    print(f'✅ 创建配置3: category={config3.category} (有效值)')

    print('\n说明: 如果使用无效值(如 "invalid"),在数据库插入时会报错')


def example_9_combined_usage():
    """示例 9: 组合使用"""
    print_section('示例 9: 组合使用多个 Mixin')

    print('DemoArticle 演示了多个 Mixin 的组合:')
    print('   1. BaseModel - 基础模型')
    print('   2. IdMixin - 主键 id')
    print('   3. TimestampMixin - created_at, updated_at')
    print('   4. SoftDeleteMixin - deleted_at, soft_delete()')
    print('   5. VersionedMixin - version')
    print('')
    print('【实际演示完整功能】')

    # 创建文章
    article = DemoArticle(title='Complete Example', content='Full feature demo')

    print(f'\n✅ 创建文章: {article.title}')
    print('   业务字段:')
    print(f'      - title: {article.title}')
    print(f'      - content: {article.content}')
    print('   Mixin 字段:')
    print(f'      - id: {article.id} (IdMixin)')
    print(f'      - version: {article.version} (VersionedMixin)')
    print(f'      - is_deleted: {article.is_deleted} (SoftDeleteMixin)')
    print(f'      - created_at: {article.created_at} (TimestampMixin)')
    print(f'      - updated_at: {article.updated_at} (TimestampMixin)')

    # 演示版本控制
    print('\n【版本控制】')
    article.increment_version()
    print(f'   增加版本后: version={article.version}')

    # 演示软删除
    print('\n【软删除】')
    article.soft_delete()
    print(f'   软删除后: is_deleted={article.is_deleted}, deleted_at={article.deleted_at}')

    # 演示恢复
    article.restore()
    print(f'   恢复后: is_deleted={article.is_deleted}, deleted_at={article.deleted_at}')

    print('\n💡 所有 Mixin 功能都可以无缝组合使用!')


def main():
    """主函数"""
    print('=' * 80)
    print('xtsqlorm Mixin 和自定义类型示例')
    print('=' * 80)

    example_1_id_mixin()
    example_2_timestamp_mixin()
    example_3_soft_delete_mixin()
    example_4_versioned_mixin()
    example_5_utc_time_mixin()
    example_6_json_encoded_dict()
    example_7_utc_datetime()
    example_8_enum_type()
    example_9_combined_usage()

    print('\n' + '=' * 80)
    print('🎉 所有示例运行完成!')
    print('=' * 80)


if __name__ == '__main__':
    main()
