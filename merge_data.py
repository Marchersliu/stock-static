import json
import re

with open('extracted_recipes.json', 'r') as f:
    recipes = json.load(f)

# 定义30问症状到方剂key的映射（新增方剂）
NEW_FORMULAS = {
    "知柏地黄丸": {
        "key": "阴虚火旺-盗汗",
        "category": "阴虚 · 内热",
        "source": "备急千金要方",
        "complexity": 1,
        "symptoms": "阴虚火旺，潮热盗汗，口干咽痛，耳鸣遗精，手脚心发热，舌红少苔，脉细数。",
        "ingredients": [
            {"name": "熟地", "unit": "g", "base": 24},
            {"name": "山药", "unit": "g", "base": 12},
            {"name": "山茱萸", "unit": "g", "base": 12},
            {"name": "茯苓", "unit": "g", "base": 9},
            {"name": "泽泻", "unit": "g", "base": 9},
            {"name": "丹皮", "unit": "g", "base": 9},
            {"name": "知母", "unit": "g", "base": 6},
            {"name": "黄柏", "unit": "g", "base": 6}
        ],
        "decoction": "丸剂，口服，一次6-9克，一日2次。",
        "note": "脾虚便溏者慎用。不宜和感冒类药同时服用。服药期间忌食辛辣食物。"
    },
    "清胃散": {
        "key": "胃热炽盛-牙痛口臭",
        "category": "阳明病 · 胃热",
        "source": "脾胃论",
        "complexity": 1,
        "symptoms": "胃火牙痛，口气热臭，口舌生疮，牙龈肿痛，喜冷饮，舌红苔黄。",
        "ingredients": [
            {"name": "生地黄", "unit": "g", "base": 6},
            {"name": "当归身", "unit": "g", "base": 6},
            {"name": "牡丹皮", "unit": "g", "base": 9},
            {"name": "黄连", "unit": "g", "base": 6},
            {"name": "升麻", "unit": "g", "base": 9}
        ],
        "decoction": "上五味，都作一服，水一盏半，煎至七分，去滓，放冷服之。",
        "note": "本方为苦寒之剂，脾胃虚寒者忌用。服药期间忌食辛辣食物。"
    },
    "四君子汤": {
        "key": "气虚阳虚-乏力",
        "category": "太阴病 · 气虚",
        "source": "太平惠民和剂局方",
        "complexity": 1,
        "symptoms": "脾胃气虚，面色萎黄，气短乏力，食少便溏，舌淡苔白，脉虚数。",
        "ingredients": [
            {"name": "人参", "unit": "g", "base": 6},
            {"name": "白术", "unit": "g", "base": 9},
            {"name": "茯苓", "unit": "g", "base": 9},
            {"name": "炙甘草", "unit": "g", "base": 6}
        ],
        "decoction": "上四味，以水八升，煮取三升，去滓，温服一升，日三服。",
        "note": "本方适用于脾胃气虚证。阴虚火旺者忌用。服药期间忌食生冷油腻。"
    },
    "玉屏风散": {
        "key": "气虚不固表-自汗",
        "category": "太阳病 · 表虚",
        "source": "世医得效方",
        "complexity": 1,
        "symptoms": "表虚自汗，易感风邪，面色苍白，气短乏力，动则汗出更甚。",
        "ingredients": [
            {"name": "防风", "unit": "g", "base": 30},
            {"name": "黄芪", "unit": "g", "base": 60},
            {"name": "白术", "unit": "g", "base": 60}
        ],
        "decoction": "上为末，每服三钱，水一盏半，加大枣一枚，煎至七分，去滓，食后热服。",
        "note": "本方适用于表虚自汗证。阴虚盗汗者忌用。服药期间忌食生冷油腻。"
    },
    "当归六黄汤": {
        "key": "阴虚火旺-盗汗",
        "category": "阴虚 · 内热",
        "source": "兰室秘藏",
        "complexity": 2,
        "symptoms": "阴虚火旺盗汗，发热盗汗，面赤心烦，口干咽燥，舌红少苔，脉细数。",
        "ingredients": [
            {"name": "当归", "unit": "g", "base": 6},
            {"name": "生地黄", "unit": "g", "base": 6},
            {"name": "熟地黄", "unit": "g", "base": 6},
            {"name": "黄芩", "unit": "g", "base": 6},
            {"name": "黄连", "unit": "g", "base": 6},
            {"name": "黄柏", "unit": "g", "base": 6},
            {"name": "黄芪", "unit": "g", "base": 12}
        ],
        "decoction": "上六味，锉如麻豆大，每服五钱匕，水二盏，煎至一盏，去滓，食前服。",
        "note": "本方适用于阴虚火旺证。脾胃虚寒者忌用。服药期间忌食辛辣食物。"
    },
    "麻黄连翘赤小豆汤": {
        "key": "上焦湿热-头面多汗",
        "category": "太阳病 · 湿热",
        "source": "伤寒论",
        "complexity": 3,
        "symptoms": "湿热黄疸，身黄发热，无汗或汗出不畅，头面多汗，身体少汗，苔黄腻。",
        "ingredients": [
            {"name": "麻黄", "unit": "g", "base": 6},
            {"name": "连翘", "unit": "g", "base": 9},
            {"name": "杏仁", "unit": "g", "base": 9},
            {"name": "赤小豆", "unit": "g", "base": 30},
            {"name": "大枣", "unit": "枚", "base": 12},
            {"name": "生梓白皮", "unit": "g", "base": 9},
            {"name": "生姜", "unit": "g", "base": 6},
            {"name": "甘草", "unit": "g", "base": 6}
        ],
        "decoction": "上八味，以水一斗，先煮麻黄再沸，去上沫，内诸药，煮取三升，去滓，分温三服，半日服尽。",
        "note": "本方适用于湿热黄疸证。阴黄者忌用。服药期间忌食生冷油腻。"
    },
    "龙胆泻肝汤": {
        "key": "下焦湿热-阴囊潮湿",
        "category": "厥阴病 · 湿热",
        "source": "医方集解",
        "complexity": 2,
        "symptoms": "肝胆湿热，胁痛口苦，阴囊潮湿，带下黄臭，小便黄赤，舌红苔黄腻。",
        "ingredients": [
            {"name": "龙胆草", "unit": "g", "base": 6},
            {"name": "黄芩", "unit": "g", "base": 9},
            {"name": "栀子", "unit": "g", "base": 9},
            {"name": "泽泻", "unit": "g", "base": 12},
            {"name": "木通", "unit": "g", "base": 6},
            {"name": "车前子", "unit": "g", "base": 9},
            {"name": "当归", "unit": "g", "base": 3},
            {"name": "生地黄", "unit": "g", "base": 9},
            {"name": "柴胡", "unit": "g", "base": 6},
            {"name": "甘草", "unit": "g", "base": 6}
        ],
        "decoction": "上十味，水煎服，一日一剂，分两次服。",
        "note": "本方苦寒，易伤脾胃，不宜久服。脾胃虚寒者忌用。孕妇慎用。"
    },
    "吴茱萸汤": {
        "key": "厥阴头痛-头顶痛",
        "category": "厥阴病 · 寒厥",
        "source": "伤寒论",
        "complexity": 2,
        "symptoms": "厥阴头痛，干呕吐涎沫，巅顶痛，手足厥冷，脉细欲绝，胃寒呕吐。",
        "ingredients": [
            {"name": "吴茱萸", "unit": "g", "base": 9},
            {"name": "人参", "unit": "g", "base": 9},
            {"name": "生姜", "unit": "g", "base": 18},
            {"name": "大枣", "unit": "枚", "base": 12}
        ],
        "decoction": "上四味，以水七升，煮取二升，去滓，温服七合，日三服。",
        "note": "本方适用于肝胃虚寒证。胃热呕吐者忌用。服药期间忌食生冷油腻。"
    },
    "半夏白术天麻汤": {
        "key": "痰湿中阻-头晕",
        "category": "太阴病 · 痰饮",
        "source": "医学心悟",
        "complexity": 2,
        "symptoms": "风痰上扰，眩晕头痛，胸闷恶心，舌苔白腻，脉弦滑。",
        "ingredients": [
            {"name": "半夏", "unit": "g", "base": 9},
            {"name": "天麻", "unit": "g", "base": 6},
            {"name": "茯苓", "unit": "g", "base": 6},
            {"name": "橘红", "unit": "g", "base": 6},
            {"name": "白术", "unit": "g", "base": 15},
            {"name": "甘草", "unit": "g", "base": 3}
        ],
        "decoction": "上六味，加生姜一片，大枣二枚，水煎服。",
        "note": "本方适用于风痰上扰证。阴虚阳亢者忌用。服药期间忌食生冷油腻。"
    },
    "归脾汤": {
        "key": "气血亏虚-头晕",
        "category": "太阴病 · 气血虚",
        "source": "济生方",
        "complexity": 2,
        "symptoms": "心脾两虚，气短乏力，失眠多梦，头晕目眩，食欲不振，面色萎黄，舌淡苔白。",
        "ingredients": [
            {"name": "白术", "unit": "g", "base": 9},
            {"name": "茯神", "unit": "g", "base": 9},
            {"name": "黄芪", "unit": "g", "base": 12},
            {"name": "龙眼肉", "unit": "g", "base": 12},
            {"name": "酸枣仁", "unit": "g", "base": 12},
            {"name": "人参", "unit": "g", "base": 6},
            {"name": "木香", "unit": "g", "base": 6},
            {"name": "甘草", "unit": "g", "base": 6},
            {"name": "当归", "unit": "g", "base": 9},
            {"name": "远志", "unit": "g", "base": 6}
        ],
        "decoction": "上十味，以水八升，煮取三升，去滓，温服一升，日三服。",
        "note": "本方适用于心脾两虚证。湿热内盛者忌用。服药期间忌食生冷油腻。"
    },
    "银翘散": {
        "key": "风热外感-黄涕",
        "category": "太阳病 · 风热",
        "source": "温病条辨",
        "complexity": 1,
        "symptoms": "风热感冒，发热头痛，咳嗽口干，咽喉疼痛，鼻塞流黄稠涕，舌红苔黄。",
        "ingredients": [
            {"name": "连翘", "unit": "g", "base": 9},
            {"name": "银花", "unit": "g", "base": 9},
            {"name": "苦桔梗", "unit": "g", "base": 6},
            {"name": "薄荷", "unit": "g", "base": 6},
            {"name": "竹叶", "unit": "g", "base": 4},
            {"name": "生甘草", "unit": "g", "base": 5},
            {"name": "荆芥穗", "unit": "g", "base": 5},
            {"name": "淡豆豉", "unit": "g", "base": 5},
            {"name": "牛蒡子", "unit": "g", "base": 9}
        ],
        "decoction": "上杵为散，每服六钱，鲜芦根汤煎，香气大出，即取服，勿过煮。",
        "note": "本方适用于风热感冒。风寒感冒者忌用。服药期间忌食生冷油腻。"
    },
    "半夏散及汤": {
        "key": "风寒咽痛-咽中痛",
        "category": "太阳病 · 咽痛",
        "source": "伤寒论",
        "complexity": 1,
        "symptoms": "风寒咽痛，咽中痛，恶寒，舌苔白，无热象。",
        "ingredients": [
            {"name": "半夏", "unit": "g", "base": 9},
            {"name": "桂枝", "unit": "g", "base": 9},
            {"name": "甘草", "unit": "g", "base": 9}
        ],
        "decoction": "上三味，各别捣筛已，合治之，白饮和服方寸匕，日三服。若不能散服者，以水一升，煎七沸，内散两方寸匕，更煮三沸，下火令小冷，少少咽之。",
        "note": "本方适用于风寒咽痛证。风热咽痛者忌用。服药期间忌食生冷。"
    },
    "桔梗汤": {
        "key": "风热咽痛-音哑",
        "category": "太阳病 · 咽痛",
        "source": "伤寒论",
        "complexity": 1,
        "symptoms": "咽痛，音哑，肺痈，咽喉红肿疼痛，舌红苔黄。",
        "ingredients": [
            {"name": "桔梗", "unit": "g", "base": 30},
            {"name": "甘草", "unit": "g", "base": 60}
        ],
        "decoction": "上二味，以水三升，煮取一升，去滓，温分再服。",
        "note": "本方适用于风热咽痛证。风寒咽痛者忌用。服药期间忌食辛辣食物。"
    },
    "平胃散": {
        "key": "寒湿内盛-苔白腻",
        "category": "太阴病 · 湿滞",
        "source": "太平惠民和剂局方",
        "complexity": 1,
        "symptoms": "湿滞脾胃，脘腹胀满，不思饮食，舌苔白厚腻，口淡无味，体倦乏力。",
        "ingredients": [
            {"name": "苍术", "unit": "g", "base": 15},
            {"name": "厚朴", "unit": "g", "base": 9},
            {"name": "陈皮", "unit": "g", "base": 9},
            {"name": "甘草", "unit": "g", "base": 6}
        ],
        "decoction": "上四味，为散，每服二钱，水一盏，姜二片，枣二枚，煎至七分，去滓，温服。",
        "note": "本方适用于湿滞脾胃证。阴虚火旺者忌用。服药期间忌食生冷油腻。"
    },
    "三仁汤": {
        "key": "湿热内蕴-苔黄腻",
        "category": "太阴病 · 湿热",
        "source": "温病条辨",
        "complexity": 2,
        "symptoms": "湿温初起，头痛恶寒，身重疼痛，舌苔黄厚腻，胸闷不饥，午后身热。",
        "ingredients": [
            {"name": "杏仁", "unit": "g", "base": 15},
            {"name": "飞滑石", "unit": "g", "base": 18},
            {"name": "白通草", "unit": "g", "base": 6},
            {"name": "白蔻仁", "unit": "g", "base": 6},
            {"name": "竹叶", "unit": "g", "base": 6},
            {"name": "厚朴", "unit": "g", "base": 6},
            {"name": "生薏苡仁", "unit": "g", "base": 18},
            {"name": "半夏", "unit": "g", "base": 15}
        ],
        "decoction": "上八味，以水八升，煮取三升，去滓，每服一升，日三服。",
        "note": "本方适用于湿温初起证。寒湿内盛者忌用。服药期间忌食生冷油腻。"
    },
    "香砂六君子汤": {
        "key": "脾胃虚弱-腹胀",
        "category": "太阴病 · 脾虚",
        "source": "古今名医方论",
        "complexity": 2,
        "symptoms": "脾胃气虚，痰阻气滞，脘腹胀满，食少便溏，呕吐嗳气，舌淡苔白。",
        "ingredients": [
            {"name": "人参", "unit": "g", "base": 6},
            {"name": "白术", "unit": "g", "base": 9},
            {"name": "茯苓", "unit": "g", "base": 9},
            {"name": "甘草", "unit": "g", "base": 6},
            {"name": "陈皮", "unit": "g", "base": 3},
            {"name": "半夏", "unit": "g", "base": 6},
            {"name": "木香", "unit": "g", "base": 2},
            {"name": "砂仁", "unit": "g", "base": 2}
        ],
        "decoction": "上八味，以水八升，煮取三升，去滓，温服一升，日三服。",
        "note": "本方适用于脾胃气虚证。湿热内盛者忌用。服药期间忌食生冷油腻。"
    },
    "左金丸": {
        "key": "肝胃不和-反酸",
        "category": "厥阴病 · 肝胃",
        "source": "丹溪心法",
        "complexity": 1,
        "symptoms": "肝火犯胃，胁肋胀痛，呕吐吞酸，嗳气口干，胃胀胃痛，舌红苔黄。",
        "ingredients": [
            {"name": "黄连", "unit": "g", "base": 180},
            {"name": "吴茱萸", "unit": "g", "base": 30}
        ],
        "decoction": "上二味，为末，水泛为丸，或蒸饼为丸。每服3-6g，温开水送服。",
        "note": "本方适用于肝火犯胃证。脾胃虚寒者忌用。孕妇慎用。"
    },
    "桂枝甘草汤": {
        "key": "心阳不足-心悸",
        "category": "太阳病 · 心阳虚",
        "source": "伤寒论",
        "complexity": 1,
        "symptoms": "心阳不足，心悸怔忡，胸闷气短，脉弱或结代，面色㿠白，畏寒肢冷。",
        "ingredients": [
            {"name": "桂枝", "unit": "g", "base": 12},
            {"name": "甘草", "unit": "g", "base": 6}
        ],
        "decoction": "上二味，以水三升，煮取一升，去滓，顿服。",
        "note": "本方适用于心阳不足证。阴虚火旺者忌用。"
    },
    "逍遥散": {
        "key": "肝郁气滞-胁痛",
        "category": "厥阴病 · 肝郁",
        "source": "太平惠民和剂局方",
        "complexity": 1,
        "symptoms": "肝郁脾虚，两胁胀痛，头痛目眩，口燥咽干，神疲食少，月经不调，乳房胀痛。",
        "ingredients": [
            {"name": "柴胡", "unit": "g", "base": 9},
            {"name": "当归", "unit": "g", "base": 9},
            {"name": "白芍", "unit": "g", "base": 9},
            {"name": "白术", "unit": "g", "base": 9},
            {"name": "茯苓", "unit": "g", "base": 9},
            {"name": "炙甘草", "unit": "g", "base": 6}
        ],
        "decoction": "上六味，加薄荷少许、生姜三片，水煎服。",
        "note": "本方适用于肝郁脾虚证。肝肾阴虚者慎用。"
    },
    "参苓白术散": {
        "key": "脾虚湿盛-便溏",
        "category": "太阴病 · 脾虚湿盛",
        "source": "太平惠民和剂局方",
        "complexity": 1,
        "symptoms": "脾虚湿盛，大便稀溏不成形，食少便溏，四肢乏力，面色萎黄，舌淡苔白腻。",
        "ingredients": [
            {"name": "人参", "unit": "g", "base": 6},
            {"name": "白术", "unit": "g", "base": 9},
            {"name": "茯苓", "unit": "g", "base": 9},
            {"name": "甘草", "unit": "g", "base": 6},
            {"name": "山药", "unit": "g", "base": 9},
            {"name": "莲子", "unit": "g", "base": 6},
            {"name": "白扁豆", "unit": "g", "base": 9},
            {"name": "薏苡仁", "unit": "g", "base": 9},
            {"name": "砂仁", "unit": "g", "base": 3},
            {"name": "桔梗", "unit": "g", "base": 3}
        ],
        "decoction": "上十味，为细末，每服二钱，枣汤调下。",
        "note": "本方适用于脾虚湿盛证。湿热内盛者忌用。"
    },
    "麻子仁丸": {
        "key": "阳明腑实-便秘",
        "category": "阳明病 · 脾约",
        "source": "伤寒论",
        "complexity": 2,
        "symptoms": "脾约便秘，大便干结，小便数多，腹满胀痛，口干渴，舌红少津。",
        "ingredients": [
            {"name": "麻子仁", "unit": "g", "base": 20},
            {"name": "芍药", "unit": "g", "base": 9},
            {"name": "枳实", "unit": "g", "base": 9},
            {"name": "大黄", "unit": "g", "base": 12},
            {"name": "厚朴", "unit": "g", "base": 9},
            {"name": "杏仁", "unit": "g", "base": 9}
        ],
        "decoction": "上六味，蜜和为丸，如梧桐子大。每服十丸，日三服，渐加，以知为度。",
        "note": "本方适用于脾约便秘证。孕妇慎用。虚寒便秘者忌用。"
    },
    "葛根芩连汤": {
        "key": "湿热下注-便粘",
        "category": "阳明病 · 湿热",
        "source": "伤寒论",
        "complexity": 2,
        "symptoms": "湿热下注，大便粘马桶、排便不尽，身热下利，肛门灼热，舌红苔黄腻。",
        "ingredients": [
            {"name": "葛根", "unit": "g", "base": 15},
            {"name": "黄芩", "unit": "g", "base": 9},
            {"name": "黄连", "unit": "g", "base": 6},
            {"name": "甘草", "unit": "g", "base": 6}
        ],
        "decoction": "上四味，以水八升，先煮葛根减二升，内诸药，煮取二升，去滓，分温再服。",
        "note": "本方适用于湿热下利证。脾胃虚寒者忌用。"
    },
    "八正散": {
        "key": "膀胱湿热-尿赤涩痛",
        "category": "太阳病 · 膀胱湿热",
        "source": "太平惠民和剂局方",
        "complexity": 2,
        "symptoms": "膀胱湿热，小便黄赤涩痛，尿频尿急，尿道灼热，口干苦，舌红苔黄腻。",
        "ingredients": [
            {"name": "车前子", "unit": "g", "base": 9},
            {"name": "瞿麦", "unit": "g", "base": 9},
            {"name": "萹蓄", "unit": "g", "base": 9},
            {"name": "滑石", "unit": "g", "base": 15},
            {"name": "山栀子", "unit": "g", "base": 9},
            {"name": "甘草", "unit": "g", "base": 6},
            {"name": "木通", "unit": "g", "base": 6},
            {"name": "大黄", "unit": "g", "base": 6}
        ],
        "decoction": "上八味，为散，每服二钱，水一盏，入灯心草煎至七分，去滓，温服。",
        "note": "本方适用于膀胱湿热证。孕妇慎用。虚寒者忌用。"
    },
    "四神丸": {
        "key": "脾肾阳虚-五更泻",
        "category": "少阴病 · 脾肾阳虚",
        "source": "证治准绳",
        "complexity": 2,
        "symptoms": "脾肾阳虚，天亮前腹泻（五更泻），腹部冷痛，畏寒肢冷，腰膝酸软，舌淡苔白。",
        "ingredients": [
            {"name": "肉豆蔻", "unit": "g", "base": 9},
            {"name": "补骨脂", "unit": "g", "base": 12},
            {"name": "五味子", "unit": "g", "base": 6},
            {"name": "吴茱萸", "unit": "g", "base": 3}
        ],
        "decoction": "上四味，为末，生姜四两、红枣五十枚同煮，枣熟去姜，取枣肉和药为丸。每服6-9g，空心食前服。",
        "note": "本方适用于脾肾阳虚之五更泻。湿热下利者忌用。"
    },
    "右归丸": {
        "key": "肾阳虚-腰痛",
        "category": "少阴病 · 肾阳虚",
        "source": "景岳全书",
        "complexity": 2,
        "symptoms": "肾阳不足，腰膝酸软，腰痛畏寒，阳痿遗精，畏寒肢冷，小便清长，舌淡苔白。",
        "ingredients": [
            {"name": "熟地", "unit": "g", "base": 24},
            {"name": "山药", "unit": "g", "base": 12},
            {"name": "山茱萸", "unit": "g", "base": 9},
            {"name": "枸杞子", "unit": "g", "base": 9},
            {"name": "菟丝子", "unit": "g", "base": 12},
            {"name": "鹿角胶", "unit": "g", "base": 12},
            {"name": "杜仲", "unit": "g", "base": 12},
            {"name": "当归", "unit": "g", "base": 9},
            {"name": "肉桂", "unit": "g", "base": 6},
            {"name": "附子", "unit": "g", "base": 6}
        ],
        "decoction": "丸剂，口服，一次6-9克，一日2次。",
        "note": "本方适用于肾阳不足证。阴虚火旺者忌用。孕妇慎用附子。"
    },
    "黄芪桂枝五物汤": {
        "key": "气血不足-肢体麻木",
        "category": "太阳病 · 血痹",
        "source": "金匮要略",
        "complexity": 2,
        "symptoms": "血痹，肌肤麻木不仁，颈椎腰椎僵硬，肢体麻木，微恶风寒，舌淡苔白，脉微涩。",
        "ingredients": [
            {"name": "黄芪", "unit": "g", "base": 9},
            {"name": "桂枝", "unit": "g", "base": 9},
            {"name": "芍药", "unit": "g", "base": 9},
            {"name": "生姜", "unit": "g", "base": 18},
            {"name": "大枣", "unit": "枚", "base": 4}
        ],
        "decoction": "上五味，以水六升，煮取二升，温服七合，日三服。",
        "note": "本方适用于血痹证。湿热痹证者慎用。"
    },
    "丹栀逍遥散": {
        "key": "肝郁化火-易怒",
        "category": "厥阴病 · 肝火",
        "source": "内科摘要",
        "complexity": 2,
        "symptoms": "肝郁化火，情绪焦虑，容易发火，两胁胀痛，口苦咽干，目赤耳鸣，舌红苔黄。",
        "ingredients": [
            {"name": "柴胡", "unit": "g", "base": 9},
            {"name": "当归", "unit": "g", "base": 9},
            {"name": "白芍", "unit": "g", "base": 9},
            {"name": "白术", "unit": "g", "base": 9},
            {"name": "茯苓", "unit": "g", "base": 9},
            {"name": "炙甘草", "unit": "g", "base": 6},
            {"name": "丹皮", "unit": "g", "base": 6},
            {"name": "栀子", "unit": "g", "base": 6}
        ],
        "decoction": "上八味，加薄荷少许、生姜三片，水煎服。",
        "note": "本方适用于肝郁化火证。脾胃虚寒者慎用。孕妇慎用。"
    }
}

# 构建 symptomList 新增条目
NEW_SYMPTOMS = []
for name, data in NEW_FORMULAS.items():
    label = f"{data['symptoms'][:20]}...（{data['source']}·{name}）"
    # 使用更简洁的label
    label_map = {
        "知柏地黄丸": "阴虚火旺，潮热盗汗，手脚心热（备急千金要方·知柏地黄丸）",
        "清胃散": "胃火牙痛，口气热臭，喜冷饮（脾胃论·清胃散）",
        "四君子汤": "脾胃气虚，面色萎黄，气短乏力（太平惠民和剂局方·四君子汤）",
        "玉屏风散": "表虚自汗，易感风邪，动则汗甚（世医得效方·玉屏风散）",
        "当归六黄汤": "阴虚火旺盗汗，面赤心烦（兰室秘藏·当归六黄汤）",
        "麻黄连翘赤小豆汤": "湿热黄疸，头面多汗，身黄发热（伤寒论·麻黄连翘赤小豆汤）",
        "龙胆泻肝汤": "肝胆湿热，胁痛口苦，阴囊潮湿（医方集解·龙胆泻肝汤）",
        "吴茱萸汤": "厥阴头痛，干呕吐涎沫，巅顶痛（伤寒论·吴茱萸汤）",
        "半夏白术天麻汤": "风痰上扰，眩晕头痛，胸闷恶心（医学心悟·半夏白术天麻汤）",
        "归脾汤": "心脾两虚，气短乏力，失眠多梦（济生方·归脾汤）",
        "银翘散": "风热感冒，发热头痛，咽喉疼痛（温病条辨·银翘散）",
        "半夏散及汤": "风寒咽痛，咽中痛，恶寒（伤寒论·半夏散及汤）",
        "桔梗汤": "咽痛音哑，咽喉红肿疼痛（伤寒论·桔梗汤）",
        "平胃散": "湿滞脾胃，脘腹胀满，不思饮食（太平惠民和剂局方·平胃散）",
        "三仁汤": "湿温初起，身重疼痛，苔黄腻（温病条辨·三仁汤）",
        "香砂六君子汤": "脾胃气虚，痰阻气滞，脘腹胀满（古今名医方论·香砂六君子汤）",
        "左金丸": "肝火犯胃，呕吐吞酸，胁肋胀痛（丹溪心法·左金丸）",
        "桂枝甘草汤": "心阳不足，心悸怔忡，胸闷气短（伤寒论·桂枝甘草汤）",
        "逍遥散": "肝郁脾虚，两胁胀痛，月经不调（太平惠民和剂局方·逍遥散）",
        "参苓白术散": "脾虚湿盛，大便稀溏，四肢乏力（太平惠民和剂局方·参苓白术散）",
        "麻子仁丸": "脾约便秘，大便干结，腹满胀痛（伤寒论·麻子仁丸）",
        "葛根芩连汤": "湿热下利，大便粘腻，肛门灼热（伤寒论·葛根芩连汤）",
        "八正散": "膀胱湿热，小便黄赤涩痛，尿频尿急（太平惠民和剂局方·八正散）",
        "四神丸": "脾肾阳虚，五更泻，腹部冷痛（证治准绳·四神丸）",
        "右归丸": "肾阳不足，腰膝酸软，畏寒肢冷（景岳全书·右归丸）",
        "黄芪桂枝五物汤": "血痹肢体麻木，颈椎腰椎僵硬（金匮要略·黄芪桂枝五物汤）",
        "丹栀逍遥散": "肝郁化火，情绪焦虑，口苦咽干（内科摘要·丹栀逍遥散）"
    }
    label = label_map.get(name, f"{data['symptoms'][:30]}（{data['source']}·{name}）")
    NEW_SYMPTOMS.append({"label": label, "key": data["key"]})

# 构建 acupointMapping 新增条目
NEW_ACUPOINTS = {
    "阴虚火旺-盗汗": {
        "effect": "滋阴降火、固表止汗",
        "points": ["太溪", "三阴交", "阴陵泉", "复溜", "神门", "内关"]
    },
    "胃热炽盛-牙痛口臭": {
        "effect": "清胃泻火、凉血止痛",
        "points": ["合谷", "内庭", "颊车", "下关", "劳宫", "曲池"]
    },
    "气虚阳虚-乏力": {
        "effect": "益气健脾、培补元气",
        "points": ["足三里", "关元", "气海", "三阴交", "脾俞", "胃俞"]
    },
    "气虚不固表-自汗": {
        "effect": "益气固表、止汗御邪",
        "points": ["足三里", "合谷", "大椎", "风门", "肺俞", "脾俞"]
    },
    "上焦湿热-头面多汗": {
        "effect": "宣肺利水、清热解毒",
        "points": ["曲池", "合谷", "列缺", "大椎", "肺俞", "风门"]
    },
    "下焦湿热-阴囊潮湿": {
        "effect": "清利肝胆湿热",
        "points": ["太冲", "行间", "阴陵泉", "三阴交", "关元", "中极"]
    },
    "厥阴头痛-头顶痛": {
        "effect": "温肝暖胃、降逆止痛",
        "points": ["百会", "太冲", "行间", "涌泉", "内关", "足三里"]
    },
    "痰湿中阻-头晕": {
        "effect": "化痰熄风、健脾祛湿",
        "points": ["丰隆", "足三里", "中脘", "百会", "风池", "内关"]
    },
    "气血亏虚-头晕": {
        "effect": "益气养血、健脾养心",
        "points": ["足三里", "三阴交", "血海", "百会", "神门", "内关"]
    },
    "风热外感-黄涕": {
        "effect": "辛凉解表、清热解毒",
        "points": ["曲池", "合谷", "大椎", "风池", "外关", "少商"]
    },
    "风寒咽痛-咽中痛": {
        "effect": "温阳散寒、化痰利咽",
        "points": ["列缺", "照海", "天突", "廉泉", "合谷", "风池"]
    },
    "风热咽痛-音哑": {
        "effect": "清热解毒、利咽消肿",
        "points": ["少商", "商阳", "合谷", "曲池", "天突", "廉泉"]
    },
    "寒湿内盛-苔白腻": {
        "effect": "燥湿运脾、行气和胃",
        "points": ["足三里", "中脘", "丰隆", "阴陵泉", "脾俞", "胃俞"]
    },
    "湿热内蕴-苔黄腻": {
        "effect": "宣畅气机、清利湿热",
        "points": ["足三里", "阴陵泉", "三阴交", "曲池", "丰隆", "中脘"]
    },
    "脾胃虚弱-腹胀": {
        "effect": "益气健脾、化痰和胃",
        "points": ["足三里", "中脘", "气海", "脾俞", "胃俞", "公孙"]
    },
    "肝胃不和-反酸": {
        "effect": "泻火疏肝、和胃止痛",
        "points": ["太冲", "行间", "足三里", "中脘", "内关", "公孙"]
    },
    "心阳不足-心悸": {
        "effect": "温通心阳、安神定悸",
        "points": ["内关", "神门", "膻中", "心俞", "厥阴俞", "巨阙"]
    },
    "肝郁气滞-胁痛": {
        "effect": "疏肝解郁、健脾和营",
        "points": ["太冲", "期门", "阳陵泉", "内关", "膻中", "足三里"]
    },
    "脾虚湿盛-便溏": {
        "effect": "健脾益气、渗湿止泻",
        "points": ["足三里", "阴陵泉", "三阴交", "天枢", "中脘", "脾俞"]
    },
    "阳明腑实-便秘": {
        "effect": "润肠通便、滋阴通便",
        "points": ["天枢", "上巨虚", "支沟", "大肠俞", "足三里", "丰隆"]
    },
    "湿热下注-便粘": {
        "effect": "清热利湿、升清止泻",
        "points": ["天枢", "上巨虚", "阴陵泉", "足三里", "曲池", "合谷"]
    },
    "膀胱湿热-尿赤涩痛": {
        "effect": "清热泻火、利水通淋",
        "points": ["中极", "膀胱俞", "三阴交", "阴陵泉", "委阳", "水道"]
    },
    "脾肾阳虚-五更泻": {
        "effect": "温肾暖脾、固肠止泻",
        "points": ["关元", "命门", "肾俞", "脾俞", "足三里", "三阴交"]
    },
    "肾阳虚-腰痛": {
        "effect": "温补肾阳、强健腰膝",
        "points": ["肾俞", "命门", "腰阳关", "委中", "太溪", "关元"]
    },
    "气血不足-肢体麻木": {
        "effect": "益气和营、通痹活络",
        "points": ["足三里", "三阴交", "血海", "合谷", "曲池", "阿是穴"]
    },
    "肝郁化火-易怒": {
        "effect": "疏肝清热、凉血调经",
        "points": ["太冲", "行间", "期门", "阳陵泉", "内关", "膻中"]
    }
}

# 构建 acupointTonification 新增穴位
NEW_TONIFICATIONS = {
    "少商": {"type": "泻", "method": "点刺出血，以清热利咽"},
    "商阳": {"type": "泻", "method": "点刺出血，以清热消肿"},
    "颊车": {"type": "泻", "method": "拇指向后捻转，轻插重提，以清热止痛"},
    "下关": {"type": "泻", "method": "拇指向后捻转，轻插重提，以通络止痛"},
    "行间": {"type": "泻", "method": "拇指向后捻转，轻插重提，以清肝泻火"},
    "腰阳关": {"type": "补", "method": "拇指向前捻转，重插轻提，或灸，以温肾壮阳"},
    "大肠俞": {"type": "泻", "method": "拇指向后捻转，轻插重提，以通腑导滞"},
    "公孙": {"type": "补", "method": "拇指向前捻转，重插轻提，以健脾和胃"}
}

# 保存为JSON
merge_data = {
    "new_formulas": NEW_FORMULAS,
    "new_symptoms": NEW_SYMPTOMS,
    "new_acupoints": NEW_ACUPOINTS,
    "new_tonifications": NEW_TONIFICATIONS
}

with open('merge_data.json', 'w', encoding='utf-8') as f:
    json.dump(merge_data, f, ensure_ascii=False, indent=2)

print(f"新增方剂: {len(NEW_FORMULAS)}")
print(f"新增症状: {len(NEW_SYMPTOMS)}")
print(f"新增针灸: {len(NEW_ACUPOINTS)}")
print(f"新增穴位补泻: {len(NEW_TONIFICATIONS)}")
print("Saved to merge_data.json")
