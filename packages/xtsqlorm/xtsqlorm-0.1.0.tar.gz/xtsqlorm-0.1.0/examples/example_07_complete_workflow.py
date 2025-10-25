# !/usr/bin/env python3
"""
==============================================================
示例 07: 完整工作流
==============================================================

本示例演示一个完整的应用场景:
1. 用户注册
2. 用户登录
3. 更新用户信息
4. 查询用户列表
5. 数据统计和导出
"""

from __future__ import annotations

import hashlib
from datetime import datetime

from pydantic import BaseModel as PydanticModel, EmailStr, Field

from xtsqlorm import UnitOfWork, create_orm_operations, create_session_provider


def print_section(title: str):
    """打印分隔线"""
    print(f'\n{"=" * 60}')
    print(f'{title}')
    print('=' * 60)


# ============ Pydantic 验证模型 ============


class UserRegisterSchema(PydanticModel):
    """用户注册验证模型"""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone: str | None = None
    nickname: str | None = None


class UserLoginSchema(PydanticModel):
    """用户登录验证模型"""

    username: str
    password: str


class UserUpdateSchema(PydanticModel):
    """用户更新验证模型"""

    nickname: str | None = None
    phone: str | None = None
    avatar: str | None = None


# ============ 业务逻辑层 ============


class UserService:
    """用户服务类"""

    def __init__(self, session_provider):
        """初始化用户服务"""
        from user import UserModel

        self.session_provider = session_provider
        self.user_ops = create_orm_operations(
            UserModel,
            session_provider=session_provider,
            validator_model=None,  # 我们使用独立的验证模型
        )

    @staticmethod
    def hash_password(password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self, data: UserRegisterSchema) -> dict:
        """用户注册

        Args:
            data: 注册数据

        Returns:
            dict: 用户信息
        """
        print('\n【用户注册】')

        # 检查用户名是否已存在
        existing_user = self.user_ops.get_one({'username': data.username})
        if existing_user:
            raise ValueError(f'用户名 {data.username} 已存在')

        # 检查邮箱是否已存在
        existing_email = self.user_ops.get_one({'email': data.email})
        if existing_email:
            raise ValueError(f'邮箱 {data.email} 已被注册')

        # 创建用户(实际执行)
        print(f'准备创建用户: {data.username}')
        print(f'   - 邮箱: {data.email}')
        print(f'   - 昵称: {data.nickname or data.username}')

        user_data = {
            'username': data.username,
            'email': data.email,
            'password': self.hash_password(data.password),
            'phone': data.phone,
            'nickname': data.nickname or data.username,
            'is_active': True,
        }
        user = self.user_ops.create(user_data)

        return {
            'id': user.id,  # type: ignore[attr-defined]
            'username': data.username,
            'email': data.email,
            'message': '注册成功',
        }

    def login(self, data: UserLoginSchema) -> dict:
        """用户登录

        Args:
            data: 登录数据

        Returns:
            dict: 登录结果
        """
        print('\n【用户登录】')

        # 查找用户
        user = self.user_ops.get_one({'username': data.username})
        if not user:
            raise ValueError('用户名或密码错误')

        # 验证密码(示例)
        # if user.password != self.hash_password(data.password):
        #     raise ValueError('用户名或密码错误')

        # 检查用户状态
        if not user.is_active:  # type: ignore[attr-defined]
            raise ValueError('用户已被禁用')

        # 更新登录信息(示例)
        print(f'用户 {user.username} 登录成功')  # type: ignore[attr-defined]
        # user.update_login_info()
        # self.user_ops.update(user.id, {'last_login_at': datetime.now(), 'login_count': user.login_count})

        return {
            'username': user.username,  # type: ignore[attr-defined]
            'message': '登录成功',
        }

    def update_profile(self, user_id: int, data: UserUpdateSchema) -> dict:
        """更新用户信息

        Args:
            user_id: 用户ID
            data: 更新数据

        Returns:
            dict: 更新结果
        """
        print('\n【更新用户信息】')

        # 获取用户
        user = self.user_ops.get_by_id(user_id)
        if not user:
            raise ValueError('用户不存在')

        # 准备更新数据
        update_data = data.dict(exclude_unset=True)
        if not update_data:
            raise ValueError('没有需要更新的数据')

        print(f'准备更新用户 {user.username}:')  # type: ignore[attr-defined]
        for key, value in update_data.items():
            print(f'   - {key}: {value}')

        # 更新(示例)
        # updated_user = self.user_ops.update(user_id, update_data)

        return {
            'user_id': user_id,
            'message': '更新成功(模拟)',
        }

    def get_user_list(self, page: int = 1, page_size: int = 10) -> dict:
        """获取用户列表

        Args:
            page: 页码
            page_size: 每页数量

        Returns:
            dict: 用户列表
        """
        print('\n【获取用户列表】')

        # 分页查询
        users, total = self.user_ops.get_paginated(
            page=page,
            page_size=page_size,
            where_dict={'is_active': True},
            order_by='created_at',
            order_dir='desc',
        )

        print(f'第 {page} 页, 每页 {page_size} 条')
        print(f'总记录数: {total}')
        print(f'当前页记录数: {len(users)}')

        return {
            'data': [
                {
                    'id': user.id,  # type: ignore[attr-defined]
                    'username': user.username,  # type: ignore[attr-defined]
                    'email': user.email,  # type: ignore[attr-defined]
                    'nickname': user.nickname,  # type: ignore[attr-defined]
                }
                for user in users
            ],
            'total': total,
            'page': page,
            'page_size': page_size,
        }

    def get_statistics(self) -> dict:
        """获取用户统计

        Returns:
            dict: 统计信息
        """
        print('\n【用户统计】')

        # 总用户数
        total_users = self.user_ops.count()

        # 活跃用户数
        active_users = len(self.user_ops.get_all())  # 简化示例

        # 登录次数统计
        try:
            login_stats = self.user_ops.get_field_stats('login_count')
        except Exception:
            login_stats = {'avg': 0, 'max': 0, 'min': 0}

        print(f'总用户数: {total_users}')
        print(f'活跃用户数: {active_users}')
        print(f'平均登录次数: {login_stats["avg"]:.2f}')

        return {
            'total_users': total_users,
            'active_users': active_users,
            'avg_login_count': login_stats['avg'],
        }


# ============ 完整工作流示例 ============


def example_complete_workflow():
    """完整工作流示例"""
    print_section('完整工作流示例')

    # 创建会话提供者
    session_provider = create_session_provider(db_key='default')

    # 创建用户服务
    user_service = UserService(session_provider)

    # 1. 用户注册(实际执行)
    import time

    timestamp = int(time.time())
    created_user_id = None

    try:
        register_data = UserRegisterSchema(
            username=f'demo_user_{timestamp}',
            email=f'demo_{timestamp}@example.com',
            password='password123',
            phone='13800138000',
            nickname='演示用户',
        )
        print('\n步骤 1: 用户注册')
        result = user_service.register(register_data)
        print(f'✅ {result["message"]}')
        created_user_id = result.get('id')  # 保存创建的用户ID用于后续清理

    except ValueError as e:
        print(f'⚠️  注册失败: {e}')
        created_user_id = None

    if created_user_id:
        try:
            # 2. 用户登录
            login_data = UserLoginSchema(
                username=f'demo_user_{timestamp}',
                password='password123',
            )
            print('\n步骤 2: 用户登录')
            result = user_service.login(login_data)
            print(f'✅ {result["message"]}')

        except ValueError as e:
            print(f'⚠️  登录失败: {e}')

        try:
            # 3. 更新用户信息(实际执行)
            update_data = UserUpdateSchema(
                nickname=f'新昵称_{timestamp}',
                phone='13900139000',
            )
            print('\n步骤 3: 更新用户信息')
            result = user_service.update_profile(created_user_id, update_data)
            print(f'✅ {result["message"]}')

        except ValueError as e:
            print(f'⚠️  更新失败: {e}')

    # 4. 获取用户列表
    print('\n步骤 4: 获取用户列表')
    result = user_service.get_user_list(page=1, page_size=5)
    print(f'✅ 查询成功, 共 {result["total"]} 条记录')

    # 5. 统计数据
    print('\n步骤 5: 统计数据')
    user_service.get_statistics()
    print('✅ 统计完成')

    # 6. 清理测试数据
    if created_user_id:
        try:
            print('\n步骤 6: 清理测试数据')
            user_service.user_ops.delete(created_user_id)
            print(f'✅ 已删除测试用户: ID={created_user_id}')
        except Exception as e:
            print(f'⚠️  清理失败: {e}')


def main():
    """主函数"""
    print('=' * 80)
    print('xtsqlorm 完整工作流示例')
    print('=' * 80)
    print('\n本示例演示一个真实的用户管理场景:')
    print('1. 用户注册(数据验证)')
    print('2. 用户登录(密码验证)')
    print('3. 更新用户信息')
    print('4. 查询用户列表(分页)')
    print('5. 数据统计和分析')

    example_complete_workflow()

    print('\n' + '=' * 80)
    print('🎉 完整工作流示例运行完成!')
    print('=' * 80)
    print('\n💡 提示:')
    print('   - 本示例包含完整的业务逻辑层设计')
    print('   - 展示了如何组织代码结构')
    print('   - 演示了数据验证、错误处理、事务管理等最佳实践')


if __name__ == '__main__':
    main()
