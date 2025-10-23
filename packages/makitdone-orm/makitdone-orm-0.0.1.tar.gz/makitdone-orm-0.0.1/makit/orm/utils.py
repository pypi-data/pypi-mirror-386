# coding:utf-8

import typing as t

from makit.orm.base import BaseField, MetaInfo, ModelMetaClass


def model_fields(model: ModelMetaClass) -> t.List[BaseField]:
    meta: MetaInfo = getattr(model, '_meta')
    return meta.fields


def tablename(model: ModelMetaClass | str):
    """获取数据模型的表名"""
    if isinstance(model, ModelMetaClass):
        meta = getattr(model, '_meta')
        return meta.tablename
    else:
        return model


def bind_data_to_model(model, **kwargs):
    instance = object.__new__(model)
    fields = model_fields(model)
    for field in fields:
        value = kwargs.get(field.name)
        setattr(instance, field.name, value)
    return instance
