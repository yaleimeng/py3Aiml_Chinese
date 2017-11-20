# -*- coding: utf-8 -*-
# 本类实现了Richard Wallace博士在以下站点描述的AIML模式匹配算法：http://www.alicebot.org/documentation/matching.html  '''


from __future__ import print_function

import marshal
import pprint
import re

from constants import *

class PatternMgr:
    # special dictionary keys
    _UNDERSCORE = 0
    _STAR       = 1
    _TEMPLATE   = 2
    _THAT       = 3
    _TOPIC      = 4
    _BOT_NAME   = 5
    
    def __init__(self):
        self._root = {}
        self._templateCount = 0
        self._botName = u"Nameless"
        punctuation = "\"`~!@#$%^&*()-_=+[{]}\|;:',<.>/?"
        self._puncStripRE = re.compile("[" + re.escape(punctuation) + "]")
        self._whitespaceRE = re.compile("\s+", re.UNICODE)

    def numTemplates(self):
        """返回当前存储的模板数量。"""
        return self._templateCount

    def setBotName(self, name):
        """设置机器人的名称，用于匹配模式中的<bot name =“name”>标签。 名字必须是一个单词！ """
        # 将多个单词的名字合并为一个单词
        self._botName = unicode( ' '.join(name.split()) )

    def dump(self):
        """打印所有学习的模式，用于调试目的。"""
        pprint.pprint(self._root)

    def save(self, filename):
        """将当前模式转储到由filename指定的文件。 要稍后恢复，请使用restore().        """
        try:
            outFile = open(filename, "wb")
            marshal.dump(self._templateCount, outFile)
            marshal.dump(self._botName, outFile)
            marshal.dump(self._root, outFile)
            outFile.close()
        except Exception as e:
            print( "Error saving PatternMgr to file %s:" % filename )
            raise

    def restore(self, filename):
        """还原以前保存过的模式集合。"""
        try:
            inFile = open(filename, "rb")
            self._templateCount = marshal.load(inFile)
            self._botName = marshal.load(inFile)
            self._root = marshal.load(inFile)
            inFile.close()
        except Exception as e:
            print( "Error restoring PatternMgr from file %s:" % filename )
            raise

    def add(self, data, template):
        """将[pattern / that / topic]元组及其相应的模板添加到节点树中。         """
        pattern,that,topic = data
        # TODO: 请确保 words只包含合法的字符！    (alphanumerics,*,_)

        # N浏览节点树到模板的位置，如有必要添加节点。
        node = self._root
        for word in pattern.split():
            key = word
            if key == u"_":
                key = self._UNDERSCORE
            elif key == u"*":
                key = self._STAR
            elif key == u"BOT_NAME":
                key = self._BOT_NAME
            if key not in node:
                node[key] = {}
            node = node[key]

        #  如果包含一个非空的“that”模式，进一步向下浏览
        if len(that) > 0:
            if self._THAT not in node:
                node[self._THAT] = {}
            node = node[self._THAT]
            for word in that.split():
                key = word
                if key == u"_":
                    key = self._UNDERSCORE
                elif key == u"*":
                    key = self._STAR
                if key not in node:
                    node[key] = {}
                node = node[key]

        # 如果包含一个非空的“topic”字符串，可以进一步导航
        if len(topic) > 0:
            if self._TOPIC not in node:
                node[self._TOPIC] = {}
            node = node[self._TOPIC]
            for word in topic.split():
                key = word
                if key == u"_":
                    key = self._UNDERSCORE
                elif key == u"*":
                    key = self._STAR
                if key not in node:
                    node[key] = {}
                node = node[key]


        # 添加模板
        if self._TEMPLATE not in node:
            self._templateCount += 1    
        node[self._TEMPLATE] = template

    def match(self, pattern, that, topic):
        """ 返回最接近模式的模板。 'that'参数包含机器人以前的回应。 “topic”参数包含当前的对话主题。
    如果没有找到模板，则返回None。        """
        if len(pattern) == 0:
            return None
        # 切断输入内容。 删除所有标点符号并将文本转换为全部大写。【关键！】
        input_ = pattern.upper()
        input_ = re.sub(self._puncStripRE, " ", input_)
        if that.strip() == u"": that = u"ULTRABOGUSDUMMYTHAT" # 'that' must never be empty
        thatInput = that.upper()
        thatInput = re.sub(self._puncStripRE, " ", thatInput)
        thatInput = re.sub(self._whitespaceRE, " ", thatInput)
        if topic.strip() == u"": topic = u"ULTRABOGUSDUMMYTOPIC" # 'topic' must never be empty
        topicInput = topic.upper()
        topicInput = re.sub(self._puncStripRE, " ", topicInput)
        
        # 将输入传递给递归调用
        patMatch, template = self._match(input_.split(), thatInput.split(), topicInput.split(), self._root)
        return template

    def star(self, starType, pattern, that, topic, index):
        """返回一个字符串，即由*匹配的模式部分。
    'starType'参数指定要找到哪种星型。  合法值是：
       - “star”：匹配主要模式中的一个星号。
       - “thatstar”：与that模式中的一个星号匹配。
       - “topicstar”：与topic模式中的一个星号匹配。        """
        # 破坏输入。 删除所有标点符号并将文本转换为全部大写。
        input_ = pattern.upper()
        input_ = re.sub(self._puncStripRE, " ", input_)
        input_ = re.sub(self._whitespaceRE, " ", input_)
        if that.strip() == u"": that = u"ULTRABOGUSDUMMYTHAT" # 'that' must never be empty
        thatInput = that.upper()
        thatInput = re.sub(self._puncStripRE, " ", thatInput)
        thatInput = re.sub(self._whitespaceRE, " ", thatInput)
        if topic.strip() == u"": topic = u"ULTRABOGUSDUMMYTOPIC" # 'topic' must never be empty
        topicInput = topic.upper()
        topicInput = re.sub(self._puncStripRE, " ", topicInput)
        topicInput = re.sub(self._whitespaceRE, " ", topicInput)

        # P将输入传递给递归  pattern-matcher
        patMatch, template = self._match(input_.split(), thatInput.split(), topicInput.split(), self._root)
        if template == None:
            return ""

        # 返回基于starType参数提取模式的适当部分。
        words = None
        if starType == 'star':
            patMatch = patMatch[:patMatch.index(self._THAT)]
            words = input_.split()
        elif starType == 'thatstar':
            patMatch = patMatch[patMatch.index(self._THAT)+1 : patMatch.index(self._TOPIC)]
            words = thatInput.split()
        elif starType == 'topicstar':
            patMatch = patMatch[patMatch.index(self._TOPIC)+1 :]
            words = topicInput.split()
        else:
            # unknown value
            raise ValueError( "starType must be in ['star', 'thatstar', 'topicstar']" )
        
        # 将输入的字符串与匹配的模式进行逐字比较。  在循环结束时，如果foundTheRightStar为true，
        # 则start和end将包含所需星形匹配子字符串的开始和结束索引（以“单词”表示）。
        foundTheRightStar = False
        start = end = j = numStars = k = 0
        for i in range(len(words)):
            # 在处理不是我们正在寻找的星星之后，这个条件是 true
            if i < k:
                continue
            # 如果我们已经达到了模式的结尾，就完成了。
            if j == len(patMatch):
                break
            if not foundTheRightStar:
                if patMatch[j] in [self._STAR, self._UNDERSCORE]: #we got a star
                    numStars += 1
                    if numStars == index:
                        # 这个是我们关心的那个 star .
                        foundTheRightStar = True
                    start = i
                    # 迭代字符串的其余部分。
                    for k in range (i, len(words)):
                        # 如果星星在模式的最后，我们知道它到底在哪里。
                        if j+1  == len (patMatch):
                            end = len (words)
                            break
                        # 如果单词已经开始再次匹配，那么这个星星就结束了。
                        # ======== 不确定：修正：对于pattch“* A B”，“A C A B”将匹配，这是一个错误
                        if patMatch[j+1] == words[k]:
                            end = k - 1
                            i = k
                            break
                # 如果我们刚刚完成处理我们所关心的星，我们会尽早退出循环。
                if foundTheRightStar:
                    break
            # 移动到模式的下一个元素。
            j += 1
            
        # 从原始的，毫不含糊的输入中提取星号。
        if foundTheRightStar:
            #print( ' '.join(pattern.split()[start:end+1]) )
            if starType == 'star': return ' '.join(pattern.split()[start:end+1])
            elif starType == 'thatstar': return ' '.join(that.split()[start:end+1])
            elif starType == 'topicstar': return ' '.join(topic.split()[start:end+1])
        else: return u""

    def _match(self, words, thatWords, topicWords, root):
        """返回一个元组（pat，tem），其中pat是节点列表，从根开始并导致匹配的模式，tem是匹配的模板。        """
        # 基本情况：如果单词列表为空，则返回当前节点的模板。
        if len(words) == 0:
            # we're out of words.
            pattern = []
            template = None
            if len(thatWords) > 0:
                # 如果该词不为空，则在_THAT节点上将该词与该词递归模式匹配。
                try:
                    pattern, template = self._match(thatWords, [], topicWords, root[self._THAT])
                    if pattern != None:
                        pattern = [self._THAT] + pattern
                except KeyError:
                    pattern = []
                    template = None
            elif len(topicWords) > 0:
                # 如果该字词为空且topicWords不为空，则以topicWords为单词在_TOPIC节点上以递归方式进行模式。
                try:
                    pattern, template = self._match(topicWords, [], [], root[self._TOPIC])
                    if pattern != None:
                        pattern = [self._TOPIC] + pattern
                except KeyError:
                    pattern = []
                    template = None
            if template == None:
                # 完全没有输入了。 在此节点抓取模板。
                pattern = []
                try: template = root[self._TEMPLATE]
                except KeyError: template = None
            return (pattern, template)

        first = words[0]
        suffix = words[1:]
        
        # Check underscore.检查下划线。
        # 注意：这是标准AIML集合中的问题，目前已被禁用。
        if self._UNDERSCORE in root:
            # 必须包含suf为[]的情况，以便处理在模式结尾处出现*或_的情况。
            for j in range(len(suffix)+1):
                suf = suffix[j:]
                pattern, template = self._match(suf, thatWords, topicWords, root[self._UNDERSCORE])
                if template is not None:
                    newPattern = [self._UNDERSCORE] + pattern
                    return (newPattern, template)

        # Check first
        if first in root:
            pattern, template = self._match(suffix, thatWords, topicWords, root[first])
            if template is not None:
                newPattern = [first] + pattern
                return (newPattern, template)

        # check bot name
        if self._BOT_NAME in root and first == self._botName:
            pattern, template = self._match(suffix, thatWords, topicWords, root[self._BOT_NAME])
            if template is not None:
                newPattern = [first] + pattern
                return (newPattern, template)
        
        # check star
        if self._STAR in root:
            # 必须包含suf为[]的情况，以便处理在模式结尾处出现*或_的情况。
            for j in range(len(suffix)+1):
                suf = suffix[j:]
                pattern, template = self._match(suf, thatWords, topicWords, root[self._STAR])
                if template is not None:
                    newPattern = [self._STAR] + pattern
                    return (newPattern, template)

        # 没有找到匹配。
        return (None, None)