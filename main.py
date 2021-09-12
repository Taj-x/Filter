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
        self.regex_dict = {}

    def make_regex(self):
        with open(self.file_name, "r", encoding="utf-8") as f:
            ban_word = f.readline()
            print(ban_word)
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
                        pattern += "[^\\u4e00-\\u9fa5]"
                    pattern += "(?:{}|{}|{})".format(char, word_to_pinyin(char), word_to_pinyin_first(char))
            print(pattern)
            self.regex_dict[ban_word.strip()] = pattern    



if __name__ == "__main__":
    content = "法轮功和鱼一起摸鱼吧，我要死了。。。粗来，，22112，干你娘速度爬"
    content.encode('utf-8')
    banword = ["法轮功", "摸鱼", "鱼", "死了"]
    myre = MyRegex("words.txt")
    myre.make_regex()
    




