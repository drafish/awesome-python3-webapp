#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'xwlyy'

'''
async web application.
'''

#logging的作用就是输出一些信息，比如说下面的server started at http://127.0.0.1:9000...
#python3 app.py之后可以在命令行看到这条信息，logging输出的信息可以帮助我们理解程序执行的流程，对后期除错也非常有帮助
#logging.basicConfig配置需要输出的信息等级，INFO指的是普通信息，INFO以及INFO以上的比如说WARNING警告信息也会被输出
import logging; logging.basicConfig(level=logging.INFO)
#引入对异步IO的支持，概念上有些不熟悉的话可以温习一下‘asyncio’这一小节
#我自己对异步IO的理解也不是很清晰，特别是loop的用法一直糊里糊涂的，现阶段我觉得知道在哪儿用知道怎么用就够了，不用太过纠结
import asyncio, os, json, time
#datetime还有上面的os，json，time暂时都没用到，用到了再说
from datetime import datetime
#aiohttp是基于asyncio实现的HTTP框架，web应该是用来处理http请求的对象，对web的理解我也不是很清晰
#当我碰到一个难以理解的东西的时候，我都会先把它理解为一个对象，因为面向对象编程中万物皆对象，理解为对象肯定是没错的
#然后观察它的用法，看这个对象在代码中到底起了什么作用，这样就能大致推断出这是个什么
from aiohttp import web

#定义处理http访问请求的方法
def index(request):
    #其实从字面意思可以理解为，把等号后面的内容作为响应的body返回
    return web.Response(body=b'<h1>Awesome</h1>')
async def init(loop):
    #往web对象中加入消息循环，生成一个支持异步IO的对象
    app = web.Application(loop=loop)
    #将浏览器通过GET方式传过来的对根目录的请求转发给index函数处理
    app.router.add_route('GET', '/', index)
    #监听127.0.0.1地址的9000端口
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    #以后碰到logging都要多留个心眼儿，现阶段还看不出有什么用，但越到后面越有用
    logging.info('server started at http://127.0.0.1:9000...')
    #把监听http请求的这个协程返回给loop，这样就能持续监听http请求，应该是这样吧，我也不太确定
    return srv
#loop我也不是很懂，还是那句话，知道在哪儿用知道怎么用就够了
loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
