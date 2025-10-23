#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : MeUtils.
# @File         : __init__.py
# @Time         : 2022/5/12 下午2:02
# @Author       : yuanjie
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  :


from meutils.pipe import *
from meutils.str_utils.regular_expression import parse_url, parse_command_string, parse_base64
from meutils.request_utils.crawler import Crawler
from urllib.parse import urlencode, parse_qs, parse_qsl, quote_plus, unquote_plus, urljoin

query_params2json = lambda q: dict(parse_qsl(q))


def parse_prompt(prompt, only_first_url: bool = True):
    if not only_first_url and (urls := parse_url(prompt)):
        prompt = reduce(lambda prompt, url: prompt.replace(url, " "), urls)
        return urls, prompt

    if prompt.startswith('http') and (prompts := prompt.split(maxsplit=1)):  # 单 url
        if len(prompts) == 2:
            return prompts
        else:
            return prompts + [' ']

    elif "http" in prompt and (urls := parse_url(prompt)):
        return urls[0], prompt.replace(urls[0], "")

    else:
        return None, prompt


def json2query_params(js: dict = None, url='') -> str:
    js = js or {}
    js = {k: v for k, v in js.items() if v}
    query_params = unquote_plus(urlencode(js))
    if query_params and url:
        url = f'{url}?{query_params}'
    return url


def remove_punctuation(sentence: str, punctuation='!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'):
    dic = str.maketrans('', '', punctuation)
    return sentence.translate(dic)


def chinese_convert(s, config='t2s'):
    """https://github.com/BYVoid/OpenCC
    pip install opencc
    pip install opencc-python-reimplemented

    s2t.json Simplified Chinese to Traditional Chinese 簡體到繁體
    t2s.json Traditional Chinese to Simplified Chinese 繁體到簡體
    s2tw.json Simplified Chinese to Traditional Chinese (Taiwan Standard) 簡體到臺灣正體
    tw2s.json Traditional Chinese (Taiwan Standard) to Simplified Chinese 臺灣正體到簡體
    s2hk.json Simplified Chinese to Traditional Chinese (Hong Kong variant) 簡體到香港繁體
    hk2s.json Traditional Chinese (Hong Kong variant) to Simplified Chinese 香港繁體到簡體
    s2twp.json Simplified Chinese to Traditional Chinese (Taiwan Standard) with Taiwanese idiom 簡體到繁體（臺灣正體標準）並轉換爲臺灣常用詞彙
    tw2sp.json Traditional Chinese (Taiwan Standard) to Simplified Chinese with Mainland Chinese idiom 繁體（臺灣正體標準）到簡體並轉換爲中國大陸常用詞彙
    t2tw.json Traditional Chinese (OpenCC Standard) to Taiwan Standard 繁體（OpenCC 標準）到臺灣正體
    hk2t.json Traditional Chinese (Hong Kong variant) to Traditional Chinese 香港繁體到繁體（OpenCC 標準）
    t2hk.json Traditional Chinese (OpenCC Standard) to Hong Kong variant 繁體（OpenCC 標準）到香港繁體
    t2jp.json Traditional Chinese Characters (Kyūjitai) to New Japanese Kanji (Shinjitai) 繁體（OpenCC 標準，舊字體）到日文新字體
    jp2t.json New Japanese Kanji (Shinjitai) to Traditional Chinese Characters (Kyūjitai) 日文新字體到繁體（OpenCC 標準，舊字體）
    tw2t.json Traditional Chinese (Taiwan standard) to Traditional Chinese 臺灣正體到繁體（OpenCC 標準）
    @return:
    """
    opencc = try_import("opencc", pip_name="opencc-python-reimplemented")
    converter = opencc.OpenCC(config)
    return converter.convert(s)


def sentence_cut(sentence, pattern='[，。！?\n]'):
    """'([，。！?\n])'可保留分隔符"""
    regexp = re.compile(pattern)

    return regexp.split(sentence.strip().strip('。').strip('！'))


def text2sentence(text):
    """断句
    https://github.com/blmoistawinde/HarvestText
    """
    _ = re.sub('([。！？\?])([^”’])', r"\1\n\2", text.strip())  # 单字符断句符
    _ = re.sub('(\.{6})([^”’])', r"\1\n\2", _)  # 英文省略号
    _ = re.sub('(\…{2})([^”’])', r"\1\n\2", _)  # 中文省略号
    _ = re.sub('([。！？\?][”’])([^，。！？\?])', r'\1\n\2', _)
    # 如果双引号前有终止符，那么双引号才是句子的终点，把分句符\n放到双引号后，注意前面的几句都小心保留了双引号
    # 很多规则中会考虑分号;，但是这里我把它忽略不计，破折号、英文双引号等同样忽略，需要的再做些简单调整即可。
    return _.rstrip().split("\n")


def half2all(ustring):
    """半角转全角"""
    rstring = ""
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code == 32:  # 半角空格直接转化
            inside_code = 12288
        elif 32 <= inside_code <= 126:  # 半角字符（除空格）根据关系转化
            inside_code += 65248
        rstring += chr(inside_code)
    return rstring


def all2half(all_string):
    """全角转半角"""
    from idna import chr

    half_string = ""
    for char in all_string:
        inside_code = ord(char)
        if inside_code == 12288:  # 全角空格直接转换,全角和半角的空格的Unicode值相差12256
            inside_code = 32
        elif (inside_code >= 65281 and inside_code <= 65374):  # 全角字符（除空格）根据关系转化,除空格外的全角和半角的Unicode值相差65248
            inside_code -= 65248

        half_string += unichr(inside_code)
    return half_string


def to_hump(string="a_b c", pattern='_| '):
    """驼峰式转换"""
    reg = re.compile(pattern)
    _ = reg.sub('', string.title())
    return _.replace(_[0], _[0].lower())


def str_replace(s: str, dic: dict):
    """多值替换
        str_replace('abcd', {'a': '8', 'd': '88'})
    """
    return s.translate(str.maketrans(dic))


@lru_cache()
def arabic2chinese(arabic=123):
    c = Crawler(f'https://szjrzzwdxje.bmcx.com/{arabic}__szjrzzwdxje')
    return c.xpath('//span//text()')[-3:-1]


@lru_cache(1024)
def json_loads(s):
    if isinstance(s, bytes):
        s = s.decode()
    try:
        return json.loads(s.replace("'", '"'))

    except Exception as e:
        logger.warning(e)

        return eval(s)


class Encrypt(object):
    """加密"""

    def __init__(self, key=2):
        self.key = key

    def encrypt(self, s):
        b = bytearray(str(s).encode("utf-8"))
        n = len(b)
        c = bytearray(n * 2)
        j = 0
        for i in range(0, n):
            b1 = b[i]
            b2 = b1 ^ self.key
            c1 = b2 % 19
            c2 = b2 // 19
            c1 = c1 + 46
            c2 = c2 + 46
            c[j] = c1
            c[j + 1] = c2
            j = j + 2
        return c.decode("utf-8")

    def decrypt(self, s):
        c = bytearray(str(s).encode("utf-8"))
        n = len(c)
        if n % 2 != 0:
            return ""
        n = n // 2
        b = bytearray(n)
        j = 0
        for i in range(0, n):
            c1 = c[j]
            c2 = c[j + 1]
            j = j + 2
            c1 = c1 - 46
            c2 = c2 - 46
            b2 = c2 * 19 + c1
            b1 = b2 ^ self.key
            b[i] = b1
        return b.decode("utf-8")


def unicode_normalize(s):
    import unicodedata
    return unicodedata.normalize('NFKC', s)


def validate_url(url):
    if isinstance(url, list):
        return all(map(validate_url, url))

    # 首先检查 URL 格式
    try:
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            return False  # , "URL 格式无效"

        # 检查格式是否符合标准
        if not re.match(r'^https?://', url):
            return False  # , "URL 必须以 http:// 或 https:// 开头"
    except Exception:

        logger.error("URL 解析错误")
        return False

    # 然后检查可访问性（可选）
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # response = requests.head(url, timeout=5, allow_redirects=False, headers=headers)
        response = requests.head(url, timeout=5, headers=headers)
        if response.status_code >= 400:
            logger.error(f"URL 返回错误状态码: {response.status_code}")

            return False

        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"连接错误: {str(e)}")

        return False

def parse_slice(slice_str):
    content = slice_str.strip()[1:-1]
    parts = content.split(':', 2)
    parts += [''] * (3 - len(parts))  # 确保有3部分
    return slice(
        int(parts[0]) if parts[0] else None,
        int(parts[1]) if parts[1] else None,
        int(parts[2]) if parts[2] else None
    )


if __name__ == '__main__':
    # print(str_replace('abcd', {'a': '8', 'd': '88'}))
    # print(unquote())
    # print(arabic2chinese())
    # print(to_hump())
    # print(translater())

    # print(json_loads("{1: 1}"))

    # print(Encrypt().encrypt('123' * 100))

    # print(query_params2json("act=get&uid=134597&vkey=07A1D82FDDE1E96DB5CEF4EF12C8125F&num=1&time=30&plat=1&re=1&type=0&so=1&ow=1&spl=1&addr=&db=1"))

    # print(half2all('⽉月'))
    # print(all2half('⽉月'))

    print(parse_prompt(" hi", only_first_url=False))

    print(parse_prompt("https://www.hao123.com/ hi"))
    print(parse_prompt("https://www.hao123.com/ hi" * 2))
    print(parse_prompt("hi https://www.hao123.com/ "))

    print(parse_prompt("https://www.hao123.com/ hi" * 2, only_first_url=False))

    # import chardet
    #
    # def detect_encoding(byte_content):
    #     result = chardet.detect(byte_content)
    #     return result['encoding']

    url = 'https://fal.ai/models/fal-ai/flux-pro/kontext/requests/de5f28be-2ca8-4bd4-8c42-c7fc32969801?output=0'
    url = "https://5b0988e595225.cdn.sohucs.com/images/20190814/5ebb727f502545718c4a06f199cd848b.jpeg"
    # url = "https://filesystem.site/cdn/20250609/1XPdqIyhHiOJ8SC68W4ZQGBrf7XRZD.png"

    # url = "https://filesystem.site/cdn/20250609/1QUKzDHRQedraO15CXnUc22aBjvqEN.png"

    # url = "https://photog.art/api/oss/R2yh8N"

    url = "https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/1fe07cca46224208bfbed8c0f3c50ed8.png~tplv-mdko3gqilj-image.image?rk3s=81d4c505&x-expires=1780112531&x-signature=e7q1NOMjqCHvMz%2FC3dVAEVisAh4%3D&x-wf-file_name=9748f6214970f744fe7fd7a3699cfa2.png"

    # print(validate_url([url] * 3))
    print(validate_url(url))

    print(re.findall("http", url*2))

    # 示例用法
    slice_str = "[:2]"
    slice_str = ":2]"

    # slice_str="https://xchatllm.feishu.cn/sheets/Bmjtst2f6hfMqFttbhLcdfRJnNf?sheet=Y7HVfo[:2]"
    # https://xchatllm.feishu.cn/sheets/Bmjtst2f6hfMqFttbhLcdfRJnNf?sheet=Y7HVfo%5B%3A2%5D
    slice_obj = parse_slice(slice_str)
    l = list(range(10))
    print(l[slice_obj])  # [0, 1]

