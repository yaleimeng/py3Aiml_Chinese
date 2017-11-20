# -*- coding: utf-8 -*-
"""这个模块实现了WordSub类，仿照“Python Cookbook”3.14中的配方（“在单一通道中替换多个模式”）。( by Xavier Defrang).

使用说明:
像字典一样使用这个类，来 添加 before/after 配对:
    > subber = TextSub()
    > subber["before"] = "after"
    > subber["begin"] = "end"
使用sub()方法执行替换：
    > print subber.sub("before we begin")
    after we end
所有的匹配都是智能的不区分大小写：
    > print subber.sub("Before we BEGIN")
    After we END
“之前”的单词必须是完整的单词 - 没有前缀。以下示例说明了这一点：
    > subber["he"] = "she"
    > print subber.sub("he says he'd like to help her")
    she says she'd like to help her
请注意 "he" 和 "he'd" 被替换了, 但"help" 和 "her" 并没有被替换。"""

from __future__ import print_function


import re
import string
try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

class WordSub(dict):
    """多合一的多字符串替换类。."""

    def _wordToRegex(self, word):
        """将一个单词转换为与该单词匹配的正则表达式对象。"""
        if word != "" and word[0].isalpha() and word[-1].isalpha():
            return "\\b%s\\b" % re.escape(word)
        else: 
            return r"\b%s\b" % re.escape(word)
    
    def _update_regex(self):
        """基于当前字典的键 来构建 re 对象。        """
        self._regex = re.compile("|".join(map(self._wordToRegex, self.keys())))
        self._regexIsDirty = False

    def __init__(self, defaults = {}):
        """初始化对象, 用默认字典中的条目填充它。        """
        self._regex = None
        self._regexIsDirty = True
        for k,v in defaults.items():
            self[k] = v

    def __call__(self, match):
        """ 为每个正则表达式匹配触发  Handler。"""
        return self[match.group(0)]

    def __setitem__(self, i, y):
        self._regexIsDirty = True
        #  对于用户添加的每个条目，我们实际添加三个入口：
        super(type(self),self).__setitem__(i.lower(),y.lower()) # key = value
        super(type(self),self).__setitem__(string.capwords(i), string.capwords(y)) # Key = Value
        super(type(self),self).__setitem__(i.upper(), y.upper()) # KEY = VALUE

    def sub(self, text):
        """翻译文本，返回修改后的文本。"""
        if self._regexIsDirty:
            self._update_regex()
        return self._regex.sub(self, text)