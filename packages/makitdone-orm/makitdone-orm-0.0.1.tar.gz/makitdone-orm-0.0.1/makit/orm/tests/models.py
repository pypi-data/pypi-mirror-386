# coding:utf-8

from makit.orm.fields import BigInt, String, Boolean, ForeignKey, UUID, Many
from makit.orm.model import DbModel

connstr = 'mysql://root:root@127.0.0.1:3306/demo?debug=true'


class User(DbModel):
    """ 用户 """
    id = BigInt(pk=True)
    name = String(20, comment='姓名')
    username = String(20, comment='用户名')
    password = String(500, json=False, comment='密码')
    is_superuser = Boolean(default=False)
    org = ForeignKey('Org', null=True, comment='组织ID')

    roles = Many('UserRole.role')


class Org(DbModel):
    """组织"""
    id = BigInt(pk=True)
    name = String(20)

    parent = ForeignKey('Org', null=True, related_name='children', comment='父级ID')


class DailyReport(DbModel):
    id = UUID(pk=True)
    summary = String(100)
    user = ForeignKey('User')


class Role(DbModel):
    id = BigInt(pk=True)
    name = String(20)


class UserRole(DbModel):
    id = BigInt(pk=True)
    role = ForeignKey('Role')
    user = ForeignKey('User')


print(User.get_meta().fields)
