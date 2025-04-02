"""示例文字生成。"""


import random


CHARACTERS = "一丁七万丈三上下不与丐丑专且世丘丙业丛东丝丢两严丧个中丰串临"
CHARACTERS += "丸丹为主丽举乃久么义之乌乍乎乏乐乒乓乔乖乘乙九乞也习乡书买乱"
CHARACTERS += "乳乾了予争事二于亏云互五井亚些亡交亥亦产亩享京亭亮亲人亿什仁"
CHARACTERS += ""

PUNCTUATIONS = "，。！？"


def gen_lorem_sentence(ends_in_period: bool = False) -> str:
    """生成随机中文句子。"""
    sentence_len = random.randint(6, 12)
    chars = random.choices(CHARACTERS, k=sentence_len)
    punct = "。" if ends_in_period else random.choice(PUNCTUATIONS)
    chars.append(punct)
    return "".join(chars)


def gen_lorem_text() -> str:
    """生成随机中文文本。"""
    sentence_num = random.randint(8, 20)
    sentences = [gen_lorem_sentence() for _ in range(sentence_num)]
    sentences.append(gen_lorem_sentence(ends_in_period=True))
    return "".join(sentences)
