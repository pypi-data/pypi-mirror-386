# -*- coding: UTF-8 -*-

import threading


def singleton(cls):
    if not hasattr(cls, '_instance_lock'):
        cls._instance_lock = threading.Lock()

    _old_new = getattr(cls, '__new__')

    def _new_(c, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            with cls._instance_lock:
                if not hasattr(c, '_instance'):
                    cls._instance = _old_new(cls, *args, **kwargs)
        return cls._instance

    setattr(cls, '__new__', _new_)

    return cls
