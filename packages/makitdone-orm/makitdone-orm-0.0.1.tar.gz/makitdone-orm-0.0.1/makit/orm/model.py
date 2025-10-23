# coding:utf-8

from makit.orm.base import SqlBase, ModelMetaClass, MetaInfo, BaseField


class DbModel(SqlBase, metaclass=ModelMetaClass):
    """"""
    __db__ = 'default'
    __abstract__ = True
    __tablename__ = None
    __order_by__ = []  # 默认排序
    __cache__ = False  # 如果为True，相应的数据会进行缓存管理，比如一些数据量比较少，基本没什么变更的

    def __init__(self, **kwargs):
        meta = getattr(self, '_meta')
        fields = meta.fields
        for field in fields:
            v = kwargs.pop(field.name, field.default_value())
            v = field.to_py_value(v)
            setattr(self, field.name, v)

    def __json__(self):
        """
        用于序列化
        """
        meta = getattr(self.__class__, '_meta')
        info = dict()
        for field in meta.fields:
            v = getattr(self, field.name)
            info[field.name] = v
        return info

    @classmethod
    def get_primary_keys(cls):
        meta: MetaInfo = getattr(cls, '_meta')
        return meta.primary_keys

    @classmethod
    def get_field(cls, name: str) -> BaseField:
        meta: MetaInfo = getattr(cls, '_meta')
        return meta.field_map.get(name)

    @classmethod
    def get_meta(cls) -> MetaInfo:
        return getattr(cls, '_meta')
