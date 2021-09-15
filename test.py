from main import MyChai
from main import MyRegex

def test_Mychai():
    chai = MyChai()
    chai.run()
    word = "你"
    zi = chai.xiaoqing.tree[word]
    assert "亻尔" == zi.first.name[0] + zi.second.name[0]
    word = "淦"
    zi = chai.xiaoqing.tree[word]
    assert "氵金" == zi.first.name[0] + zi.second.name[0]
    word = "粗"
    zi = chai.xiaoqing.tree[word]
    assert "米且" == zi.first.name[0] + zi.second.name[0]

def test_Myregex():
    filename = "test_data/words.txt"
    regx = MyRegex(filename)
    regx.make_regex()
    key = "法轮功"
    assert regx.regex_dict[key] == r"(?:法|fa|f|氵去)[^\u4e00-\u9fa5]*(?:轮|lun|l|车仑)[^\u4e00-\u9fa5]*(?:功|gong|g|工力)"
    key = "fuck"
    assert regx.regex_dict[key] == r"(?:f)[^a-zA-Z]*(?:u)[^a-zA-Z]*(?:c)[^a-zA-Z]*(?:k)"
    key = "邪教"
    assert regx.regex_dict[key] == r"(?:邪|xie|x|牙阝)[^\u4e00-\u9fa5]*(?:教|jiao|j|孝攵)"

if __name__ == "__main__":
    test_Myregex()
    test_Mychai()