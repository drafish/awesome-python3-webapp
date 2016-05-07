#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao'

import asyncio, os, inspect, logging, functools

from urllib import parse

from aiohttp import web

from apis import APIError
#这是个装饰器，在handlers模块中被引用，其作用是给http请求添加请求方法和请求路径这两个属性
def get(path):
    '''
    Define decorator @get('/path')
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'GET'	#请求方法
        wrapper.__route__ = path	#请求路径
        return wrapper
    return decorator
#解释同上，暂时没用到
def post(path):
    '''
    Define decorator @post('/path')
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper
    return decorator

#函数的参数fn本身就是个函数，下面五个函数是针对fn函数的参数做一些处理判断
def get_required_kw_args(fn):
    args = []#定义一个空的list，用来储存fn的参数名
    #想深究inspect的同学可以去查下官方文档，像我这样比较懒的知道这是个什么就好了，=后面那一串就是fn函数的所有参数，是一个dict
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        #参数类型为命名关键字参数且没有指定默认值
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
            args.append(name)#把命名关键字参数的参数名加入args这个list
    return tuple(args)#把list变成tuple，我不知道为什么要这么做
#和上一个函数基本一样，唯一的区别就是不需要满足没有默认值这个条件，也就是说这个函数把fn的所有命名关键字参数的参数名都提取出来
def get_named_kw_args(fn):
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)
#判断fn有没有命名关键字参数，有的话就返回True
def has_named_kw_args(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            return True
#判断fn有没有关键字参数，有的话就返回True，注意关键字参数和命名关键字参数是不一样的，不熟悉的同学可以温习下‘函数的参数’这一小节
def has_var_kw_arg(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True
#判断fn的参数中有没有参数名为request的参数
def has_request_arg(fn):
    sig = inspect.signature(fn)#这边之所以拆成两行，是因为后面raise语句要用到sig
    params = sig.parameters
    found = False#默认没有找到
    for name, param in params.items():
        if name == 'request':#找到参数名为request的参数后把found设置为True
            found = True
            continue#下面的代码不执行，直接进入下一个循环
        #下面这两行代码我怎么都想不通，基本能猜出来这两行代码在这儿的作用，但我想不通为什么要这么些
        #我在day5的评论区提出了我的疑问，但没人鸟我，大家可以去看看http://www.liaoxuefeng.com/discuss/001409195742008d822b26cf3de46aea14f2b7378a1ba91000/00146232548240136b7590e87fb4765b88197275b42a5fd000
        if found and (param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_KEYWORD):
            raise ValueError('request parameter must be the last named parameter in function: %s%s' % (fn.__name__, str(sig)))
    return found

class RequestHandler(object):
    #初始化自身的属性
    def __init__(self, app, fn):
        self._app = app
        self._func = fn
        self._has_request_arg = has_request_arg(fn)
        self._has_var_kw_arg = has_var_kw_arg(fn)
        self._has_named_kw_args = has_named_kw_args(fn)
        self._named_kw_args = get_named_kw_args(fn)
        self._required_kw_args = get_required_kw_args(fn)
    #定义了__call__方法后这个类就相当与一个函数了
    async def __call__(self, request):
        kw = None
        #感觉有self._has_named_kw_args就没必要再加self._required_kw_args，不知道为什么这么写
        if self._has_var_kw_arg or self._has_named_kw_args or self._required_kw_args:
            if request.method == 'POST':
                if not request.content_type:#content_type是request提交的消息主体类型，没有就返回丢失消息主体类型
                    return web.HTTPBadRequest('Missing Content-Type.')
                ct = request.content_type.lower()#lower函数的作用是把字符串转化为小写
                if ct.startswith('application/json'):#如果消息主体类型开头为application/json，则说明消息主体是个json对象
                    params = await request.json()#用json方法读取信息
                    if not isinstance(params, dict):#读取出来的信息如果不是dict就有问题
                        return web.HTTPBadRequest('JSON body must be object.')
                    kw = params#把读取出来的dict复制给kw
                elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
                    params = await request.post()#浏览器表单信息用post方法来读取
                    kw = dict(**params)#这儿params不是dict，需要通过dict方法转化成dict，那params到底是什么？
                else:#post的消息主体既不是json对象，又不是浏览器表单，那就只能返回不支持该消息主体类型
                    return web.HTTPBadRequest('Unsupported Content-Type: %s' % request.content_type)
            if request.method == 'GET':
                qs = request.query_string#获取请求字符串
                if qs:
                    kw = dict()#定义一个空的dict
                    for k, v in parse.parse_qs(qs, True).items():#解析字符串后用for循环迭代
                        kw[k] = v[0]#把解析出来的结果存入kw
        if kw is None:#经过以上步骤，如果kw为空，那就。。。。。。我也不知道这是怎么处理的
            kw = dict(**request.match_info)
        else:
            if not self._has_var_kw_arg and self._named_kw_args:#没有关键字参数但有命名关键字参数
                copy = dict()
                for name in self._named_kw_args:#把命名关键字都提取出来，存入copy这个dict
                    if name in kw:
                        copy[name] = kw[name]
                kw = copy#再把copy赋值给kw
            for k, v in request.match_info.items():#不懂
                if k in kw:
                    logging.warning('Duplicate arg name in named arg and kw args: %s' % k)
                kw[k] = v
        if self._has_request_arg:#如果有request参数，就把这个参数存入kw
            kw['request'] = request
        if self._required_kw_args:#如果有未指定默认值的命名关键字参数
            for name in self._required_kw_args:#用for循环迭代
                if not name in kw:#kw必须包含全部未指定默认值的命名关键字参数，如果发现遗漏则说明有参数没传入
                    return web.HTTPBadRequest('Missing argument: %s' % name)
        logging.info('call with args: %s' % str(kw))
        try:
            r = await self._func(**kw)
            return r
        except APIError as e:
            return dict(error=e.error, data=e.data, message=e.message)
#向app中添加静态文件目录
def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path)
    logging.info('add static %s => %s' % ('/static/', path))
#把请求处理函数注册到app
def add_route(app, fn):
    method = getattr(fn, '__method__', None)#提取函数中的方法属性
    path = getattr(fn, '__route__', None)#提取函数中的路径属性
    if path is None or method is None:#如果两个属性必须都有值，否则就报错
        raise ValueError('@get or @post not defined in %s.' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)#如果函数即不是一个协程也不是生成器，那就把函数变成一个协程
    logging.info('add route %s %s => %s(%s)' % (method, path, fn.__name__, ', '.join(inspect.signature(fn).parameters.keys())))
    app.router.add_route(method, path, RequestHandler(app, fn))#把函数注册到app
#将handlers模块中所有请求处理函数提取出来交给add_route去处理
def add_routes(app, module_name):
    #因为handlers模块在当前目录下，所以在app.py中传入的module_name是handlers
    #假设handlers模块在handler目录下，那传入的module_name就是handler.handlers
    n = module_name.rfind('.')#找出module_name中.的索引位置
    if n == (-1):#-1表示没有找到，说明模块在当前目录下，直接导入
        #查了下官方文档，__import__的作用类似import，import是为当前模块导入另一个模块，而__import__则是返回一个对象
        #大家可以在python命令行玩儿下，找找感觉。至于globals和locals，我也不知道是什么，感觉好像没什么用
        mod = __import__(module_name, globals(), locals())
    else:
        name = module_name[n+1:]#当module_name为handler.handlers时，[n+1:]就是取.后面的部分，也就是handlers
        mod = getattr(__import__(module_name[:n], globals(), locals(), [name]), name)#这就是这种情况下导入handlers模块的方式，我也不是很懂
    for attr in dir(mod):#dir(mod)应该是mod的所有属性，然后通过for循环来遍历
        if attr.startswith('_'):#下划线开头说明是私有属性，不是我们想要的，直接跳过进入下一个循环
            continue
        fn = getattr(mod, attr)#排除私有属性后，就把属性提取出来
        if callable(fn):#查看提取出来的属性是不是函数
            method = getattr(fn, '__method__', None)
            path = getattr(fn, '__route__', None)
            if method and path:#如果是函数，再判断是否有__method__和__route__属性
                add_route(app, fn)#就这样一层一层地把请求处理函数给筛选出来，然后交给add_route去处理
