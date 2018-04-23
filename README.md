# py3Aiml_Chinese
官方py3版本的AIML基于英文，现为其增加中文支持，并翻译了代码中的注释。实测可正确解析带中文pattern和模板的aiml文件。

本想找到一个py3的中文aiml项目直接上手，没想到困难重重。有的无法执行，有的又是py2版本。网上关于改写的资料也少，大部分只提到思路。</br>
本项目得益于：

项目名|链接（安装）|说明
:-:|:-|:-
py2版本的中文aiml|[py2AIML](https://github.com/andelf/PyAIML) |不支持py3
python-aiml|pip install python-aiml| 0.9.1版本，核心代码可用。可使用英文模板库
aiml|pip install aiml|不能直接用。但带有Alice的英文模板库。

查找相关资源可以：pip search aiml

众所周知，python2的文字编码问题是个万人坑，所以py3是文字处理的最佳选择。所以在通读了支持中文的py2版本aiml整个项目之后，着手进行py3 0.91版本的修改。去除了一些冗余代码。保持了代码的整洁有序。<br>
眼见为实，上图：<br>
![示例聊天图片](https://github.com/yaleimeng/py3Aiml_Chinese/blob/master/alice.png)

大家如果有疑问可发Issue与我交流，若有完善，提PullRequest更加欢迎。</br>
现在Chatbot方面**又有[ChatScript](https://github.com/ChatScript/ChatScript)可选**。只可惜关于中文改造内容也比较少。欢迎一起探讨。
