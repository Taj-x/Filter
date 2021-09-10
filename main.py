#-*- conding:utf-8 -*-
from pypinyin import lazy_pinyin
from pypinyin import Style
import itertools
import time

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
        tmp = "".join(_)
        res.append(tmp)
    return res



class node(object):
    def __init__(self):
        self.next = {} # 指向下一层节点
        self.fail = None # 失配指针
        self.isWord = False # 是否为一个模式串
        self.word = "" #存储模式串

class ac_automation(object):
    def __init__(self) :
        self.root = node()

    def add_word(self, word):
        now = self.root
        for char in word:
            if char not in now.next: 
                now.next[char] = node()
            now = now.next[char]
        now.isWord = True
        now.word = word

    def make_faile(slef): #构建fail指针
        que = []
        que.append(self.root)
        while len(que) != 0:
            temp = que.pop(0)
            p = None
            for key, value in temp.next.item():
                if temp == self.root:
                    temp.next[key].fail = self.root
                else :
                    p = temp.fail
                    while p is not None:
                        if key in p.next : 
                            temp.next[key].fail = p.fail
                            break
                        p = p.fail
                    if p is None:
                        temp.next[key].fail = self.root
                que.append(temp.next[key])

    def search(self, content):
        p = self.root
        result = set()
        index = 0
        while index < len(content) - 1:
            currentposition = index
            while currentposition < len(content):
                word = content[currentposition]
                while word in p.next == False and p != self.root:
                    p = p.fail

                if word in p.next:
                    p = p.next[word]
                else:
                    p = self.root

                if p.isWord:
                    end_index = currentposition + 1
                    result.add((p.word, end_index - len(p.word), end_index))
                    break
                currentposition += 1

            p = self.root
            index += 1
        return result


if __name__ == "__main__":
    ac = ac_automation()
    banword = ["法轮功", "邪教"]
    ac.add_word("日你妈")
    content = "我日你氵妈日你sss是妈的1122啊啊实33打实的日你妈"
    content.encode('utf-8')
    res = []
    for words in banword:
        a1 = []
        for word in words:
            a2 = []
            if iszh(word):
                a2.append(word_to_pinyin(word))
                a2.append(word_to_pinyin_first(word))
            else:
                a2.append(word)
            a1.append(a2)
        res.append(a1)
    
    for _ in res:
        for item in itertools.product(*_):
            ans = ""
            for pp in item:
                ans += pp
    
    print(get_product("你妈的"))




