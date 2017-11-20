# -*- coding: utf-8 -*-
'''
@author: yaleimeng@sina.com
@license: (C) Copyright 2017
@desc:  python3 版本中文Alice，暂时简单添加空格
@DateTime: Created on 2017/11/15，at  10:20       '''

import Kernel

alice = Kernel.Kernel()
alice.learn("cn-test.aiml")

while True:
    print(alice.respond(input('Alice请您提问...>>')))
