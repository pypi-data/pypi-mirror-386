# -*- coding: UTF-8 -*-


class Error(Exception):
    """"""

    def __init__(self, *args, **kwargs):
        self.data = kwargs
        super().__init__(*args)


class NotSupportError(Error):
    """ """
