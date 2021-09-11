from datetime import datetime
from pychai import Schema
import sys
import re
from pypinyin import lazy_pinyin as lp


def initChai():
    wubi98 = Schema('wubi98')
    wubi98.run()
    for nameChar in wubi98.charList:
        if nameChar in wubi98.component:
            scheme = wubi98.component[nameChar]
        else:
            tree = wubi98.tree[nameChar]
            componentList = tree.flatten_with_complex(wubi98.complexRootList)
            scheme = sum((wubi98.component[component] for component in componentList), tuple())
        if len(scheme) == 1:
            objectRoot = scheme[0]
            nameRoot = objectRoot.name
            # 单根字中的键名字，击四次该键，等效于取四次该字根
            if nameChar in '王土大木工目日口田山禾白月人金言立水火之已子女又幺':
                info = [nameRoot] * 4
            # 单根字中的单笔画字，取码为双击该键加上两个 L
            elif nameChar in '一丨丿丶乙':
                info = [nameRoot] * 2 + ['田'] * 2
            # 普通字根字，报户口 + 一二末笔
            else:
                firstStroke = objectRoot.strokeList[0].type
                secondStroke = objectRoot.strokeList[1].type
                if objectRoot.charlen == 2:
                    info = [nameRoot, firstStroke, secondStroke]
                else:
                    lastStroke = objectRoot.strokeList[-1].type
                    info = [nameRoot, firstStroke, secondStroke, lastStroke]
        elif len(scheme) < 4:
            if nameChar in wubi98.component or tree.structure not in 'hz':
                weima = '3'
            elif tree.structure == 'h':
                weima = '1'
            elif tree.structure == 'z':
                weima = '2'
            lastObjectRoot = scheme[-1]
            quma = wubi98.category[lastObjectRoot.strokeList[-1].type]
            shibiema = quma + weima
            info = [objectRoot.name for objectRoot in scheme] + [shibiema]
        elif len(scheme) > 4:
            scheme = scheme[:3] + scheme[-1:]
            info = [objectRoot.name for objectRoot in scheme]
        else:
            info = [objectRoot.name for objectRoot in scheme]
        code = ''.join(wubi98.rootSet[nameRoot] for nameRoot in info)
        wubi98.encoder[nameChar] = code
    return wubi98


def createRegex(chai, fileName):
    finalRegex = dict()
    file = open(fileName, encoding="utf-8")
    line = file.readline()
    while line != "":
        forbidden = ""
        first = True
        for word in line:
            if word == '\n' or word.isdigit():
                break
            elif 'a' <= word <= 'z' or 'A' <= word <= 'Z':
                if first:
                    first = False
                else:
                    forbidden += "[^A-Za-z]*"
                forbidden += "(?:" + word + ")"
            elif word in chai.tree.keys():
                if first:
                    first = False
                else:
                    forbidden += "[^\\u4e00-\\u9fa5]*"
                pinyin = lp(word)
                forbidden += "(?:{}{}|{}|{}|{})".format(
                    chai.tree[word].first.name[0], chai.tree[word].second.name[0],
                    pinyin[0], pinyin[0][0], word)
            else:
                if first:
                    first = False
                else:
                    forbidden += "[^\\u4e00-\\u9fa5]*"
                pinyin = lp(word)
                forbidden += "(?:{}|{}|{})".format(pinyin[0], pinyin[0][0], word)
        print(forbidden)
        finalRegex[line.strip()] = forbidden
        line = file.readline()
    return finalRegex


def matchForbidden(regex, fileName):
    file = open(fileName, encoding="utf-8")
    line = file.readline()
    cnt = 1
    total = 0
    ansList = list()
    while line:
        line = line.strip()
        for key in regex.keys():
            fbd = re.findall(regex[key], line, re.I)
            if len(fbd) > 0:
                for o in fbd:
                    ansList.append("Line{}: <{}> {}".format(cnt, key, o))
                    total += 1
            else:
                cw = dict()
                for i in range(len(line)):
                    curPinyin = lp(line[i])[0]
                    keyPinyin = lp(key)
                    if curPinyin in keyPinyin:
                        fb = key[keyPinyin.index(curPinyin)]
                        cw[i]=line[i]
                        if 0 < i < len(line)-1:
                            line = line[:i] + fb + line[i + 1:]
                        elif i == 0:
                            line = fb + line[i + 1:]
                        elif i == len(line)-1:
                            line = line[:i] + fb
                fd = re.findall(regex[key], line, re.I)
                if len(fd) > 0:
                    for o in fd:
                        pos = line.index(o)
                        for p in range(len(o)):
                            if pos+p in cw.keys():
                                o = str(o).replace(o[p], cw[pos+p])
                                ansList.append("Line{}: <{}> {}".format(cnt, key, o))
                                total += 1
        line = file.readline()
        cnt += 1
    return total, ansList


if __name__ == '__main__':
    #forbiddenFileName = sys.argv[1]
    #orgFileName = sys.argv[2]
    #ansFileName = sys.argv[3]
    chai = initChai()
    regex = createRegex(chai, "words.txt")
    total, fbdList = matchForbidden(regex, "org.txt")
    file = open("mo.txt", mode='w')
    file.write("Total: {}\n".format(total))
    for d in fbdList:
        file.write(d + '\n')
    file.close()