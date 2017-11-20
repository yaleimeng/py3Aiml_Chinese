# -*- coding: utf-8 -*-
'''     AIML文件的解析器       '''

from __future__ import print_function
from LangSupport import splitChinese

from xml.sax.handler import ContentHandler
from xml.sax.xmlreader import Locator
import sys
import xml.sax
import xml.sax.handler

from constants import *


class AimlParserError(Exception): 
    pass


class AimlHandler(ContentHandler):
    ''' AIML文件的 一个 SAX handler    '''

    # AIML parser 的合法状态
    _STATE_OutsideAiml    = 0
    _STATE_InsideAiml     = 1
    _STATE_InsideCategory = 2
    _STATE_InsidePattern  = 3
    _STATE_AfterPattern   = 4
    _STATE_InsideThat     = 5
    _STATE_AfterThat      = 6
    _STATE_InsideTemplate = 7
    _STATE_AfterTemplate  = 8


    def __init__(self, encoding=None):
        self.categories = {}
        self._encoding = encoding
        self._state = self._STATE_OutsideAiml
        self._version = ""
        self._namespace = ""
        self._forwardCompatibleMode = False
        self._currentPattern = ""
        self._currentThat    = ""
        self._currentTopic   = ""
        self._insideTopic = False
        self._currentUnknown = "" # the name of the current unknown element

        # 在类别中发生分析错误时，将其设置为true。
        self._skipCurrentCategory = False

        # 统计特定AIML文档中解析错误的数量。用getNumErrors()查询。 如果为0，则文档符合AIML。
        self._numParseErrors = 0

        # TODO: 根据版本号选择合适的validInfo表。
        self._validInfo = self._validationInfo101

        # 这个bool值栈在解析<condition>元素中的<li>元素时，用来跟踪是否已经找到了一个无属性的“default”<li>元素。
        # 每个<condition>元素中只允许有一个默认的<li>。  我们需要一个栈来正确处理嵌套的<condition>标签。
        self._foundDefaultLiStack = []

        # 这个字符串堆栈表示当前的空白处理行为应该是什么。堆栈中的每个字符串都是"default" 或"preserve"。
        # 当遇到一个新的AIML元素时，根据元素的“xml：space”属性的值（如果没有，堆栈顶部被再次push），一个新的字符串被压入栈中。
        # 一个元素结束时，从堆栈中弹出一个对象。
        self._whitespaceBehaviorStack = ["default"]
        
        self._elemStack = []
        self._locator = Locator()
        self.setDocumentLocator(self._locator)

    def getNumErrors(self):
        "返回解析当前文档时发现的错误数。"
        return self._numParseErrors

    def setEncoding(self, encoding):
        """设置在对从XML读取的字符串进行编码时使用的文本编码。  默认为'UTF-8'。        """
        self._encoding = encoding

    def _location(self):
        "返回描述源文件中当前位置的字符串。"
        line = self._locator.getLineNumber()
        column = self._locator.getColumnNumber()
        return "(line %d, column %d)" % (line, column)

    def _pushWhitespaceBehavior(self, attr):
        """将一个新的字符串推送到_whitespaceBehaviorStack。
     该字符串的值取自“xml：space”属性，如果它存在且具有合法值（“default”或“preserve”）。
         否则，以前的堆栈元素是重复的。         """
        assert len(self._whitespaceBehaviorStack) > 0, "Whitespace behavior stack should never be empty!"
        try:
            if attr["xml:space"] == "default" or attr["xml:space"] == "preserve":
                self._whitespaceBehaviorStack.append(attr["xml:space"])
            else:
                raise AimlParserError( "Invalid value for xml:space attribute "+self._location() )
        except KeyError:
            self._whitespaceBehaviorStack.append(self._whitespaceBehaviorStack[-1])

    def startElementNS(self, name, qname, attr):
        print( "QNAME:", qname )
        print( "NAME:", name )
        uri,elem = name
        if (elem == "bot"): 
                    print( "name:", attr.getValueByQName("name"), "a'ite?" )
        self.startElement(elem, attr)
        pass

    def startElement(self, name, attr):
        # 包装在_startElement周围，捕获_startElement（）中的错误并继续前进。
        # 如果我们在一个未知的元素内，那么在再次出来之前，不要理会任何东西。
        if self._currentUnknown != "":
            return
        #  如果我们跳过当前类别，则在完成之前忽略所有内容。
        if self._skipCurrentCategory:
            return

        # 处理这个起始元素.
        try: self._startElement(name, attr)
        except AimlParserError as err:
            # 打印错误消息
            sys.stderr.write("PARSE ERROR: %s\n" % err)
            
            self._numParseErrors += 1 # increment error count
            # 当发生解析错误时，如果在一个category内，跳过它。
            if self._state >= self._STATE_InsideCategory:
                self._skipCurrentCategory = True
            
    def _startElement(self, name, attr):
        if name == "aiml":
            # <aiml> tags are only legal in the OutsideAiml state
            if self._state != self._STATE_OutsideAiml:
                raise AimlParserError( "Unexpected <aiml> tag "+self._location() )
            self._state = self._STATE_InsideAiml
            self._insideTopic = False
            self._currentTopic = u""
            try: self._version = attr["version"]
            except KeyError:
                # 这原本应该是一个语法错误，但是大量的AIML被指出缺少“版本”属性，让它溜走似乎更好。
                #raise AimlParserError( "Missing 'version' attribute in <aiml> tag "+self._location() )
                #print( "WARNING: Missing 'version' attribute in <aiml> tag "+self._location() )
                #print( "         Defaulting to version 1.0" )
                self._version = "1.0"
            self._forwardCompatibleMode = (self._version != "1.0.1")
            self._pushWhitespaceBehavior(attr)          
            # 这个名字空间的业务尚不明确......
            #try:
            #   self._namespace = attr["xmlns"]
            #   if self._version == "1.0.1" and self._namespace != "http://alicebot.org/2001/AIML-1.0.1":
            #       raise AimlParserError( "Incorrect namespace for AIML v1.0.1 "+self._location() )
            #except KeyError:
            #   if self._version != "1.0":
            #       raise AimlParserError( "Missing 'version' attribute(s) in <aiml> tag "+self._location() )
        elif self._state == self._STATE_OutsideAiml:
            # 如果在AIML元素之外，我们会忽略所有的标签。
            return
        elif name == "topic":
            # <topic>标签只有在 InsideAiml 状态，而且不在在一个<topic>内。才是合法的，
            if (self._state != self._STATE_InsideAiml) or self._insideTopic:
                raise AimlParserError( "Unexpected <topic> tag", self._location() )
            try: self._currentTopic = unicode(attr['name'])
            except KeyError:
                raise AimlParserError( "Required \"name\" attribute missing in <topic> element "+self._location() )
            self._insideTopic = True
        elif name == "category":
            # <category> 标签只有在 InsideAiml 状态才是合法的
            if self._state != self._STATE_InsideAiml:
                raise AimlParserError( "Unexpected <category> tag "+self._location() )
            self._state = self._STATE_InsideCategory
            self._currentPattern = u""
            self._currentThat = u""
            # 如果不在 topic 内部, topic 被隐式设置为 *
            if not self._insideTopic: self._currentTopic = u"*"
            self._elemStack = []
            self._pushWhitespaceBehavior(attr)
        elif name == "pattern":
            # <pattern> 标签只有在 InsideCategory 状态才是合法的
            if self._state != self._STATE_InsideCategory:
                raise AimlParserError( "Unexpected <pattern> tag "+self._location() )
            self._state = self._STATE_InsidePattern
        elif name == "that" and self._state == self._STATE_AfterPattern:
            # <that> 只有在 <template> 元素内部, 或者在 <category> 元素内部而且在 <pattern> 与<template> 元素之间
            # 才是合法的。  本条款处理后一种情况。
            self._state = self._STATE_InsideThat
        elif name == "template":
            # <template> 标签只有在 AfterPattern 和 AfterThat 状态才是合法的
            if self._state not in [self._STATE_AfterPattern, self._STATE_AfterThat]:
                raise AimlParserError( "Unexpected <template> tag "+self._location() )
            # 如果不指定 <that> 元素, 它被隐式设置为 *
            if self._state == self._STATE_AfterPattern:
                self._currentThat = u"*"
            self._state = self._STATE_InsideTemplate
            self._elemStack.append(['template',{}])
            self._pushWhitespaceBehavior(attr)
        elif self._state == self._STATE_InsidePattern:
            # 特定的一些标签在<pattern> 元素中是允许的。
            if name == "bot" and "name" in attr and attr["name"] == u"name":
                # 插入一个 PatternMgr 将会用 bot的名字替换掉的 特定的字符串 。
                self._currentPattern += u" BOT_NAME "
            else:
                raise AimlParserError( ( "Unexpected <%s> tag " % name)+self._location() )
        elif self._state == self._STATE_InsideThat:
            # 特定的一些标签在<that>元素中是允许的。
            if name == "bot" and "name" in attr and attr["name"] == u"name":
                # 插入一个 PatternMgr 将会用 bot的名字替换掉的 特定的字符串 。
                self._currentThat += u" BOT_NAME "
            else:
                raise AimlParserError( ("Unexpected <%s> tag " % name)+self._location() )
        elif self._state == self._STATE_InsideTemplate and name in self._validInfo:
            # 在当前模式中开始一个新元素。 首先，需要将'attr'转换成一个本地的Python字典，以便将来可以编组。 marshaled. marshaled.
            it = ( (unicode(k),unicode(v)) for k,v in attr.items() )
            attrDict = dict( it )
            self._validateElemStart(name, attrDict, self._version)
            # 将当前元素推入元素堆栈。
            self._elemStack.append( [unicode(name),attrDict] )
            self._pushWhitespaceBehavior(attr)
            # 如果这是一个条件元素，则将新入口推送到foundDefaultLiStack
            if name == "condition":
                self._foundDefaultLiStack.append(False)
        else:
            #  现在我们处于一个未知元素的内部。
            if self._forwardCompatibleMode:
                # In Forward Compatibility Mode, 在向前兼容模式下，我们忽略元素及其内容。
                self._currentUnknown = name
            else:
                #  否则，不明的元素应该判断为错误！
                raise AimlParserError( ("Unexpected <%s> tag " % name)+self._location() )

    def characters(self, ch):
        # 包装在_characters（）中捕获错误的_characters周围，并继续前进。
        if self._state == self._STATE_OutsideAiml:
            #  如果在AIML元素之外，则忽略所有文本
            return
        if self._currentUnknown != "":
            # 如果在一个未知元素内部，则忽略所有文本
            return
        if self._skipCurrentCategory:
            # 如果我们跳过目前的类别，则忽略所有文本
            return
        try: self._characters(ch)
        except AimlParserError as msg:
            # 打印消息
            sys.stderr.write("PARSE ERROR: %s\n" % msg)
            self._numParseErrors += 1       # 错误计数加1
            # 当发生解析错误时，如果在一个category类别内，跳过它。
            if self._state >= self._STATE_InsideCategory:
                self._skipCurrentCategory = True
            
    def _characters(self, ch):
        text = unicode(ch)
        if self._state == self._STATE_InsidePattern:
            # TODO: text inside patterns must be upper-case!
            self._currentPattern += text
        elif self._state == self._STATE_InsideThat:
            self._currentThat += text
        elif self._state == self._STATE_InsideTemplate:
            # 首先，查看元素堆栈顶部的元素是否允许包含文本。
            try:
                parent = self._elemStack[-1][0]
                parentAttr = self._elemStack[-1][1]
                required, optional, canBeParent = self._validInfo[parent]
                nonBlockStyleCondition = (parent == "condition" and not ("name" in parentAttr and "value" in parentAttr))
                if not canBeParent:
                    raise AimlParserError( ("Unexpected text inside <%s> element "%parent)+self._location() )
                elif parent == "random" or nonBlockStyleCondition:
                    # <random> 元素只能包含 <li> 子元素。 However,  there's invariably 一些空白 around the <li> that 我们需要忽略的。
                    # 非块风格的 <condition> 元素也一样 (i.e.   those 没有 both a "name" and a "value" 属性).
                    if len(text.strip()) == 0:
                        # 忽略这些元素内部的 空格
                        return
                    else:
                        # 这些元素内部的非空白文本是一个语法错误。
                        raise AimlParserError( ("Unexpected text inside <%s> element "%parent)+self._location() )
            except IndexError:
                # 元素堆栈为空。这种事永远不该发生。
                raise AimlParserError( "Element stack is empty while validating text "+self._location() )
            
            # 向元素堆栈顶部的元素添加一个新的文本元素。如果已经有一个文本元素，只需将新字符添加到它的内容中。
            try: textElemOnStack = (self._elemStack[-1][-1][0] == "text")
            except IndexError: textElemOnStack = False
            except KeyError: textElemOnStack = False
            if textElemOnStack:
                self._elemStack[-1][-1][2] += text
            else:
                self._elemStack[-1].append(["text", {"xml:space": self._whitespaceBehaviorStack[-1]}, text])
        else:
            # all other text is ignored
            pass

    def endElementNS(self, name, qname):
        uri, elem = name
        self.endElement(elem)
        
    def endElement(self, name):
        """包装在_characters（）中捕获错误的_endElement周围，并继续前进。       """
        if self._state == self._STATE_OutsideAiml:
            # 如果在AIML元素之外，则忽略所有文本
            return
        if self._currentUnknown != "":
            # 看看我们是否处在一个未知的元素的末尾。如果是，我们就可以停止忽视一切。
            if name == self._currentUnknown:
                self._currentUnknown = ""
            return
        if self._skipCurrentCategory:
            # 如果我们跳过当前类别，看看它是否结束。我们停在任何</ category>标签上，因为我们没有在忽略模式下跟踪状态。
            if name == "category":
                self._skipCurrentCategory = False
                self._state = self._STATE_InsideAiml
            return
        try: self._endElement(name)
        except AimlParserError as msg:
            # 打印错误消息
            sys.stderr.write("PARSE ERROR: %s\n" % msg)
            self._numParseErrors += 1 # increment error count
            # 当发生解析错误时，如果在一个category内，跳过它。
            if self._state >= self._STATE_InsideCategory:
                self._skipCurrentCategory = True

    def _endElement(self, name):
        """验证AIML结束元素在当前上下文中是否有效。 如果遇到非法的结束元素，则引发AimlParserError。        """
        if name == "aiml":
            # </aiml> 标签只有在 InsideAiml 状态才是合法的
            if self._state != self._STATE_InsideAiml:
                raise AimlParserError( "Unexpected </aiml> tag "+self._location() )
            self._state = self._STATE_OutsideAiml
            self._whitespaceBehaviorStack.pop()
        elif name == "topic":
            # </topic> 标签只有在InsideAiml 状态, 而且 _insideTopic 为 true才是合法的。
            if self._state != self._STATE_InsideAiml or not self._insideTopic:
                raise AimlParserError( "Unexpected </topic> tag "+self._location() )
            self._insideTopic = False
            self._currentTopic = u""
        elif name == "category":
            # </category> 标签只有在 AfterTemplate  状态才是合法的
            if self._state != self._STATE_AfterTemplate:
                raise AimlParserError( "Unexpected </category> tag "+self._location() )
            self._state = self._STATE_InsideAiml
            # 结束当前类别。 将当前 pattern/ that / topic和元素存储在类别字典中。
            #【注意：这里修改了当前模式，用中文分割结果做了替换。。】
            self._currentPattern = u' '.join(splitChinese(self._currentPattern))
            key = (self._currentPattern.strip(), self._currentThat.strip(),self._currentTopic.strip())
            self.categories[key] = self._elemStack[-1]
            self._whitespaceBehaviorStack.pop()
        elif name == "pattern":
            # </pattern> 标签只有在 InsidePattern 状态才是合法的。
            if self._state != self._STATE_InsidePattern:
                raise AimlParserError( "Unexpected </pattern> tag "+self._location() )
            self._state = self._STATE_AfterPattern
        elif name == "that" and self._state == self._STATE_InsideThat:
            #  </ that>标签只允许在<template>元素内部，或InsideThat状态下。本条款处理后一种情况。
            self._state = self._STATE_AfterThat
        elif name == "template":
            # </template> 标签只允许在 InsideTemplate 状态出现。
            if self._state != self._STATE_InsideTemplate:
                raise AimlParserError( "Unexpected </template> tag "+self._location() )
            self._state = self._STATE_AfterTemplate
            self._whitespaceBehaviorStack.pop()
        elif self._state == self._STATE_InsidePattern:
            # 特定的标签允许在 <pattern> 元素内部出现。
            if name not in ["bot"]:
                raise AimlParserError( ("Unexpected </%s> tag " % name)+self._location() )
        elif self._state == self._STATE_InsideThat:
            # 特定的标签允许在 <that> 元素内部出现.
            if name not in ["bot"]:
                raise AimlParserError( ("Unexpected </%s> tag " % name)+self._location() )
        elif self._state == self._STATE_InsideTemplate:
            # 当前模板内的元素结束。 将堆栈顶部的元素追加到下面的元素上。
            elem = self._elemStack.pop()
            self._elemStack[-1].append(elem)
            self._whitespaceBehaviorStack.pop()
            #  如果元素是一个条件，那么也可以从foundDefaultLiStack中弹出一个条目。
            if elem[0] == "condition": self._foundDefaultLiStack.pop()
        else:
            # 意外的关闭标签
            raise AimlParserError( ("Unexpected </%s> tag " % name)+self._location() )

    # 包含每个AIML元素的验证信息的字典。 键是元素的名称。 值是三项的元组。
    # 第一个是包含REQUIRED 必需属性名称的列表，第二个是 OPTIONAL 可选属性列表，
    # 第三个是指示元素是否可以包含其他元素和/或文本的布尔值（如果为False，元素只能出现在原子上下文中，比如<date/>）。
    _validationInfo101 = {
        "bot":          ( ["name"], [], False ),
        "condition":    ( [], ["name", "value"], True ), # can only contain <li> elements
        "date":         ( [], [], False ),
        "formal":       ( [], [], True ),
        "gender":       ( [], [], True ),
        "get":          ( ["name"], [], False ),
        "gossip":       ( [], [], True ),
        "id":           ( [], [], False ),
        "input":        ( [], ["index"], False ),
        "javascript":   ( [], [], True ),
        "learn":        ( [], [], True ),
        "li":           ( [], ["name", "value"], True ),
        "lowercase":    ( [], [], True ),
        "person":       ( [], [], True ),
        "person2":      ( [], [], True ),
        "random":       ( [], [], True ), # can only contain <li> elements
        "sentence":     ( [], [], True ),
        "set":          ( ["name"], [], True),
        "size":         ( [], [], False ),
        "sr":           ( [], [], False ),
        "srai":         ( [], [], True ),
        "star":         ( [], ["index"], False ),
        "system":       ( [], [], True ),
        "template":     ( [], [], True ), # needs to be in the list because it can be a parent.
        "that":         ( [], ["index"], False ),
        "thatstar":     ( [], ["index"], False ),
        "think":        ( [], [], True ),
        "topicstar":    ( [], ["index"], False ),
        "uppercase":    ( [], [], True ),
        "version":      ( [], [], False ),
    }

    def _validateElemStart(self, name, attr, version):
        """测试在<template>元素内开始元素的有效性。如果标签无效，此函数将引发AimlParserError异常。否则，没有消息是好消息。"""

        #检查元素的属性。 确保所有必需的属性都存在，并且其余的属性都是有效的选项。
        required, optional, canBeParent = self._validInfo[name]
        for a in required:
            if a not in attr and not self._forwardCompatibleMode:
                raise AimlParserError( ("Required \"%s\" attribute missing in <%s> element " % (a,name))+self._location() )
        for a in attr:
            if a in required: continue
            if a[0:4] == "xml:": continue # attributes in the "xml" namespace can appear anywhere
            if a not in optional and not self._forwardCompatibleMode:
                raise AimlParserError( ("Unexpected \"%s\" attribute in <%s> element " % (a,name))+self._location() )

        # 特殊情况: several tags 包含一个可选的"index" 属性。 这个 attribute 的值 必须是一个正整数。
        if name in ["star", "thatstar", "topicstar"]:
            for k,v in attr.items():
                if k == "index":
                    temp = 0
                    try: temp = int(v)
                    except:
                        raise AimlParserError( ("Bad type for \"%s\" attribute (expected integer, found \"%s\") " % (k,v))+self._location() )
                    if temp < 1:
                        raise AimlParserError( ("\"%s\" attribute must have non-negative value " % (k))+self._location() )

        # 查看包含的元素是否被允许包含子元素。 如果不是，不管它是什么，这个元素都是无效的。
        try:
            parent = self._elemStack[-1][0]
            parentAttr = self._elemStack[-1][1]
        except IndexError:
            #  如果堆栈为空，则不存在父代。 这绝不应该发生。
            raise AimlParserError( ("Element stack is empty while validating <%s> " % name)+self._location() )
        required, optional, canBeParent = self._validInfo[parent]
        nonBlockStyleCondition = (parent == "condition" and not ("name" in parentAttr and "value" in parentAttr))
        if not canBeParent:
            raise AimlParserError( ("<%s> elements cannot have any contents "%parent)+self._location() )
        # 特殊情况测试 ：如果父元素是<condition>（非块式变体）或<random>，则这些元素只能包含<li>子元素。
        elif (parent == "random" or nonBlockStyleCondition) and name!="li":
            raise AimlParserError( ("<%s> elements can only contain <li> subelements "%parent)+self._location() )
        # <li>元素的特殊情况测试，只能由非块式<condition>和<random>元素包含，其必需属性取决于<condition>父级中存在的属性。
        elif name=="li":
            if not (parent=="random" or nonBlockStyleCondition):
                raise AimlParserError( ("Unexpected <li> element contained by <%s> element "%parent)+self._location() )
            if nonBlockStyleCondition:
                if "name" in parentAttr:
                    # 单谓词条件。 除了最后一个，每个<li>元素都必须有一个“value”属性。
                    if len(attr) == 0:
                        # 这可能是这个<condition>的默认<li>元素，除非我们已经找到一个。
                        if self._foundDefaultLiStack[-1]:
                            raise AimlParserError( "Unexpected default <li> element inside <condition> "+self._location() )
                        else:
                            self._foundDefaultLiStack[-1] = True
                    elif len(attr) == 1 and "value" in attr:
                        pass # 这是valid case
                    else:
                        raise AimlParserError( "Invalid <li> inside single-predicate <condition> "+self._location() )
                elif len(parentAttr) == 0:
                    # 多谓词条件。 除了最后一个，每个<li>元素都必须有一个“value”属性。
                    if len(attr) == 0:
                        # 这可能是这个<condition>的默认<li>元素，除非我们已经找到一个。
                        if self._foundDefaultLiStack[-1]:
                            raise AimlParserError( "Unexpected default <li> element inside <condition> "+self._location() )
                        else:
                            self._foundDefaultLiStack[-1] = True
                    elif len(attr) == 2 and "value" in attr and "name" in attr:
                        pass # 这是 valid case
                    else:
                        raise AimlParserError( "Invalid <li> inside multi-predicate <condition> "+self._location() )
        # All is well!
        return True

def create_parser():
    """创建并返回一个 AIML 解析器对象。"""
    parser = xml.sax.make_parser()
    handler = AimlHandler("UTF-8")
    parser.setContentHandler(handler)
    #parser.setFeature(xml.sax.handler.feature_namespaces, True)
    return parser
