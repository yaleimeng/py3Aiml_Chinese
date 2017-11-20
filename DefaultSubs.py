"""本文件包含PyAIML内核的默认（英文）替换。 使用Kernel.loadSubs（filename）方法可以覆盖这些替换。
 指定的文件名应使用以下格式引用Windows风格的INI文件：

   # “gender”部分包含由<gender> AIML标记执行的替换，它交换了男性和女性代词。
    # “person”部分包含由<person> AIML标记执行的替换，它交换第一和第二人称代词。
    # “person2”部分包含由<person2> AIML标记执行的替换，它交换第一和第三人称代词。

    # “normal”部分包含对传入Kernel.respond()的每个输入字符串运行的结构。
    它主要用于纠正常见的拼写错误，并将缩写“what's”转换为匹配AIML模式“WHAT IS”的格式。
    [normal]
    what's = what is                    """

defaultGender = {
    # masculine -> feminine
    "he": "she",
    "他": "她",
    "him": "her",
    "his": "her",
    "himself": "herself",

    # feminine -> masculine    
    "she": "he",
    "她": "他",
    "her": "him",
    "hers": "his",
    "herself": "himself",
}

defaultPerson = {
    # 第一人称->第三人称 (masculine)
    "I": "he",
    "me": "him",
    "my": "his",
    "mine": "his",
    "myself": "himself",
    "我": "她",

    # 第三人称->第一人称(masculine)
    "he":"I",
    "him":"me",
    "his":"my",
    "himself":"myself",
    "他":"我",
    
    # 第三人称-> 第一人称 (feminine)
    "she":"I",
    "her":"me",
    "hers":"mine",
    "herself":"myself",
    "她":"我",
}

defaultPerson2 = {
    # 第一人称 -> 第二人称
    "I": "you",
    "me": "you",
    "my": "your",
    "mine": "yours",
    "myself": "yourself",
    "我": "你",
    "我们": "你们",

    # 第二人称 -> 第一人称
    "you": "me",
    "your": "my",
    "yours": "mine",
    "yourself": "myself",
}


# TODO: 这个列表还远远没有完成……
defaultNormal = {
    "wanna": "want to",
    "gonna": "going to",

    "I'm": "I am",
    "I'd": "I would",
    "I'll": "I will",
    "I've": "I have",
    "you'd": "you would",
    "you're": "you are",
    "you've": "you have",
    "you'll": "you will",
    "he's": "he is",
    "he'd": "he would",
    "he'll": "he will",
    "she's": "she is",
    "she'd": "she would",
    "she'll": "she will",
    "we're": "we are",
    "we'd": "we would",
    "we'll": "we will",
    "we've": "we have",
    "they're": "they are",
    "they'd": "they would",
    "they'll": "they will",
    "they've": "they have",

    "y'all": "you all",    

    "can't": "can not",
    "cannot": "can not",
    "couldn't": "could not",
    "wouldn't": "would not",
    "shouldn't": "should not",
    
    "isn't": "is not",
    "ain't": "is not",
    "don't": "do not",
    "aren't": "are not",
    "won't": "will not",
    "weren't": "were not",
    "wasn't": "was not",
    "didn't": "did not",
    "hasn't": "has not",
    "hadn't": "had not",
    "haven't": "have not",

    "where's": "where is",
    "where'd": "where did",
    "where'll": "where will",
    "who's": "who is",
    "who'd": "who did",
    "who'll": "who will",
    "what's": "what is",
    "what'd": "what did",
    "what'll": "what will",
    "when's": "when is",
    "when'd": "when did",
    "when'll": "when will",
    "why's": "why is",
    "why'd": "why did",
    "why'll": "why will",

    "it's": "it is",
    "it'd": "it would",
    "it'll": "it will",
}
