import typing
# 定义一个类型变量，表示类的类型
T = typing.TypeVar('T')


def singleton(cls: typing.Type[T]) -> typing.Callable[..., T]:
    """
    单例模式装饰器。

    :param cls: 要装饰的类
    :return: 返回一个函数，该函数返回类的单例实例
    """
    instances: dict[typing.Type[T], T] = {}

    def get_instance(*args: typing. Any, **kwargs: typing.Any) -> T:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance
