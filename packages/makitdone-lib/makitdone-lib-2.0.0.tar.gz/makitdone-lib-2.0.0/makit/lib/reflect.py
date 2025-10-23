# -*- coding: UTF-8 -*-

import inspect
import re


def obj_name(obj):
    """
    获取函数名称
    :param obj:
    :return:
    """
    if inspect.isfunction(obj):
        name = re.search(r'<function (\S+) at', str(obj)).groups()[0]
    elif inspect.ismethod(obj):
        name = re.search(r'<bound method (\S+) of', str(obj)).groups()[0]
    elif inspect.ismodule(obj):
        name = obj.__name__
    elif inspect.isclass(obj):
        name = obj.__name__
    else:
        name = obj.__class__.__name__
    return name


def get_class(routine, module=None):
    if inspect.isclass(routine):
        return routine
    module = module or inspect.getmodule(routine)
    name = obj_name(routine)
    class_name = name[:name.rindex('.')] if '.' in name else None
    if class_name:  # 如果是类方法
        # reload(module)
        cls = getattr(module, class_name, None)
        return cls
    return None
