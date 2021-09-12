#-*- conding:utf-8 -*-
from pypinyin import lazy_pinyin
from pypinyin import Style
import itertools
import copy
import time
import re
import ahocorasick

'''
汉字 => {拼音，拼音首字母， 拆字}
'''

def word_to_pinyin(word):
    return lazy_pinyin(word)[0]

def word_to_pinyin_first(word):
    return lazy_pinyin(word, style=Style.FIRST_LETTER)[0]

def iszh(word):
    for c in word:
        if not '\u4e00' <= c <= '\u9fa5':
            return False
    return True

#得到笛卡儿积，以list形式返回，值为字符串
#传入敏感词
def get_product(words): 
    data_list = []
    for word in words:
        tmp = []
        if iszh(word):
            tmp.append(word_to_pinyin(word))
            tmp.append(word_to_pinyin_first(word))
        else:
            tmp.append(word)
        data_list.append(tmp)
    res = []
    for _ in itertools.product(*data_list):
        res.append(list(_))
    return res

class AhocorasickNer:
    def __init__(self, user_dict_list):
        self.user_dict_list = user_dict_list
        self.actree = ahocorasick.Automaton() #初始化AC自动机

    def add_keywords(self):
        #idx:索引 key:字符
        for idx, key in enumerate(self.user_dict_list):
            self.actree.add_word(key, (idx, key))
        self.actree.make_automaton() #构建fail指针

    def get_match_result(self, sentence):
        res = [] #保存答案
        #end_indx:匹配结果在sentenc中的末尾索引
        #insert_order:匹配结果在AC机中的索引
        for end_index, (insert_order, original_value) in self.actree.iter(sentence):
            strat_index = end_index - len(original_value) + 1
            #print((strat_index, end_index + 1), (insert_order, original_value))
            res.append([strat_index, end_index])

        return res

class MyRegex(object):
    def __init__(self, file_name):
        self.file_name = file_name
        self.regex_dict = {} #敏感词正则表达式

    def make_regex(self):
        with open(self.file_name, "r", encoding="utf-8") as f:
            for ban_word in f.readlines():
                is_first = True
                pattern = ""
                for char in ban_word:
                    if char == '\n' or char.isdigit():
                        break
                    elif char.encode("utf-8").isalpha():
                        if is_first:
                            is_first = False
                        else:
                            pattern += "[^a-zA-Z]*"
                        pattern += "(?:" + char + ")"
                    else:
                        if is_first:
                            is_first = False
                        else:
                            pattern += "[^\\u4e00-\\u9fa5]*"
                        pattern += "(?:{}|{}|{})".format(char, word_to_pinyin(char), word_to_pinyin_first(char))
                #print(pattern)
                self.regex_dict[ban_word.strip()] = pattern    

class BanWordDict(object):
    def __init__(self, file_name):
        self.file_name = file_name #待匹配文本
        self.new_word = [] #文本中的敏感词
        self.new_to_original = {} #文本到黑名单的映射

    def make_word(self, regex):
        with open(self.file_name, "r", encoding="utf-8") as f:
            for line in f.readlines():
                for key, val in regex.items():
                    #初次匹配
                    it = re.findall(val, line, re.I)
                    for res in it:
                        self.new_to_original[res] = key
                        self.new_word.append(res)
                    if key.encode("utf-8").isalpha():
                        continue
                    #谐音匹配
                    mp = {}
                    line = list(line)
                    for i in range(len(line)):
                        _cur = lazy_pinyin(line[i])[0]
                        _key = lazy_pinyin(key)
                        if _cur in _key:
                            to = key[_key.index(_cur)]
                            mp[i] = line[i]
                            line[i] = to
                    line = ''.join(line)
                    it = re.findall(val, line, re.I)
                    for res in it:
                        pos = line.index(res)
                        for i in range(len(res)):
                            if pos + i in mp.keys():
                                res = res.replace(res[i], mp[pos + i])
                        self.new_to_original[res] = key
                        self.new_word.append(res)
            self.new_word = list(set(self.new_word))
            #for it in self.new_word:
            #    print(it)




if __name__ == "__main__":
    content = "法轮功和鱼一起摸鱼吧，我要死了。。。粗来，，22112，干你娘速度爬"
    content.encode('utf-8')
    banword = ["法轮功", "摸鱼", "鱼", "死了"]
    myre = MyRegex("words.txt")
    myre.make_regex()
    bd = BanWordDict("org.txt")
    bd.make_word(myre.regex_dict)




