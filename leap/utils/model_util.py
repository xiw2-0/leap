from typing import Type, TypeVar, Any
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


def pydantic_model_from_object(data: object, model_type: Type[T]) -> T:
    """
    将一个对象转换为 Pydantic 模型类型。

    :param data: 要转换的对象
    :param model_type: 目标 Pydantic 模型类型
    :return: 转换后的 Pydantic 模型实例
    """
    assert data is not None, "Data cannot be None"

    # 检查数据对象的类名是否与模型类名一致
    assert data.__class__.__name__ == model_type.__name__, \
        f"Data class name '{data.__class__.__name__}' does not match model class name '{model_type.__name__}'"

    # 检查数据对象的模块是否在指定的模块中
    assert data.__class__.__module__ in (
        'xtquant.xttype', 'xtquant.xtpythonclient'), \
        f"Data class module '{data.__class__.__module__}' is not in the allowed modules"

    # 从 Pydantic 模型的字段注解中提取字段名
    fields = model_type.model_fields
    values = {field: getattr(data, field, None) for field in fields}

    # 使用 Pydantic 模型的构造函数创建实例
    return model_type.model_validate(values)


def pydantic_model_from_dict(dict_data: dict[str, Any], model_type: Type[T]) -> T:
    """
    将字典数据转换为 Pydantic 模型类型。
    """
    assert dict_data is not None, "Data cannot be None"

    fields = model_type.model_fields
    values = {field: dict_data.get(field, None) for field in fields}

    return model_type.model_validate(values)
