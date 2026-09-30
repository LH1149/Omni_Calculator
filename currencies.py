# -*- coding: utf-8 -*-
"""
货币数据表 — 全量 ISO 4217 常用货币（中文名称 + 货币代号）。
"""

# (代号, 中文名称)
CURRENCIES = [
    ("CNY", "人民币"),
    ("USD", "美元"),
    ("EUR", "欧元"),
    ("GBP", "英镑"),
    ("JPY", "日元"),
    ("KRW", "韩元"),
    ("HKD", "港币"),
    ("TWD", "新台币"),
    ("SGD", "新加坡元"),
    ("MYR", "马来西亚林吉特"),
    ("THB", "泰铢"),
    ("VND", "越南盾"),
    ("IDR", "印尼盾"),
    ("PHP", "菲律宾比索"),
    ("INR", "印度卢比"),
    ("AUD", "澳大利亚元"),
    ("NZD", "新西兰元"),
    ("CAD", "加拿大元"),
    ("CHF", "瑞士法郎"),
    ("RUB", "俄罗斯卢布"),
    ("BRL", "巴西雷亚尔"),
    ("ZAR", "南非兰特"),
    ("AED", "阿联酋迪拉姆"),
    ("SAR", "沙特里亚尔"),
    ("TRY", "土耳其里拉"),
    ("SEK", "瑞典克朗"),
    ("NOK", "挪威克朗"),
    ("DKK", "丹麦克朗"),
    ("PLN", "波兰兹罗提"),
    ("CZK", "捷克克朗"),
    ("HUF", "匈牙利福林"),
    ("ILS", "以色列新谢克尔"),
    ("MXN", "墨西哥比索"),
    ("RUB", "俄罗斯卢布"),
    ("KZT", "哈萨克斯坦坚戈"),
    ("PKR", "巴基斯坦卢比"),
    ("BDT", "孟加拉塔卡"),
    ("LKR", "斯里兰卡卢比"),
    ("NPR", "尼泊尔卢比"),
    ("MMK", "缅甸缅元"),
    ("KHR", "柬埔寨瑞尔"),
    ("LAK", "老挝基普"),
    ("MNT", "蒙古图格里克"),
    ("JOD", "约旦第纳尔"),
    ("QAR", "卡塔尔里亚尔"),
    ("KWD", "科威特第纳尔"),
    ("BHD", "巴林第纳尔"),
    ("OMR", "阿曼里亚尔"),
    ("EGP", "埃及镑"),
    ("NGN", "尼日利亚奈拉"),
    ("KES", "肯尼亚先令"),
    ("ARS", "阿根廷比索"),
    ("CLP", "智利比索"),
    ("COP", "哥伦比亚比索"),
    ("PEN", "秘鲁索尔"),
    ("UYU", "乌拉圭比索"),
    ("VES", "委内瑞拉玻利瓦尔"),
    ("RON", "罗马尼亚列伊"),
    ("BGN", "保加利亚列弗"),
    ("HRK", "克罗地亚库纳"),
    ("ISK", "冰岛克朗"),
    ("UAH", "乌克兰格里夫纳"),
    ("MDL", "摩尔多瓦列伊"),
    ("RSD", "塞尔维亚第纳尔"),
    ("MKD", "北马其顿第纳尔"),
    ("ALL", "阿尔巴尼亚列克"),
    ("BAM", "波黑可兑换马克"),
    ("GEL", "格鲁吉亚拉里"),
    ("AMD", "亚美尼亚德拉姆"),
    ("AZN", "阿塞拜疆马纳特"),
    ("AFN", "阿富汗尼"),
    ("IQD", "伊拉克第纳尔"),
    ("LBP", "黎巴嫩镑"),
    ("YER", "也门里亚尔"),
    ("TND", "突尼斯第纳尔"),
    ("MAD", "摩洛哥迪拉姆"),
    ("DZD", "阿尔及利亚第纳尔"),
    ("LYD", "利比亚第纳尔"),
    ("SDG", "苏丹镑"),
    ("ETB", "埃塞俄比亚比尔"),
    ("TZS", "坦桑尼亚先令"),
    ("UGX", "乌干达先令"),
    ("GHS", "加纳塞地"),
    ("XOF", "西非法郎"),
    ("XAF", "中非法郎"),
    ("FJD", "斐济元"),
    ("PGK", "巴布亚新几内亚基那"),
    ("WST", "萨摩亚塔拉"),
    ("VUV", "瓦努阿图瓦图"),
    ("TMT", "土库曼斯坦马纳特"),
    ("TJS", "塔吉克斯坦索莫尼"),
    ("UZS", "乌兹别克斯坦苏姆"),
    ("BYN", "白俄罗斯卢布"),
    ("GTQ", "危地马拉格查尔"),
    ("HNL", "洪都拉斯伦皮拉"),
    ("NIO", "尼加拉瓜科多巴"),
    ("DOP", "多米尼加比索"),
    ("HTG", "海地古德"),
    ("JMD", "牙买加元"),
    ("TTD", "特立尼达和多巴哥元"),
    ("BBD", "巴巴多斯元"),
    ("BZD", "伯利兹元"),
    ("XCD", "东加勒比元"),
    ("AWG", "阿鲁巴弗罗林"),
    ("ANG", "荷属安的列斯盾"),
    ("SRD", "苏里南元"),
    ("PYG", "巴拉圭瓜拉尼"),
    ("BOB", "玻利维亚诺"),
    ("CRC", "哥斯达黎加科朗"),
    ("PAB", "巴拿马巴波亚"),
    ("GTQ", "危地马拉格查尔"),
]

# 去重（保持顺序）
_seen = set()
_CURRENCIES_DEDUPED = []
for code, name in CURRENCIES:
    if code not in _seen:
        _seen.add(code)
        _CURRENCIES_DEDUPED.append((code, name))
CURRENCIES = _CURRENCIES_DEDUPED

# 快查字典
_BY_CODE = {code: name for code, name in CURRENCIES}


def get_currency_name(code):
    """根据货币代号返回中文名称，找不到返回代号本身。"""
    return _BY_CODE.get(code, code)


def search_currencies(query):
    """按关键词搜索货币，返回 (代号, 中文名称) 列表。支持中英文模糊匹配。"""
    q = query.strip().lower()
    if not q:
        return list(CURRENCIES)
    results = []
    for code, name in CURRENCIES:
        if q in code.lower() or q in name:
            results.append((code, name))
    return results
