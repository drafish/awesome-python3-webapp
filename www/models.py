#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Models for user, blog, comment.
'''

__author__ = 'Michael Liao'

import time, uuid

from orm import Model, StringField, BooleanField, FloatField, TextField

def next_id():
    #看别的小伙伴的解释说uuid4()是用来生成随机数的，我也是懒的求证了，这边会用就行了
    #time.time()就是返回当前时间戳
    #这个函数的作用就是生成一个和当前时间有关的独一无二的id，来做为数据库表中每一行的主键
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)

class User(Model):
    __table__ = 'users'				#定义表名

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')#定义id为主键，调用next_id方法后获得默认值
    email = StringField(ddl='varchar(50)')	#邮箱
    passwd = StringField(ddl='varchar(50)')	#密码
    admin = BooleanField()			#管理员身份，值为1表示该用户为管理员，值为0表示该用户不是管理员
    name = StringField(ddl='varchar(50)')	#名字
    image = StringField(ddl='varchar(500)')	#应该是头像吧
    created_at = FloatField(default=time.time)	#创建时间默认为当前时间，也是要调用time.time方法后获得

class Blog(Model):
    __table__ = 'blogs'
    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')	#作者id
    user_name = StringField(ddl='varchar(50)')	#作者名
    user_image = StringField(ddl='varchar(500)')#作者上传的图片
    name = StringField(ddl='varchar(50)')	#文章名
    summary = StringField(ddl='varchar(200)')	#文章概要
    content = TextField()			#文章正文
    created_at = FloatField(default=time.time)

class Comment(Model):
    __table__ = 'comments'
    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    blog_id = StringField(ddl='varchar(50)')	#博客id
    user_id = StringField(ddl='varchar(50)')	#评论者id
    user_name = StringField(ddl='varchar(50)')	#评论者名字
    user_image = StringField(ddl='varchar(500)')#评论者上传的图片
    content = TextField()			#评论内容
    created_at = FloatField(default=time.time)
