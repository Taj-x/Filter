#-*- conding:utf-8 -*-
from pypinyin import lazy_pinyin
from pypinyin import Style
import itertools
import time
import sys
import re
from pychai import Erbi
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
            #res.append([strat_index, end_index])
            res.append(original_value)
        return res

#拆字
class MyChai(object):
    def __init__(self):
        self.xiaoqing = Erbi('xiaoqing')
    def run(self):
        self.xiaoqing.run()
        for nameChar in self.xiaoqing.charList:
            if nameChar in self.xiaoqing.component:
                # 如果字是基本部件，则获取字根拆分
                root, strokeList = self.xiaoqing.component[nameChar]
                scheme = [root] + strokeList[-1:] * 4
            else:
                # 否则先按嵌套拆分拆开对于拆出的每个基础字，索引出其用户字根拆分列，最后组合起来
                tree = self.xiaoqing.tree[nameChar]
                first = tree.first
                second = tree.second
                if second.divisible():
                    r1, sl1 = self.xiaoqing.component[first.veryFirst()]
                    r2, sl2 = self.xiaoqing.component[second.first.veryFirst()]
                    r3, sl3 = self.xiaoqing.component[second.second.veryFirst()]
                    scheme = [r1] + [sl2[0], sl2[-1], sl3[0], sl3[-1]]
                elif first.divisible():
                    r1, sl1 = self.xiaoqing.component[first.first.veryFirst()]
                    r2, sl2 = self.xiaoqing.component[first.second.veryFirst()]
                    r3, sl3 = self.xiaoqing.component[second.veryFirst()]
                    scheme = [r1] + [sl2[0], sl2[-1], sl3[0], sl3[-1]]
                else:
                    r1, sl1 = self.xiaoqing.component[first.name]
                    r2, sl2 = self.xiaoqing.component[second.name]
                    scheme = ([r1] + sl2[:3] + sl2[-1:] * 3)[:5]
            code = ''.join(self.xiaoqing.rootSet[root] for root in scheme)
            self.xiaoqing.encoder[nameChar] = code

class MyRegex(object):
    def __init__(self, file_name):
        self.file_name = file_name
        self.regex_dict = {} #敏感词正则表达式

    def make_regex(self):
        mychai = MyChai()
        mychai.run()
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
                        if char in mychai.xiaoqing.tree.keys():
                            zi = mychai.xiaoqing.tree[char]
                            if len(zi.first.name) >= 1 and len(zi.second.name) >= 1:
                                pattern += "(?:{}|{}|{}|{}{})".format(char, word_to_pinyin(char), word_to_pinyin_first(char), zi.first.name[0], zi.second.name[0])
                            else:
                                pattern += "(?:{}|{}|{})".format(char, word_to_pinyin(char), word_to_pinyin_first(char))
                        else:
                            pattern += "(?:{}|{}|{})".format(char, word_to_pinyin(char), word_to_pinyin_first(char))
                #print(pattern)
                self.regex_dict[ban_word.strip()] = pattern

class BanWordDict(object):
    def __init__(self, file_name):
        self.file_name = file_name #待匹配文本
        self.new_word = [] #文本中的敏感词
        self.new_to_original = {} #文本到黑名单的映射


    def make_dict(self, regex):
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

def Ioerr(file_name):
    try:
        f = open(file_name, "r")
    except IOError:
        print("没有找到该文件")
        exit(0)
    else:
        f.close()

class Moyu_Banned(object):
    def __init__(self, blacklist_file, matched_file, ans_file) -> object:
        self.blacklist_file = blacklist_file
        self.matched_file = matched_file
        self.ans_file = ans_file

    def run(self):
        Ioerr(self.blacklist_file)
        Ioerr(self.matched_file)
        #对黑名单词语构建正则表达式


        myre = MyRegex(self.blacklist_file)
        myre.make_regex()
        #用正则去匹配文本中的敏感词
        mydict = BanWordDict(self.matched_file)
        mydict.make_dict(myre.regex_dict)

        #用文本中的敏感词构建ac机
        ac = AhocorasickNer(mydict.new_word)
        ac.add_keywords()
        total = 0
        res = []
        with open(self.matched_file, "r", encoding="utf-8") as f:
            for index, line in enumerate(f.readlines()):
                tmp_res = ac.get_match_result(line.strip())
                for it in tmp_res:
                    total += 1
                    res.append("Line{}: <{}> {}\n".format(index + 1, mydict.new_to_original[it], it))
        with open(self.ans_file, "w", encoding="utf-8") as f:
            f.write("Total: {}\n".format(total))
        with open(self.ans_file, "a", encoding="utf-8") as f:
            f.writelines(res)
        #print(res)



if __name__ == "__main__":
    st = time.time()
    if len(sys.argv) == 1:
        words_file = "test_data/words.txt"
        matched_file = "test_data/org.txt"
        ans_file = "test_data/pp.txt"
    elif len(sys.argv) == 4:
        words_file = sys.argv[1]
        matched_file = sys.argv[2]
        ans_file = sys.argv[3]
    else:
        print("命令行错误")
        exit(0)
    fuckse = Moyu_Banned(words_file, matched_file, ans_file)
    fuckse.run()
    ed = time.time()
    print(ed - st)
    exit(0)




