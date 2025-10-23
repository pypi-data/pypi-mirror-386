# -*- coding: UTF-8 -*-

import asyncio
import inspect
import io
import re
import sys
import traceback
from functools import cached_property

from makit.lib import reflect, py


class Null:
    """"""


class Argument:
    def __init__(self, name, default=Null, arg_type=None, kwonly=False):
        self.name = name
        self.default = default
        if not arg_type and self.optional:
            arg_type = type(default)
        self.type = arg_type
        self.kwonly = kwonly

    @property
    def optional(self):
        return self.default is not Null

    def __repr__(self):
        if self.optional:
            return f'<Argument {self.name}={self.default}>'
        return f'<Argument {self.name}>'


class Func:
    def __init__(self, func):
        self.func = func
        self._name = None
        self.args = []
        self.allow_args = False
        self.allow_kwargs = False
        self.description = None
        self._cls = None
        self.module = inspect.getmodule(func)
        self._arg_parsed = False

    @property
    def name(self):
        if not self._name:
            self._name = reflect.obj_name(self.func)  # f'{self.cls.__name__}.{self.func.__name__}'
        return self._name

    @cached_property
    def cls(self):
        if not self._cls:
            self._cls = reflect.get_class(self.func, module=self.module)
        return self._cls

    @cached_property
    def is_classmethod(self):
        if self.cls:
            o = object.__new__(self.cls)
            f = getattr(o, self.func.__name__)
            f_str = str(f)
            return re.match(r'<bound method [a-zA-Z_0-9]+\.[a-zA-Z0-9_]+ of <class', f_str) is not None
        return False

    @cached_property
    def is_module_function(self):
        return re.match(r'<function [a-zA-Z_][a-zA-Z0-9_]* at', str(self.func)) is not None

    @cached_property
    def is_staticmethod(self):
        if self.cls:
            o = object.__new__(self.cls)
            f = getattr(o, self.func.__name__)
            f_str = str(f)
            return re.match(r'<function [a-zA-Z_0-9]+\.[a-zA-Z_][a-zA-Z0-9_]* at', f_str) is not None
        return False

    @cached_property
    def is_instance_method(self):
        if self.cls:
            o = object.__new__(self.cls)
            f = getattr(o, self.func.__name__)
            f_str = str(f)
            return re.match(r'<bound method .+ of <.+ object at 0x[A-Z0-9]+>>', f_str) is not None
        return False

    def parse_args(self):
        if self._arg_parsed:
            return
        self._arg_parsed = True
        full_args = inspect.getfullargspec(self.func)
        self.allow_args = full_args.varargs is not None
        self.allow_kwargs = full_args.varkw is not None
        if full_args.defaults:
            kwargs = zip(reversed(full_args.args), reversed(full_args.defaults))
            required_args = full_args.args[:len(full_args.args) - len(full_args.defaults)]
        else:
            required_args, kwargs = full_args.args, {}
        for name in required_args:
            self.args.append(Argument(name, arg_type=full_args.annotations.get(name)))
        for name, value in kwargs:
            self.args.append(Argument(name, default=value, arg_type=full_args.annotations.get(name)))
        for name in full_args.kwonlyargs:
            default = full_args.kwonlydefaults.get(name)
            arg_type = full_args.annotations.get(name)
            self.args.append(Argument(name, default=default, arg_type=arg_type, kwonly=True))
        return self

    def __call__(self, *args, **kwargs):
        args = [*args]
        if self.func.__name__ == '__init__':
            instance = object.__new__(self.cls)
            args.insert(0, instance)
        actual_args, actual_kwargs = [], {}
        _args = self.args[1:] if inspect.ismethod(self.func) else self.args  # 如果是实例方法，需要忽略第一个参数
        for a in _args:
            if a.name in kwargs:
                value = kwargs.pop(a.name)
            else:
                if a.optional:
                    value = a.default
                else:
                    if args:
                        value = args.pop(0)
                    else:
                        raise TypeError(f"{self.name}() missing 1 required positional argument: '{a.name}'")
            if a.kwonly:
                actual_kwargs[a.name] = value
            else:
                actual_args.append(value)
        if self.allow_args:
            actual_args.extend(args)
        if self.allow_kwargs:
            actual_kwargs.update(kwargs)
        return self.func(*actual_args, **actual_kwargs)


def run(_func, *args, **kwargs):
    """
    调用函数，可正确处理参数，不会因为参数给多或者顺序错乱而导致错误
    :param _func:
    :param args:
    :param kwargs:
    :return:
    """
    return Func(_func).parse_args()(*args, **kwargs)


async def async_run(_func, *args, **kwargs):
    if asyncio.iscoroutinefunction(_func):
        return await Func(_func).parse_args()(*args, **kwargs)
    else:
        return Func(_func).parse_args()(*args, **kwargs)


class CallInfo:
    def __init__(self, frame):
        self.__frame = frame
        self._filename = None
        self._lineno = None
        self._caller = None

    @property
    def filename(self):
        return self.__frame.f_code.co_filename

    @property
    def lineno(self):
        return self.__frame.f_lineno

    @property
    def func_name(self):
        return self.__frame.f_code.co_name

    @property
    def caller(self):
        frame_str = str(self.__frame)
        caller_name = re.findall(r'code (.+)>', frame_str)[0]
        f_locals = self.__frame.f_locals
        if 'self' in f_locals:
            instance = f_locals.get('self')
            return getattr(instance, caller_name)
        elif 'cls' in f_locals:
            cls = f_locals.get('cls')
            return getattr(cls, caller_name)

    @property
    def module(self):
        return py.import_file(self.filename, raise_error=False)

    def get_stack(self):
        sio = io.StringIO()
        sio.write('Stack (most recent call last):\n')
        traceback.print_stack(self.__frame, file=sio)
        stack_info = sio.getvalue()
        if stack_info[-1] == '\n':
            stack_info = stack_info[:-1]
        sio.close()
        return stack_info

    def flat(self):
        return self.filename, self.module, self.func_name, self.lineno, self.get_stack()


def parse_caller(invoked_file):
    """
    用于解析函数调用者信息
    :param invoked_file: 被调用函数所在的py文件路径
    :return:
    """
    f = getattr(sys, '_getframe')(0)
    found, changed = None, False
    while f:
        code_file = f.f_code.co_filename
        if code_file == invoked_file and found is None:
            found = True
        if found and code_file != invoked_file:
            changed = True
        if found and changed:
            break
        f = f.f_back
    if not f:
        return
    return CallInfo(f)
