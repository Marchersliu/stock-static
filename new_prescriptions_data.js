// ========== 30问新增方剂数据（从豆包文档提取） ==========
const newPrescriptions = {
  "少阴阴虚-手脚心热": {
    source: "后世方", category: "少阴病 · 阴虚内热",
    name: "知柏地黄丸",
    symptoms: "阴虚火旺，虚火上炎。潮热盗汗，口干咽痛，耳鸣遗精，手脚心发热，舌红少苔，脉细数。",
    ingredients: [
      { name: "熟地", unit: "g", base: 24 },
      { name: "山药", unit: "g", base: 12 },
      { name: "山茱萸", unit: "g", base: 12 },
      { name: "茯苓", unit: "g", base: 9 },
      { name: "泽泻", unit: "g", base: 9 },
      { name: "丹皮", unit: "g", base: 9 },
      { name: "知母", unit: "g", base: 6 },
      { name: "黄柏", unit: "g", base: 6 }
    ],
    decoction: "丸剂，口服，一次6-9克，一日2次。",
    note: "滋阴降火。脾虚便溏者慎用。不宜和感冒类药同时服用。服药期间忌食辛辣食物。",
    complexity: 2
  },
  "胃热炽盛-喜冷饮": {
    source: "后世方", category: "阳明病 · 胃热",
    name: "清胃散",
    symptoms: "胃火牙痛，口气热臭，口舌生疮，牙龈肿痛，喜冷饮，舌红苔黄，脉滑数。",
    ingredients: [
      { name: "生地黄", unit: "g", base: 6 },
      { name: "当归身", unit: "g", base: 6 },
      { name: "牡丹皮", unit: "g", base: 9 },
      { name: "黄连", unit: "g", base: 6 },
      { name: "升麻", unit: "g", base: 9 }
    ],
    decoction: "上五味，都作一服，水一盏半，煎至七分，去滓，放冷服之。",
    note: "清胃凉血。脾胃虚寒者忌用。服药期间忌食辛辣食物。",
    complexity: 2
  },
  "气虚阳虚-疲劳乏力": {
    source: "后世方", category: "太阴病 · 气虚",
    name: "四君子汤",
    symptoms: "脾胃气虚。面色萎黄，语声低微，气短乏力，食少便溏，舌淡苔白，脉虚弱。",
    ingredients: [
      { name: "人参", unit: "g", base: 6 },
      { name: "白术", unit: "g", base: 9 },
      { name: "茯苓", unit: "g", base: 9 },
      { name: "炙甘草", unit: "g", base: 6 }
    ],
    decoction: "上四味，以水八升，煮取三升，去滓，温服一升，日三服。",
    note: "益气健脾。阴虚火旺者忌用。服药期间忌食生冷油腻。",
    complexity: 1
  },
  "气虚不固表-自汗": {
    source: "后世方", category: "太阳病 · 表虚",
    name: "玉屏风散",
    symptoms: "表虚自汗。白天不活动也出汗，动则汗更甚，易感风邪，面色㿠白，舌淡苔薄白，脉虚浮。",
    ingredients: [
      { name: "防风", unit: "g", base: 30 },
      { name: "黄芪", unit: "g", base: 60 },
      { name: "白术", unit: "g", base: 60 }
    ],
    decoction: "上为末，每服三钱，水一盏半，加大枣一枚，煎至七分，去滓，食后热服。",
    note: "益气固表止汗。阴虚盗汗者忌用。服药期间忌食生冷油腻。",
    complexity: 2
  },
  "阴虚火旺-盗汗": {
    source: "后世方", category: "少阴病 · 阴虚",
    name: "当归六黄汤",
    symptoms: "阴虚火旺盗汗。发热盗汗，面赤心烦，口干唇燥，大便干结，小便黄赤，舌红苔黄，脉数。",
    ingredients: [
      { name: "当归", unit: "g", base: 6 },
      { name: "生地黄", unit: "g", base: 6 },
      { name: "熟地黄", unit: "g", base: 6 },
      { name: "黄芩", unit: "g", base: 6 },
      { name: "黄连", unit: "g", base: 6 },
      { name: "黄柏", unit: "g", base: 6 },
      { name: "黄芪", unit: "g", base: 12 }
    ],
    decoction: "上六味，锉如麻豆大，每服五钱匕，水二盏，煎至一盏，去滓，食前服。",
    note: "滋阴泻火，固表止汗。脾胃虚寒者忌用。服药期间忌食辛辣食物。",
    complexity: 3
  },
  "上焦湿热-头面多汗": {
    source: "伤寒论", category: "太阳病 · 湿热",
    name: "麻黄连翘赤小豆汤",
    symptoms: "湿热蕴结，身黄发热，无汗或汗出不畅，头面多汗而身体少汗，或兼浮肿，小便不利，舌红苔黄腻。",
    ingredients: [
      { name: "麻黄", unit: "g", base: 6 },
      { name: "连翘", unit: "g", base: 9 },
      { name: "杏仁", unit: "g", base: 9 },
      { name: "赤小豆", unit: "g", base: 30 },
      { name: "大枣", unit: "枚", base: 12 },
      { name: "生梓白皮", unit: "g", base: 9 },
      { name: "生姜", unit: "g", base: 6 },
      { name: "甘草", unit: "g", base: 6 }
    ],
    decoction: "上八味，以水一斗，先煮麻黄再沸，去上沫，内诸药，煮取三升，去滓，分温三服，半日服尽。",
    note: "宣肺利水，清热解毒。阴黄者忌用。服药期间忌食生冷油腻。",
    complexity: 3
  },
  "下焦湿热-下身多汗": {
    source: "后世方", category: "厥阴病 · 湿热",
    name: "龙胆泻肝汤",
    symptoms: "肝胆湿热下注。下身多汗、阴囊潮湿、瘙痒，胁痛口苦，带下黄臭，小便短赤，舌红苔黄腻，脉弦数。",
    ingredients: [
      { name: "龙胆草", unit: "g", base: 6 },
      { name: "黄芩", unit: "g", base: 9 },
      { name: "栀子", unit: "g", base: 9 },
      { name: "泽泻", unit: "g", base: 12 },
      { name: "木通", unit: "g", base: 6 },
      { name: "车前子", unit: "g", base: 9 },
      { name: "当归", unit: "g", base: 3 },
      { name: "生地黄", unit: "g", base: 9 },
      { name: "柴胡", unit: "g", base: 6 },
      { name: "甘草", unit: "g", base: 6 }
    ],
    decoction: "上十味，水煎服，一日一剂，分两次服。",
    note: "清肝胆，利湿热。本方苦寒，易伤脾胃，不宜久服。脾胃虚寒者忌用。孕妇慎用。",
    complexity: 3
  },
  "厥阴头痛-头顶痛": {
    source: "伤寒论", category: "厥阴病 · 头痛",
    name: "吴茱萸汤",
    symptoms: "厥阴头痛，干呕吐涎沫，巅顶痛，手足厥冷，烦躁欲死，舌淡苔白滑，脉细弦。",
    ingredients: [
      { name: "吴茱萸", unit: "g", base: 9 },
      { name: "人参", unit: "g", base: 9 },
      { name: "生姜", unit: "g", base: 18 },
      { name: "大枣", unit: "枚", base: 12 }
    ],
    decoction: "上四味，以水七升，煮取二升，去滓，温服七合，日三服。",
    note: "温中补虚，降逆止呕。胃热呕吐者忌用。服药期间忌食生冷油腻。",
    complexity: 2
  },
  "气血亏虚-头晕": {
    source: "后世方", category: "太阴病 · 气血虚",
    name: "归脾汤",
    symptoms: "心脾两虚。气短乏力，失眠多梦，头晕目眩，食欲不振，面色萎黄，舌淡苔薄白，脉细弱。",
    ingredients: [
      { name: "白术", unit: "g", base: 9 },
      { name: "茯神", unit: "g", base: 9 },
      { name: "黄芪", unit: "g", base: 12 },
      { name: "龙眼肉", unit: "g", base: 12 },
      { name: "酸枣仁", unit: "g", base: 12 },
      { name: "人参", unit: "g", base: 6 },
      { name: "木香", unit: "g", base: 6 },
      { name: "甘草", unit: "g", base: 6 },
      { name: "当归", unit: "g", base: 9 },
      { name: "远志", unit: "g", base: 6 }
    ],
    decoction: "上十味，以水八升，煮取三升，去滓，温服一升，日三服。",
    note: "益气补血，健脾养心。湿热内盛者忌用。服药期间忌食生冷油腻。",
    complexity: 2
  },
  "痰湿中阻-头晕": {
    source: "后世方", category: "太阴病 · 痰湿",
    name: "半夏白术天麻汤",
    symptoms: "风痰上扰，眩晕头痛。胸闷恶心，呕吐痰涎，舌苔白腻，脉弦滑。",
    ingredients: [
      { name: "半夏", unit: "g", base: 9 },
      { name: "天麻", unit: "g", base: 6 },
      { name: "茯苓", unit: "g", base: 6 },
      { name: "橘红", unit: "g", base: 6 },
      { name: "白术", unit: "g", base: 15 },
      { name: "甘草", unit: "g", base: 3 }
    ],
    decoction: "上六味，加生姜一片，大枣二枚，水煎服。",
    note: "化痰熄风，健脾祛湿。阴虚阳亢者忌用。服药期间忌食生冷油腻。",
    complexity: 2
  },
  "风热外感-黄稠涕": {
    source: "温病条辨", category: "卫分证 · 风热",
    name: "银翘散",
    symptoms: "风热感冒。发热头痛，咳嗽口干，咽喉疼痛，鼻塞流黄稠涕，舌红苔薄黄，脉浮数。",
    ingredients: [
      { name: "连翘", unit: "g", base: 9 },
      { name: "银花", unit: "g", base: 9 },
      { name: "苦桔梗", unit: "g", base: 6 },
      { name: "薄荷", unit: "g", base: 6 },
      { name: "竹叶", unit: "g", base: 4 },
      { name: "生甘草", unit: "g", base: 5 },
      { name: "荆芥穗", unit: "g", base: 5 },
      { name: "淡豆豉", unit: "g", base: 5 },
      { name: "牛蒡子", unit: "g", base: 9 }
    ],
    decoction: "上杵为散，每服六钱，鲜芦根汤煎，香气大出，即取服，勿过煮。",
    note: "辛凉解表，清热解毒。风寒感冒者忌用。服药期间忌食生冷油腻。",
    complexity: 2
  },
  "风寒咽痛": {
    source: "伤寒论", category: "少阴病 · 咽痛",
    name: "半夏散及汤",
    symptoms: "风寒咽痛。咽中痛，恶寒，咽部不红或微红，舌淡苔白，脉紧。",
    ingredients: [
      { name: "半夏", unit: "g", base: 9 },
      { name: "桂枝", unit: "g", base: 9 },
      { name: "甘草", unit: "g", base: 9 }
    ],
    decoction: "上三味，各别捣筛已，合治之，白饮和服方寸匕，日三服。若不能散服者，以水一升，煎七沸，内散两方寸匕，更煮三沸，下火令小冷，少少咽之。",
    note: "温阳散寒，化痰利咽。风热咽痛者忌用。服药期间忌食生冷。",
    complexity: 1
  },
  "风热咽痛": {
    source: "伤寒论", category: "少阴病 · 咽痛",
    name: "桔梗汤",
    symptoms: "风热咽痛。咽痛，音哑，咽喉红肿，或咳吐脓痰，舌红苔黄，脉数。",
    ingredients: [
      { name: "桔梗", unit: "g", base: 30 },
      { name: "甘草", unit: "g", base: 60 }
    ],
    decoction: "上二味，以水三升，煮取一升，去滓，温分再服。",
    note: "清热解毒，利咽消肿。风寒咽痛者忌用。服药期间忌食辛辣食物。",
    complexity: 1
  },
  "寒湿内盛-白厚腻": {
    source: "后世方", category: "太阴病 · 寒湿",
    name: "平胃散",
    symptoms: "湿滞脾胃。脘腹胀满，不思饮食，口淡无味，恶心呕吐，舌苔白厚腻，脉缓。",
    ingredients: [
      { name: "苍术", unit: "g", base: 15 },
      { name: "厚朴", unit: "g", base: 9 },
      { name: "陈皮", unit: "g", base: 9 },
      { name: "甘草", unit: "g", base: 6 }
    ],
    decoction: "上四味，为散，每服二钱，水一盏，姜二片，枣二枚，煎至七分，去滓，温服。",
    note: "燥湿运脾，行气和胃。阴虚火旺者忌用。服药期间忌食生冷油腻。",
    complexity: 1
  },
  "湿热内蕴-黄厚腻": {
    source: "后世方", category: "太阴病 · 湿热",
    name: "三仁汤",
    symptoms: "湿温初起。头痛恶寒，身重疼痛，午后身热，胸闷不饥，舌苔黄厚腻，脉弦细而濡。",
    ingredients: [
      { name: "杏仁", unit: "g", base: 15 },
      { name: "飞滑石", unit: "g", base: 18 },
      { name: "白通草", unit: "g", base: 6 },
      { name: "白蔻仁", unit: "g", base: 6 },
      { name: "竹叶", unit: "g", base: 6 },
      { name: "厚朴", unit: "g", base: 6 },
      { name: "生薏苡仁", unit: "g", base: 18 },
      { name: "半夏", unit: "g", base: 15 }
    ],
    decoction: "上八味，以水八升，煮取三升，去滓，每服一升，日三服。",
    note: "宣畅气机，清利湿热。寒湿内盛者忌用。服药期间忌食生冷油腻。",
    complexity: 3
  },
  "脾胃虚弱-胃口差": {
    source: "后世方", category: "太阴病 · 脾虚",
    name: "香砂六君子汤",
    symptoms: "脾胃气虚，痰阻气滞。脘腹胀满，不思饮食，嗳气频频，大便溏薄，舌淡苔白腻，脉虚。",
    ingredients: [
      { name: "人参", unit: "g", base: 6 },
      { name: "白术", unit: "g", base: 9 },
      { name: "茯苓", unit: "g", base: 9 },
      { name: "甘草", unit: "g", base: 6 },
      { name: "陈皮", unit: "g", base: 3 },
      { name: "半夏", unit: "g", base: 6 },
      { name: "木香", unit: "g", base: 2 },
      { name: "砂仁", unit: "g", base: 2 }
    ],
    decoction: "上八味，以水八升，煮取三升，去滓，温服一升，日三服。",
    note: "益气健脾，化痰和胃。湿热内盛者忌用。服药期间忌食生冷油腻。",
    complexity: 2
  },
  "肝胃不和-反酸烧心": {
    source: "后世方", category: "厥阴病 · 肝胃不和",
    name: "左金丸",
    symptoms: "肝火犯胃。脘胁疼痛，口苦嘈杂，呕吐吞酸，嗳气频作，舌红苔黄，脉弦数。",
    ingredients: [
      { name: "黄连", unit: "g", base: 180 },
      { name: "吴茱萸", unit: "g", base: 30 }
    ],
    decoction: "上为末，水丸或丸剂，每服2-3克，温开水送服。",
    note: "泻火，疏肝，和胃，止痛。脾胃虚寒者忌用。服药期间忌食辛辣食物。",
    complexity: 2
  },
  "心阳不足-胸闷心慌": {
    source: "伤寒论", category: "太阳病 · 心阳虚",
    name: "桂枝甘草汤",
    symptoms: "心阳不足。心悸，烦躁不安，胸闷气短，叉手自冒心，舌淡苔白，脉虚弱或结代。",
    ingredients: [
      { name: "桂枝", unit: "g", base: 12 },
      { name: "甘草", unit: "g", base: 6 }
    ],
    decoction: "上二味，以水三升，煮取一升，去滓，顿服。",
    note: "温通心阳。阴虚火旺者忌用。服药期间忌食生冷。",
    complexity: 1
  },
  "肝郁气滞-两胁胀痛": {
    source: "后世方", category: "厥阴病 · 肝郁",
    name: "逍遥散",
    symptoms: "肝郁血虚。两胁作痛，头痛目眩，口燥咽干，神疲食少，月经不调，乳房胀痛，舌淡红，脉弦虚。",
    ingredients: [
      { name: "柴胡", unit: "g", base: 9 },
      { name: "当归", unit: "g", base: 9 },
      { name: "白芍", unit: "g", base: 9 },
      { name: "白术", unit: "g", base: 9 },
      { name: "茯苓", unit: "g", base: 9 },
      { name: "炙甘草", unit: "g", base: 4.5 }
    ],
    decoction: "上为粗末，每服二钱，水一大盏，烧生姜一块切破，薄荷少许，同煎至七分，去滓热服。",
    note: "疏肝解郁，健脾和营。阴虚火旺者忌用。服药期间保持心情舒畅。",
    complexity: 2
  },
  "脾虚湿盛-便溏": {
    source: "后世方", category: "太阴病 · 脾虚湿盛",
    name: "参苓白术散",
    symptoms: "脾胃虚弱，食少便溏。四肢乏力，形体消瘦，面色萎黄，胸脘痞闷，舌淡苔白腻，脉虚缓。",
    ingredients: [
      { name: "莲子肉", unit: "g", base: 500 },
      { name: "薏苡仁", unit: "g", base: 500 },
      { name: "缩砂仁", unit: "g", base: 500 },
      { name: "桔梗", unit: "g", base: 500 },
      { name: "白扁豆", unit: "g", base: 750 },
      { name: "白茯苓", unit: "g", base: 1000 },
      { name: "人参", unit: "g", base: 1000 },
      { name: "甘草", unit: "g", base: 1000 },
      { name: "白术", unit: "g", base: 1000 },
      { name: "山药", unit: "g", base: 1000 }
    ],
    decoction: "上为细末，每服二钱，枣汤调下，小儿量岁数加减服之。",
    note: "健脾益气，渗湿止泻。湿热内盛者忌用。服药期间忌食生冷油腻。",
    complexity: 2
  },
  "肠燥便秘-大便干结": {
    source: "伤寒论", category: "阳明病 · 脾约",
    name: "麻子仁丸",
    symptoms: "肠胃燥热，津液不足。大便干结，小便频数，腹胀不适，舌红苔黄燥，脉细涩。",
    ingredients: [
      { name: "麻子仁", unit: "g", base: 500 },
      { name: "芍药", unit: "g", base: 250 },
      { name: "枳实", unit: "g", base: 250 },
      { name: "大黄", unit: "g", base: 500 },
      { name: "厚朴", unit: "g", base: 250 },
      { name: "杏仁", unit: "g", base: 250 }
    ],
    decoction: "上六味，蜜和丸，如梧桐子大，饮服十丸，日三服，渐加，以知为度。",
    note: "润肠泄热，行气通便。脾虚便溏者忌用。服药期间忌食辛辣食物。",
    complexity: 2
  },
  "湿热下注-大便粘": {
    source: "伤寒论", category: "阳明病 · 协热下利",
    name: "葛根芩连汤",
    symptoms: "协热下利。身热下利，胸脘烦热，大便粘滞不爽，肛门灼热，舌红苔黄腻，脉数。",
    ingredients: [
      { name: "葛根", unit: "g", base: 15 },
      { name: "黄芩", unit: "g", base: 9 },
      { name: "黄连", unit: "g", base: 9 },
      { name: "甘草", unit: "g", base: 6 }
    ],
    decoction: "上四味，以水八升，先煮葛根，减二升，内诸药，煮取二升，去滓，分温再服。",
    note: "解表清里。虚寒下利者忌用。服药期间忌食生冷油腻。",
    complexity: 2
  },
  "膀胱湿热-小便黄赤": {
    source: "后世方", category: "太阳病 · 淋证",
    name: "八正散",
    symptoms: "湿热淋证。尿频尿急，溺时涩痛，小便黄赤混浊，小腹急满，口燥咽干，舌红苔黄腻，脉滑数。",
    ingredients: [
      { name: "车前子", unit: "g", base: 500 },
      { name: "瞿麦", unit: "g", base: 500 },
      { name: "萹蓄", unit: "g", base: 500 },
      { name: "滑石", unit: "g", base: 500 },
      { name: "山栀子仁", unit: "g", base: 500 },
      { name: "甘草", unit: "g", base: 500 },
      { name: "木通", unit: "g", base: 500 },
      { name: "大黄", unit: "g", base: 500 }
    ],
    decoction: "上为散，每服二钱，水一盏，入灯心，煎至七分，去滓，温服，食后临卧。",
    note: "清热泻火，利水通淋。虚寒淋证者忌用。服药期间忌食辛辣食物。",
    complexity: 3
  },
  "脾肾阳虚-五更泻": {
    source: "后世方", category: "少阴病 · 五更泻",
    name: "四神丸",
    symptoms: "脾肾阳虚，命门火衰。五更泄泻，不思饮食，食不消化，或久泻不止，腰酸肢冷，舌淡苔白，脉沉迟无力。",
    ingredients: [
      { name: "肉豆蔻", unit: "g", base: 60 },
      { name: "补骨脂", unit: "g", base: 120 },
      { name: "五味子", unit: "g", base: 60 },
      { name: "吴茱萸", unit: "g", base: 30 }
    ],
    decoction: "上为末，用水一碗，煮生姜15克，大枣50枚，取枣肉为丸，如梧桐子大，每服50丸，空心食前服。",
    note: "温肾暖脾，固肠止泻。湿热泄泻者忌用。服药期间忌食生冷油腻。",
    complexity: 2
  },
  "肾阳虚-腰膝酸软": {
    source: "后世方", category: "少阴病 · 肾阳虚",
    name: "右归丸",
    symptoms: "肾阳不足，命门火衰。腰膝酸冷，畏寒肢冷，阳痿遗精，大便溏薄，小便清长，舌淡苔白，脉沉细。",
    ingredients: [
      { name: "熟地", unit: "g", base: 24 },
      { name: "山药", unit: "g", base: 12 },
      { name: "山茱萸", unit: "g", base: 9 },
      { name: "枸杞", unit: "g", base: 12 },
      { name: "鹿角胶", unit: "g", base: 12 },
      { name: "菟丝子", unit: "g", base: 12 },
      { name: "杜仲", unit: "g", base: 12 },
      { name: "当归", unit: "g", base: 9 },
      { name: "肉桂", unit: "g", base: 6 },
      { name: "制附子", unit: "g", base: 6 }
    ],
    decoction: "上为细末，先将熟地蒸烂杵膏，加炼蜜为丸，如梧桐子大，每服百余丸，食前用滚汤或淡盐汤送下。",
    note: "温补肾阳，填精补血。阴虚火旺者忌用。服药期间忌食生冷油腻。",
    complexity: 2
  },
  "气血不足-颈腰椎僵硬": {
    source: "金匮要略", category: "血痹 · 气血不足",
    name: "黄芪桂枝五物汤",
    symptoms: "血痹。肌肤麻木不仁，颈椎腰椎僵硬，肢体麻木，脉微涩而紧。",
    ingredients: [
      { name: "黄芪", unit: "g", base: 9 },
      { name: "芍药", unit: "g", base: 9 },
      { name: "桂枝", unit: "g", base: 9 },
      { name: "生姜", unit: "g", base: 18 },
      { name: "大枣", unit: "枚", base: 12 }
    ],
    decoction: "上五味，以水六升，煮取二升，温服七合，日三服。",
    note: "益气温经，和血通痹。湿热痹阻者忌用。服药期间避风保暖。",
    complexity: 2
  },
  "肝郁化火-情绪焦虑": {
    source: "后世方", category: "厥阴病 · 肝郁化火",
    name: "丹栀逍遥散",
    symptoms: "肝郁化火。烦躁易怒，颊赤口干，头痛目赤，胸胁胀痛，月经不调，舌红苔黄，脉弦数。",
    ingredients: [
      { name: "柴胡", unit: "g", base: 60 },
      { name: "当归", unit: "g", base: 60 },
      { name: "白芍", unit: "g", base: 60 },
      { name: "白术", unit: "g", base: 60 },
      { name: "茯苓", unit: "g", base: 60 },
      { name: "甘草", unit: "g", base: 30 },
      { name: "牡丹皮", unit: "g", base: 45 },
      { name: "山栀", unit: "g", base: 45 }
    ],
    decoction: "上为末，每服二钱，水一盏，煎至七分，空腹热服。",
    note: "疏肝解郁，清热调经。脾胃虚寒者忌用。服药期间保持心情舒畅。",
    complexity: 2
  }
};

module.exports = { newPrescriptions };
