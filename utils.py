# -*- coding: utf-8 -*-
# @Time    : 2021/8/20 14:40
# @Author  : ShaoJK
# @File    : utils.py
# @Remark  :


class Dict(dict):
    """用属性的形式使用字典"""
    def __init__(self, seq=None, default=None, **kwargs):
        super(Dict, self).__init__(seq=None, **kwargs)
        self.default = default

    def __getattr__(self, key):
        if key not in self.keys():
            return self.default
        return self.get(key)

    def __setattr__(self, key, value):
        self[key] = value

