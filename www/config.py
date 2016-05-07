#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Configuration
'''

__author__ = 'Michael Liao'

import config_default#导入默认配置

class Dict(dict):#这个类应该算是很常见了，就是把dict类加工一下，使得新的Dict类创建的实例可以用x.y的方式来取值和赋值
    '''
    Simple dict but support access as x.y style.
    '''
    def __init__(self, names=(), values=(), **kw):#看不懂这个初始化方法
        super(Dict, self).__init__(**kw)#先调用父类的初始化方法存储键值对
        for k, v in zip(names, values):#然后自己再用for循环遍历存储键值对，why?
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

def merge(defaults, override):#融合默认配置和自定义配置
    r = {}
    for k, v in defaults.items():
        if k in override:
            if isinstance(v, dict):
                r[k] = merge(v, override[k])
            else:
                r[k] = override[k]
        else:
            r[k] = v
    return r

def toDict(d):#把d这个dict的键值对存入我们自定义的Dict中，然后返回一个新的Dict也就是D
    D = Dict()
    for k, v in d.items():#用for循环遍历d的键值对，然后把这些键值对存入新的Dict
        D[k] = toDict(v) if isinstance(v, dict) else v#假如值本身就是一个dict，那就把这个值交给toDict处理，然后再存入Dict
    return D#返回生成的新Dict

configs = config_default.configs

try:
    import config_override#导入自定义配置
    configs = merge(configs, config_override.configs)#融合默认配置和自定义配置
except ImportError:#导入自定义配置失败就直接pass
    pass

configs = toDict(configs)#将融合后的配置交给toDict函数处理
