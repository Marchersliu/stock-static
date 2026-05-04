const fs = require('fs');

// ========== 新增方剂数据（从 new_prescriptions_data.js 加载） ==========
const { newPrescriptions } = require('./new_prescriptions_data.js');

// ========== 新增 symptomList 条目 ==========
const newSymptomList = [
  { label: "手脚心发热，潮热盗汗，口干咽痛（后世方·知柏地黄丸）", key: "少阴阴虚-手脚心热" },
  { label: "喜冷饮，胃火牙痛，口气热臭（后世方·清胃散）", key: "胃热炽盛-喜冷饮" },
  { label: "常年疲劳乏力，面色萎黄，气短懒言（后世方·四君子汤）", key: "气虚阳虚-疲劳乏力" },
  { label: "白天自汗，动则汗甚，易感冒（后世方·玉屏风散）", key: "气虚不固表-自汗" },
  { label: "夜间盗汗，醒后汗止，面赤心烦（后世方·当归六黄汤）", key: "阴虚火旺-盗汗" },
  { label: "头面多汗，身体少汗，身黄发热（伤寒论·麻黄连翘赤小豆汤）", key: "上焦湿热-头面多汗" },
  { label: "下身多汗，阴囊潮湿，胁痛口苦（后世方·龙胆泻肝汤）", key: "下焦湿热-下身多汗" },
  { label: "头顶痛，干呕吐涎沫，手足厥冷（伤寒论·吴茱萸汤）", key: "厥阴头痛-头顶痛" },
  { label: "头晕目眩，气短乏力，失眠多梦（后世方·归脾汤）", key: "气血亏虚-头晕" },
  { label: "头晕天旋地转，胸闷恶心，呕吐痰涎（后世方·半夏白术天麻汤）", key: "痰湿中阻-头晕" },
  { label: "鼻塞黄稠涕，发热头痛，咽喉疼痛（温病条辨·银翘散）", key: "风热外感-黄稠涕" },
  { label: "咽喉干痛，咽部不红，恶寒（伤寒论·半夏散及汤）", key: "风寒咽痛" },
  { label: "咽喉红肿疼痛，音哑，咳吐脓痰（伤寒论·桔梗汤）", key: "风热咽痛" },
  { label: "舌苔白厚腻，脘腹胀满，不思饮食（后世方·平胃散）", key: "寒湿内盛-白厚腻" },
  { label: "舌苔黄厚腻，午后身热，胸闷不饥（后世方·三仁汤）", key: "湿热内蕴-黄厚腻" },
  { label: "胃口差，食后腹胀，嗳气频频（后世方·香砂六君子汤）", key: "脾胃虚弱-胃口差" },
  { label: "胃胀胃痛，反酸烧心，口苦嘈杂（后世方·左金丸）", key: "肝胃不和-反酸烧心" },
  { label: "胸闷心慌，心悸烦躁，叉手自冒心（伤寒论·桂枝甘草汤）", key: "心阳不足-胸闷心慌" },
  { label: "两胁胀痛，易怒烦躁，头痛目眩（后世方·逍遥散）", key: "肝郁气滞-两胁胀痛" },
  { label: "大便稀溏不成形，四肢乏力，面色萎黄（后世方·参苓白术散）", key: "脾虚湿盛-便溏" },
  { label: "大便干结，小便频数，腹胀不适（伤寒论·麻子仁丸）", key: "肠燥便秘-大便干结" },
  { label: "大便粘马桶，排便不尽，肛门灼热（伤寒论·葛根芩连汤）", key: "湿热下注-大便粘" },
  { label: "小便黄赤涩痛，尿频尿急，小腹急满（后世方·八正散）", key: "膀胱湿热-小便黄赤" },
  { label: "天亮前腹泻，腰酸肢冷，不思饮食（后世方·四神丸）", key: "脾肾阳虚-五更泻" },
  { label: "腰膝酸软，腰痛畏寒，阳痿早泄（后世方·右归丸）", key: "肾阳虚-腰膝酸软" },
  { label: "颈椎腰椎僵硬，肢体麻木，肌肤不仁（金匮要略·黄芪桂枝五物汤）", key: "气血不足-颈腰椎僵硬" },
  { label: "情绪焦虑，容易发火，颊赤口干（后世方·丹栀逍遥散）", key: "肝郁化火-情绪焦虑" }
];

// ========== 新增 acupointMapping 条目 ==========
const newAcupointMapping = {
  "少阴阴虚-手脚心热": {
    effect: "滋阴降火、清热除烦（倪海厦：太溪+涌泉引火归元）",
    points: ["太溪", "涌泉", "三阴交", "内关", "神门"]
  },
  "胃热炽盛-喜冷饮": {
    effect: "清胃泻火、凉血止痛",
    points: ["足三里", "内庭", "合谷", "曲池", "劳宫"]
  },
  "气虚阳虚-疲劳乏力": {
    effect: "益气健脾、培元固本",
    points: ["足三里", "关元", "气海", "脾俞", "胃俞", "百会"]
  },
  "气虚不固表-自汗": {
    effect: "益气固表、调和营卫",
    points: ["足三里", "合谷", "大椎", "肺俞", "脾俞"]
  },
  "阴虚火旺-盗汗": {
    effect: "滋阴降火、固表止汗",
    points: ["太溪", "三阴交", "阴郄", "后溪", "涌泉"]
  },
  "上焦湿热-头面多汗": {
    effect: "宣肺利水、清热化湿",
    points: ["列缺", "合谷", "曲池", "大椎", "肺俞"]
  },
  "下焦湿热-下身多汗": {
    effect: "清利湿热、疏肝理气",
    points: ["阳陵泉", "太冲", "三阴交", "阴陵泉", "中极"]
  },
  "厥阴头痛-头顶痛": {
    effect: "温肝暖胃、降逆止痛（倪海厦：百会+太冲调厥阴）",
    points: ["百会", "太冲", "内关", "足三里", "涌泉"]
  },
  "气血亏虚-头晕": {
    effect: "益气补血、健脾养心",
    points: ["足三里", "三阴交", "百会", "神门", "心俞", "脾俞"]
  },
  "痰湿中阻-头晕": {
    effect: "化痰熄风、健脾祛湿",
    points: ["丰隆", "中脘", "内关", "百会", "足三里"]
  },
  "风热外感-黄稠涕": {
    effect: "疏风清热、宣肺利咽",
    points: ["曲池", "合谷", "大椎", "外关", "少商"]
  },
  "风寒咽痛": {
    effect: "温阳散寒、利咽止痛",
    points: ["天突", "廉泉", "合谷", "列缺", "风池"]
  },
  "风热咽痛": {
    effect: "清热解毒、利咽消肿",
    points: ["少商", "商阳", "合谷", "曲池", "尺泽"]
  },
  "寒湿内盛-白厚腻": {
    effect: "燥湿运脾、温中散寒",
    points: ["足三里", "中脘", "丰隆", "脾俞", "阴陵泉"]
  },
  "湿热内蕴-黄厚腻": {
    effect: "清利湿热、宣畅气机",
    points: ["足三里", "阴陵泉", "曲池", "合谷", "内庭"]
  },
  "脾胃虚弱-胃口差": {
    effect: "益气健脾、和胃消食",
    points: ["足三里", "中脘", "公孙", "脾俞", "胃俞"]
  },
  "肝胃不和-反酸烧心": {
    effect: "疏肝和胃、降逆止呕",
    points: ["足三里", "内关", "太冲", "中脘", "阳陵泉"]
  },
  "心阳不足-胸闷心慌": {
    effect: "温通心阳、宁心安神",
    points: ["内关", "神门", "膻中", "心俞", "巨阙"]
  },
  "肝郁气滞-两胁胀痛": {
    effect: "疏肝解郁、理气止痛",
    points: ["太冲", "阳陵泉", "期门", "膻中", "内关"]
  },
  "脾虚湿盛-便溏": {
    effect: "健脾益气、渗湿止泻",
    points: ["足三里", "天枢", "三阴交", "脾俞", "阴陵泉"]
  },
  "肠燥便秘-大便干结": {
    effect: "润肠通便、行气导滞",
    points: ["天枢", "支沟", "上巨虚", "大肠俞", "足三里"]
  },
  "湿热下注-大便粘": {
    effect: "清热燥湿、升清止泻",
    points: ["天枢", "足三里", "阴陵泉", "合谷", "曲池"]
  },
  "膀胱湿热-小便黄赤": {
    effect: "清热利水、通淋止痛",
    points: ["中极", "膀胱俞", "三阴交", "阴陵泉", "委阳"]
  },
  "脾肾阳虚-五更泻": {
    effect: "温肾暖脾、固肠止泻",
    points: ["关元", "命门", "肾俞", "脾俞", "足三里"]
  },
  "肾阳虚-腰膝酸软": {
    effect: "温补肾阳、强腰健膝",
    points: ["肾俞", "命门", "关元", "太溪", "委中", "腰阳关"]
  },
  "气血不足-颈腰椎僵硬": {
    effect: "益气温经、和血通痹",
    points: ["大椎", "天柱", "后溪", "足三里", "三阴交", "阿是穴"]
  },
  "肝郁化火-情绪焦虑": {
    effect: "疏肝解郁、清热安神",
    points: ["太冲", "行间", "百会", "神门", "内关"]
  }
};

// ========== 新增穴位补泻（acupointTonification 中不存在的穴位） ==========
const newAcupointTonification = {
  "涌泉": { type: "补", method: "拇指向前捻转，重插轻提，或灸，以引火归元、滋阴降火" },
  "阴郄": { type: "补", method: "拇指向前捻转，重插轻提，以养阴清热、固表止汗" },
  "少商": { type: "泻", method: "三棱针点刺出血，以清热利咽、开窍醒神" },
  "商阳": { type: "泻", method: "三棱针点刺出血，以清热消肿、开窍醒神" },
  "腰阳关": { type: "补", method: "拇指向前捻转，重插轻提，或灸，以温肾壮阳、强腰健膝" },
  "行间": { type: "泻", method: "拇指向后捻转，轻插重提，以清肝泻火、疏肝理气" }
};

// ========== 艾灸版新增 moxaMapping 条目 ==========
const newMoxaMapping = {
  "少阴阴虚-手脚心热": {
    effect: "滋阴降火、引火归元（阴虚火旺轻量灸）",
    points: ["涌泉", "太溪", "三阴交"],
    method: "陈日新热敏灸·轻量温和灸：涌泉灸5分钟引火下行，太溪灸10分钟",
    note: "陈日新：阴虚火旺非典型热敏态，灸量宜轻。涌泉为引火归元要穴，灸量控制在5-10分钟",
    source: "陈日新·热敏灸（轻量）",
    technique: "轻量温和灸"
  },
  "胃热炽盛-喜冷饮": {
    effect: "⚠️ 本证属胃火炽盛，不宜灸法",
    points: [],
    method: "不宜灸法 — 胃热炽盛，灸法温补助热，恐加重胃火",
    note: "吴中朝：'辨灸法'——胃热牙痛清胃散清胃凉血，灸法温助与清热治法相悖",
    source: "四大名家共识·热证禁灸",
    technique: "不宜灸法"
  },
  "气虚阳虚-疲劳乏力": {
    effect: "益气培元、健脾和胃",
    points: ["关元", "气海", "足三里", "脾俞", "胃俞", "百会"],
    method: "吴中朝保健灸·背腧功能带灸：脾俞至胃俞背腧带隔姜灸各9壮，关元温和灸",
    note: "吴中朝：气虚乏力灸背腧脾胃带+关元培元。'杂合以治'——灸法+四君子汤协同增效",
    source: "吴中朝·保健灸",
    technique: "背腧功能带灸+温和灸"
  },
  "气虚不固表-自汗": {
    effect: "益气固表、调和营卫",
    points: ["大椎", "肺俞", "脾俞", "足三里", "合谷"],
    method: "陈日新热敏灸·循经往返灸：沿手太阴肺经往返施灸，灸至局部热敏灸感出现",
    note: "陈日新：玉屏风散证气虚不固表，热敏灸激发肺经卫气。灸感消失即停灸",
    source: "陈日新·热敏灸",
    technique: "循经往返灸"
  },
  "阴虚火旺-盗汗": {
    effect: "滋阴降火、固表止汗（阴虚轻量灸）",
    points: ["涌泉", "太溪", "阴郄"],
    method: "陈日新热敏灸·轻量温和灸：涌泉灸5分钟引火下行，阴郄灸8分钟",
    note: "陈日新：阴虚盗汗灸量宜轻，涌泉引火归元为要。非热敏态穴位不宜深灸",
    source: "陈日新·热敏灸（轻量）",
    technique: "轻量温和灸"
  },
  "上焦湿热-头面多汗": {
    effect: "⚠️ 本证属上焦湿热，不宜灸法",
    points: [],
    method: "不宜灸法 — 上焦湿热，灸法温助恐助湿生热",
    note: "吴中朝：湿热证'辨灸法'——麻黄连翘赤小豆汤宣肺利水，灸法温助与清热利湿治法相悖",
    source: "四大名家共识·湿热禁灸",
    technique: "不宜灸法"
  },
  "下焦湿热-下身多汗": {
    effect: "⚠️ 本证属下焦湿热，不宜灸法",
    points: [],
    method: "不宜灸法 — 下焦湿热，灸法温助恐助湿化热",
    note: "吴中朝：龙胆泻肝汤证湿热下注，灸法温助与清利湿热治法相悖。湿热证禁用灸法",
    source: "四大名家共识·湿热禁灸",
    technique: "不宜灸法"
  },
  "厥阴头痛-头顶痛": {
    effect: "温肝暖胃、降逆止痛",
    points: ["百会", "关元", "足三里", "涌泉"],
    method: "崇桂琴督灸法+百会悬灸：督灸扶阳治本，百会悬灸温通厥阴",
    note: "崇桂琴：厥阴头痛督灸扶阳治本，百会悬灸治标。'督灸扶阳，邪不可干'",
    source: "崇桂琴·督灸+悬灸",
    technique: "督灸+悬灸"
  },
  "气血亏虚-头晕": {
    effect: "益气补血、升清养脑",
    points: ["百会", "足三里", "脾俞", "心俞", "关元"],
    method: "吴中朝保健灸·背腧功能带灸：心俞至脾俞背腧带温和灸，百会悬灸",
    note: "吴中朝：气血虚头晕灸背腧心脾带+百会升清。百会灸时注意头发防火",
    source: "吴中朝·保健灸",
    technique: "背腧功能带灸+悬灸"
  },
  "痰湿中阻-头晕": {
    effect: "化痰祛湿、升清降浊",
    points: ["中脘", "丰隆", "百会", "足三里"],
    method: "陈日新热敏灸·中脘透热灸：灸至热感上传至头，丰隆灸至热感下传",
    note: "陈日新：痰湿中阻灸中脘+丰隆效佳，激发'腹气运转'，中焦气机通畅则痰湿自化",
    source: "陈日新·热敏灸",
    technique: "透热灸+循经感传"
  },
  "风热外感-黄稠涕": {
    effect: "⚠️ 本证属风热外感，不宜灸法",
    points: [],
    method: "不宜灸法 — 风热外感，灸法温助恐助热伤津",
    note: "吴中朝：银翘散证风热在表，灸法温助与辛凉解表治法相悖。热证禁用灸法",
    source: "四大名家共识·热证禁灸",
    technique: "不宜灸法"
  },
  "风寒咽痛": {
    effect: "温阳散寒、利咽止痛",
    points: ["天突", "大椎", "风池", "合谷"],
    method: "热敏灸·大椎透热灸：灸至热感传至咽喉部，天突温和灸10分钟",
    note: "陈日新：风寒咽痛热敏灸大椎效佳，灸感传至咽喉部为度。灸后避风保暖",
    source: "陈日新·热敏灸",
    technique: "透热灸+温和灸"
  },
  "风热咽痛": {
    effect: "⚠️ 本证属风热咽痛，不宜灸法",
    points: [],
    method: "不宜灸法 — 风热咽痛，灸法温助恐助热加重",
    note: "吴中朝：桔梗汤证风热咽痛，灸法温助与清热解毒治法相悖",
    source: "四大名家共识·热证禁灸",
    technique: "不宜灸法"
  },
  "寒湿内盛-白厚腻": {
    effect: "温中燥湿、健脾运脾",
    points: ["中脘", "神阙", "足三里", "丰隆", "脾俞"],
    method: "崇桂琴督灸法+中脘隔姜灸：督灸扶阳+中脘隔姜灸12壮",
    note: "崇桂琴：寒湿内盛督灸扶阳治本，中脘隔姜灸燥湿运脾治标。灸后常出现腹内暖流",
    source: "崇桂琴·督灸+隔姜灸",
    technique: "督灸+隔姜灸"
  },
  "湿热内蕴-黄厚腻": {
    effect: "⚠️ 本证属湿热内蕴，不宜灸法",
    points: [],
    method: "不宜灸法 — 湿热内蕴，灸法温助恐助湿化热",
    note: "吴中朝：三仁汤证湿热内蕴，灸法温助与清利湿热治法相悖。湿热证禁用灸法",
    source: "四大名家共识·湿热禁灸",
    technique: "不宜灸法"
  },
  "脾胃虚弱-胃口差": {
    effect: "温中健脾、和胃消食",
    points: ["中脘", "足三里", "脾俞", "胃俞", "公孙"],
    method: "吴中朝保健灸·背腧功能带灸：脾俞至胃俞背腧带隔姜灸，中脘温和灸",
    note: "吴中朝：脾胃虚弱灸背腧脾胃带+中脘调中焦。坚持灸疗可改善消化功能",
    source: "吴中朝·保健灸",
    technique: "背腧功能带灸+温和灸"
  },
  "肝胃不和-反酸烧心": {
    effect: "疏肝和胃、降逆温中",
    points: ["中脘", "足三里", "太冲", "内关"],
    method: "陈日新热敏灸·中脘透热灸：灸至热感透入胃脘，内关灸至热感上传",
    note: "陈日新：肝胃不和灸中脘+内关效佳，热敏灸激发'气至病所'。灸后注意情绪调节",
    source: "陈日新·热敏灸",
    technique: "透热灸"
  },
  "心阳不足-胸闷心慌": {
    effect: "温通心阳、宁心安神",
    points: ["心俞", "厥阴俞", "巨阙", "内关", "膻中"],
    method: "吴中朝保健灸·背腧功能带灸：心俞至厥阴俞背腧带隔姜灸9壮，内关温和灸",
    note: "吴中朝：心阳不足灸心俞+巨阙温通心阳。背腧功能带理论——沿心俞至厥阴俞区域施灸",
    source: "吴中朝·保健灸",
    technique: "背腧功能带灸+隔姜灸"
  },
  "肝郁气滞-两胁胀痛": {
    effect: "疏肝解郁、理气止痛",
    points: ["期门", "膻中", "太冲", "阳陵泉"],
    method: "陈日新热敏灸·期门透热灸：灸至热感传至胁肋部，膻中灸至热感扩散",
    note: "陈日新：肝郁气滞灸期门+膻中效佳，激发肝经感传。灸后保持心情舒畅",
    source: "陈日新·热敏灸",
    technique: "透热灸+循经感传"
  },
  "脾虚湿盛-便溏": {
    effect: "健脾益气、温阳止泻",
    points: ["天枢", "足三里", "阴陵泉", "脾俞", "关元"],
    method: "吴中朝保健灸·背腧功能带灸：脾俞背腧带温和灸，天枢隔姜灸9壮",
    note: "吴中朝：脾虚便溏灸背腧脾俞带+天枢调肠。灸后观察大便性状变化",
    source: "吴中朝·保健灸",
    technique: "背腧功能带灸+隔姜灸"
  },
  "肠燥便秘-大便干结": {
    effect: "⚠️ 本证属肠燥便秘，不宜灸法",
    points: [],
    method: "不宜灸法 — 肠燥便秘，灸法温助恐加重燥热",
    note: "吴中朝：麻子仁丸证肠燥便秘，灸法温助与润肠泄热治法相悖。津亏便秘慎用灸法",
    source: "四大名家共识·津亏禁灸",
    technique: "不宜灸法"
  },
  "湿热下注-大便粘": {
    effect: "⚠️ 本证属湿热下注，不宜灸法",
    points: [],
    method: "不宜灸法 — 湿热下注，灸法温助恐助湿化热",
    note: "吴中朝：葛根芩连汤证协热下利，灸法温助与清热燥湿治法相悖",
    source: "四大名家共识·湿热禁灸",
    technique: "不宜灸法"
  },
  "膀胱湿热-小便黄赤": {
    effect: "⚠️ 本证属膀胱湿热，不宜灸法",
    points: [],
    method: "不宜灸法 — 膀胱湿热，灸法温助恐助热加重",
    note: "吴中朝：八正散证湿热淋证，灸法温助与清热泻火利水治法相悖",
    source: "四大名家共识·湿热禁灸",
    technique: "不宜灸法"
  },
  "脾肾阳虚-五更泻": {
    effect: "温肾暖脾、固肠止泻",
    points: ["关元", "命门", "肾俞", "脾俞", "足三里", "天枢"],
    method: "崇桂琴督灸法+关元隔姜灸：督灸扶阳+关元隔姜灸15壮",
    note: "崇桂琴：五更泻督灸扶阳治本，关元隔姜灸暖命门之火。坚持三个月效佳",
    source: "崇桂琴·督灸+隔姜灸",
    technique: "督灸+隔姜灸"
  },
  "肾阳虚-腰膝酸软": {
    effect: "温补肾阳、强腰健膝",
    points: ["肾俞", "命门", "关元", "腰阳关", "委中", "太溪"],
    method: "崇桂琴督灸法+肾俞隔姜灸：督灸扶阳+肾俞隔姜灸12壮",
    note: "崇桂琴：肾阳虚督灸核心方，肾俞深灸透热为关键。单次灸疗1-2小时",
    source: "崇桂琴·督灸",
    technique: "督灸+隔姜灸"
  },
  "气血不足-颈腰椎僵硬": {
    effect: "益气温经、和血通痹",
    points: ["大椎", "天柱", "后溪", "足三里", "阿是穴"],
    method: "韩善明蕲春艾灸·大灸法：沿膀胱经颈背段大面积施灸，阿是穴重点灸",
    note: "韩善明：蕲春大灸法沿整条膀胱经或大面积施行隔物灸，主治风寒湿痹及气血不足顽疾",
    source: "韩善明·蕲春艾灸",
    technique: "蕲春大灸法"
  },
  "肝郁化火-情绪焦虑": {
    effect: "疏肝解郁、清热安神",
    points: ["百会", "太冲", "行间", "神门", "膻中"],
    method: "吴中朝保健灸·背腧功能带灸：肝俞至胆俞背腧带温和灸，百会悬灸",
    note: "吴中朝：肝郁化火灸背腧肝胆带+百会疏肝升清。注意情绪疏导配合灸疗",
    source: "吴中朝·保健灸",
    technique: "背腧功能带灸+悬灸"
  }
};

// ========== 辅助函数：将对象序列化为JS代码字符串 ==========
function serializePrescriptionEntry(key, obj) {
  const ings = obj.ingredients.map(ing =>
    `      { name: "${ing.name}", unit: "${ing.unit}", base: ${ing.base} }`
  ).join(',\n');
  return `  "${key}": {
    source: "${obj.source}", category: "${obj.category}",
    name: "${obj.name}",
    symptoms: "${obj.symptoms}",
    ingredients: [
${ings}
    ],
    decoction: "${obj.decoction}",
    note: "${obj.note}",
    complexity: ${obj.complexity}
  }`;
}

function serializeSymptomEntry(obj) {
  return `  { label: "${obj.label}", key: "${obj.key}" }`;
}

function serializeAcupointMappingEntry(key, obj) {
  const pts = obj.points.map(p => `"${p}"`).join(', ');
  return `  "${key}": {
    effect: "${obj.effect}",
    points: [${pts}]
  }`;
}

function serializeAcupointTonificationEntry(key, obj) {
  return `  "${key}": { type: "${obj.type}", method: "${obj.method}" }`;
}

function serializeMoxaMappingEntry(key, obj) {
  const pts = obj.points.map(p => `"${p}"`).join(', ');
  return `  "${key}": {
    effect: "${obj.effect}",
    points: [${pts}],
    method: "${obj.method}",
    note: "${obj.note}",
    source: "${obj.source}",
    technique: "${obj.technique}"
  }`;
}

// ========== 主函数：合并到原版HTML ==========
function mergeOriginal() {
  const filePath = '/Users/hf/.kimi_openclaw/workspace/shl-jgyj-formulas.html';
  let content = fs.readFileSync(filePath, 'utf-8');

  // 1. 插入 prescriptions（在 "梅核气" 条目后，prescriptions 对象结束前）
  const prescriptionsInsertMarker = `  "梅核气": {\n    source: "金匮要略", category: "妇人病 · 梅核气",\n    name: "半夏厚朴汤",`;
  const prescriptionsEndMarker = '};\n\n// ========== 辨治要点症状列表';

  const newPrescriptionsCode = '\n  // ========== 倪海厦30问新增方剂 ==========\n' +
    Object.entries(newPrescriptions).map(([k, v]) => serializePrescriptionEntry(k, v)).join(',\n');

  // 找到 prescriptions 对象最后一个 } 的位置，在其后插入
  const lastPrescriptionEnd = content.lastIndexOf('  "梅核气":');
  const afterMoxa = content.indexOf('\n};\n\n// ========== 辨治要点症状列表', lastPrescriptionEnd);
  if (afterMoxa === -1) {
    console.error('Cannot find prescriptions end marker');
    process.exit(1);
  }
  content = content.slice(0, afterMoxa) + ',' + newPrescriptionsCode + '\n' + content.slice(afterMoxa);

  // 2. 插入 symptomList（在最后一个梅核气条目后， symptomList 数组结束前）
  const symptomListEndMarker = '  { label: "咽中如有炙脔，咽喉异物感，胸闷嗳气（半夏厚朴汤）", key: "梅核气" }\n];';
  const newSymptomListCode = '\n  // ========== 倪海厦30问新增症状选项 ==========\n' +
    newSymptomList.map(serializeSymptomEntry).join(',\n');

  const symIdx = content.indexOf(symptomListEndMarker);
  if (symIdx === -1) {
    console.error('Cannot find symptomList end marker');
    process.exit(1);
  }
  content = content.slice(0, symIdx + symptomListEndMarker.length - 2) +
    ',' + newSymptomListCode + '\n' +
    content.slice(symIdx + symptomListEndMarker.length - 2);

  // 3. 插入 acupointMapping（在最后一个梅核气条目后）
  const acuMappingEndMarker = `  "梅核气": {\n    effect: "行气散结、降逆化痰（倪海厦：天突+膻中利咽）",\n    points: ["天突", "膻中", "丰隆", "内关", "太冲", "廉泉"]\n  }\n};`;
  const newAcuMappingCode = '\n  // ========== 倪海厦30问新增针灸配穴 ==========\n' +
    Object.entries(newAcupointMapping).map(([k, v]) => serializeAcupointMappingEntry(k, v)).join(',\n');

  const acuIdx = content.indexOf(acuMappingEndMarker);
  if (acuIdx === -1) {
    console.error('Cannot find acupointMapping end marker');
    process.exit(1);
  }
  content = content.slice(0, acuIdx + acuMappingEndMarker.length - 2) +
    ',' + newAcuMappingCode + '\n' +
    content.slice(acuIdx + acuMappingEndMarker.length - 2);

  // 4. 插入 acupointTonification（在最后一个风市条目后）
  const tonifyEndMarker = '  "风市": { type: "泻", method: "拇指向后捻转，轻插重提，以祛风通络" }\n};';
  const newTonifyCode = '\n  // ========== 倪海厦30问新增穴位补泻 ==========\n' +
    Object.entries(newAcupointTonification).map(([k, v]) => serializeAcupointTonificationEntry(k, v)).join(',\n');

  const tonIdx = content.indexOf(tonifyEndMarker);
  if (tonIdx === -1) {
    console.error('Cannot find acupointTonification end marker');
    process.exit(1);
  }
  content = content.slice(0, tonIdx + tonifyEndMarker.length - 2) +
    ',' + newTonifyCode + '\n' +
    content.slice(tonIdx + tonifyEndMarker.length - 2);

  fs.writeFileSync(filePath, content);
  console.log('Original HTML merged successfully');
  return content;
}

// ========== 主函数：合并到艾灸版HTML ==========
function mergeMoxa() {
  const filePath = '/Users/hf/.kimi_openclaw/workspace/shl-jgyj-formulas-moxa.html';
  let content = fs.readFileSync(filePath, 'utf-8');

  // 1. 插入 prescriptions
  const afterMoxa = content.indexOf('\n};\n\n// ========== 辨治要点症状列表', content.lastIndexOf('  "梅核气":'));
  if (afterMoxa === -1) {
    console.error('Cannot find prescriptions end marker in moxa');
    process.exit(1);
  }
  const newPrescriptionsCode = '\n  // ========== 倪海厦30问新增方剂 ==========\n' +
    Object.entries(newPrescriptions).map(([k, v]) => serializePrescriptionEntry(k, v)).join(',\n');
  content = content.slice(0, afterMoxa) + ',' + newPrescriptionsCode + '\n' + content.slice(afterMoxa);

  // 2. 插入 symptomList
  const symptomListEndMarker = '  { label: "咽中如有炙脔，咽喉异物感，胸闷嗳气（半夏厚朴汤）", key: "梅核气" }\n];';
  const newSymptomListCode = '\n  // ========== 倪海厦30问新增症状选项 ==========\n' +
    newSymptomList.map(serializeSymptomEntry).join(',\n');
  const symIdx = content.indexOf(symptomListEndMarker);
  content = content.slice(0, symIdx + symptomListEndMarker.length - 2) +
    ',' + newSymptomListCode + '\n' +
    content.slice(symIdx + symptomListEndMarker.length - 2);

  // 3. 插入 acupointMapping
  const acuMappingEndMarker = `  "梅核气": {\n    effect: "行气散结、降逆化痰（倪海厦：天突+膻中利咽）",\n    points: ["天突", "膻中", "丰隆", "内关", "太冲", "廉泉"]\n  }\n};`;
  const newAcuMappingCode = '\n  // ========== 倪海厦30问新增针灸配穴 ==========\n' +
    Object.entries(newAcupointMapping).map(([k, v]) => serializeAcupointMappingEntry(k, v)).join(',\n');
  const acuIdx = content.indexOf(acuMappingEndMarker);
  content = content.slice(0, acuIdx + acuMappingEndMarker.length - 2) +
    ',' + newAcuMappingCode + '\n' +
    content.slice(acuIdx + acuMappingEndMarker.length - 2);

  // 4. 插入 acupointTonification
  const tonifyEndMarker = '  "风市": { type: "泻", method: "拇指向后捻转，轻插重提，以祛风通络" }\n};';
  const newTonifyCode = '\n  // ========== 倪海厦30问新增穴位补泻 ==========\n' +
    Object.entries(newAcupointTonification).map(([k, v]) => serializeAcupointTonificationEntry(k, v)).join(',\n');
  const tonIdx = content.indexOf(tonifyEndMarker);
  content = content.slice(0, tonIdx + tonifyEndMarker.length - 2) +
    ',' + newTonifyCode + '\n' +
    content.slice(tonIdx + tonifyEndMarker.length - 2);

  // 5. 插入 moxaMapping
  const moxaEndMarker = `  "梅核气": {\n    effect: "行气散结、降逆化痰（半夏厚朴汤配灸）",\n    points: ["天突", "膻中", "丰隆", "廉泉", "太冲"],\n    method: "天突、膻中温和灸12分钟；丰隆15分钟",\n    note: "梅核气灸天突+膻中利咽散结。吴中朝：颈部病症可用枕项功能带灸辅助",\n    source: "倪海厦经验+吴中朝保健灸",\n    technique: "温和灸"\n  }\n};`;
  const newMoxaCode = '\n  // ========== 倪海厦30问新增艾灸方案 ==========\n' +
    Object.entries(newMoxaMapping).map(([k, v]) => serializeMoxaMappingEntry(k, v)).join(',\n');
  const moxaIdx = content.indexOf(moxaEndMarker);
  if (moxaIdx === -1) {
    // Try alternate marker
    const altMoxaEnd = content.indexOf('"梅核气":', content.indexOf('const moxaMapping'));
    const altEnd2 = content.indexOf('\n};\n\n// ========== 全局状态', altMoxaEnd);
    if (altEnd2 === -1) {
      console.error('Cannot find moxaMapping end marker');
      process.exit(1);
    }
    content = content.slice(0, altEnd2) + ',' + newMoxaCode + '\n' + content.slice(altEnd2);
  } else {
    content = content.slice(0, moxaIdx + moxaEndMarker.length - 2) +
      ',' + newMoxaCode + '\n' +
      content.slice(moxaIdx + moxaEndMarker.length - 2);
  }

  fs.writeFileSync(filePath, content);
  console.log('Moxa HTML merged successfully');
  return content;
}

// ========== 验证JS语法 ==========
function validateHTML(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const scriptStart = content.indexOf('<script>');
  const scriptEnd = content.indexOf('</script>', scriptStart);
  const jsCode = content.slice(scriptStart + 8, scriptEnd);

  const tmpFile = '/tmp/validate_' + Date.now() + '.js';
  fs.writeFileSync(tmpFile, jsCode);
  const { execSync } = require('child_process');
  try {
    execSync(`node --check "${tmpFile}"`, { encoding: 'utf-8' });
    console.log(`✅ ${filePath} syntax OK`);
    fs.unlinkSync(tmpFile);
    return true;
  } catch (e) {
    console.error(`❌ ${filePath} syntax error:`);
    console.error(e.stderr || e.message);
    fs.unlinkSync(tmpFile);
    return false;
  }
}

// ========== 执行 ==========
console.log('=== 开始融合 ===');
mergeOriginal();
mergeMoxa();

console.log('\n=== 验证语法 ===');
const ok1 = validateHTML('/Users/hf/.kimi_openclaw/workspace/shl-jgyj-formulas.html');
const ok2 = validateHTML('/Users/hf/.kimi_openclaw/workspace/shl-jgyj-formulas-moxa.html');

// ========== 生成报告 ==========
if (ok1 && ok2) {
  const report = `# 倪海厦30问融合报告

## 融合概览

- **融合日期**: ${new Date().toISOString().slice(0, 10)}
- **数据来源**: 豆包30问完整数据 + 千问补充数据
- **原版方剂数**: 38 → ${38 + Object.keys(newPrescriptions).length}
- **艾灸版方剂数**: 38 → ${38 + Object.keys(newPrescriptions).length}

## 新增统计

| 项目 | 新增数量 | 备注 |
|------|---------|------|
| 方剂 (prescriptions) | ${Object.keys(newPrescriptions).length} | 27个新方剂 |
| 症状选项 (symptomList) | ${newSymptomList.length} | 对应27个新方剂 |
| 针灸配穴 (acupointMapping) | ${Object.keys(newAcupointMapping).length} | 27个新配穴方案 |
| 穴位补泻 (acupointTonification) | ${Object.keys(newAcupointTonification).length} | 6个新穴位 |
| 艾灸方案 (moxaMapping) | ${Object.keys(newMoxaMapping).length} | 仅艾灸版新增 |

## 新增方剂清单

${Object.entries(newPrescriptions).map(([k, v]) => `- **${v.name}** (${k}) — ${v.source}`).join('\n')}

## 30问条目覆盖情况

### 已完全覆盖（方剂已在系统中）

| 问序号 | 问诊内容 | 辨证分支 | 对应方剂 | 状态 |
|--------|---------|---------|---------|------|
| 1 | 畏寒怕冷/怕热喜凉 | 畏寒怕冷 | 麻黄附子细辛汤、金匮肾气丸 | ✅ 已有 |
| 1 | 畏寒怕冷/怕热喜凉 | 怕热喜凉 | 白虎汤 | ✅ 已有 |
| 2 | 手脚冰凉/手脚心热 | 手脚冰凉 | 当归四逆汤 | ✅ 已有 |
| 3 | 喜热水/喜凉水 | 喜热水 | 理中汤 | ✅ 已有 |
| 4 | 怕风/畏寒 | 怕风自汗 | 桂枝汤 | ✅ 已有 |
| 4 | 怕风/畏寒 | 畏寒无汗 | 麻黄汤 | ✅ 已有 |
| 10 | 头痛部位 | 后枕痛 | 麻黄汤 | ✅ 已有 |
| 10 | 头痛部位 | 两侧痛 | 小柴胡汤 | ✅ 已有 |
| 10 | 头痛部位 | 前额痛 | 葛根汤 | ✅ 已有 |
| 12 | 口苦口干 | 口苦 | 小柴胡汤 | ✅ 已有 |
| 13 | 鼻塞清涕 | 流清涕 | 麻黄汤 | ✅ 已有 |
| 15 | 耳鸣 | 肾虚耳鸣 | 金匮肾气丸 | ✅ 已有 |
| 15 | 耳鸣 | 肝胆火旺 | 小柴胡汤 | ✅ 已有 |
| 17 | 胃口差/食欲亢进 | 食欲亢进 | 白虎汤 | ✅ 已有 |
| 18 | 胃胀胃痛 | 胃寒腹痛 | 理中汤 | ✅ 已有 |
| 19 | 胸闷心慌 | 水饮内停 | 苓桂术甘汤 | ✅ 已有 |
| 21 | 腹部怕冷 | 太阴脾虚寒 | 理中汤 | ✅ 已有 |
| 26 | 入睡困难易醒 | 心血不足 | 酸枣仁汤 | ✅ 已有 |
| 30 | 男科/妇科 | 妇科宫寒血瘀 | 温经汤 | ✅ 已有 |
| 30 | 男科/妇科 | 妇科气血失调 | 当归芍药散 | ✅ 已有 |

### 新增覆盖（本次融合新增）

| 问序号 | 问诊内容 | 辨证分支 | 新增方剂 | 状态 |
|--------|---------|---------|---------|------|
| 2 | 手脚冰凉/手脚心热 | 手脚心热 | 知柏地黄丸 | ✅ 新增 |
| 3 | 喜热水/喜凉水 | 喜凉水 | 清胃散 | ✅ 新增 |
| 5 | 常年疲劳乏力 | 气虚阳虚 | 四君子汤 | ✅ 新增 |
| 6 | 白天自汗 | 气虚不固表 | 玉屏风散 | ✅ 新增 |
| 7 | 夜间盗汗 | 阴虚火旺 | 当归六黄汤 | ✅ 新增 |
| 8 | 头面多汗 | 上焦湿热 | 麻黄连翘赤小豆汤 | ✅ 新增 |
| 9 | 下身多汗 | 下焦湿热 | 龙胆泻肝汤 | ✅ 新增 |
| 10 | 头痛部位 | 头顶痛 | 吴茱萸汤 | ✅ 新增 |
| 11 | 头晕 | 气血亏虚 | 归脾汤 | ✅ 新增 |
| 11 | 头晕 | 痰湿中阻 | 半夏白术天麻汤 | ✅ 新增 |
| 12 | 口干口臭 | 口臭 | 清胃散 | ✅ 新增 |
| 13 | 鼻塞黄稠涕 | 风热外感 | 银翘散 | ✅ 新增 |
| 14 | 咽喉干痛 | 风寒咽痛 | 半夏散及汤 | ✅ 新增 |
| 14 | 咽喉干痛 | 风热咽痛 | 桔梗汤 | ✅ 新增 |
| 16 | 舌苔白厚腻 | 寒湿内盛 | 平胃散 | ✅ 新增 |
| 16 | 舌苔黄厚腻 | 湿热内蕴 | 三仁汤 | ✅ 新增 |
| 17 | 胃口差腹胀 | 脾胃虚弱 | 香砂六君子汤 | ✅ 新增 |
| 18 | 胃胀反酸 | 肝胃不和 | 左金丸 | ✅ 新增 |
| 19 | 胸闷心慌 | 心阳不足 | 桂枝甘草汤 | ✅ 新增 |
| 20 | 两胁胀痛 | 肝郁气滞 | 逍遥散 | ✅ 新增 |
| 22 | 大便稀溏/干结 | 脾虚湿盛 | 参苓白术散 | ✅ 新增 |
| 22 | 大便稀溏/干结 | 阳明腑实 | 麻子仁丸 | ✅ 新增 |
| 23 | 大便粘马桶 | 湿热下注 | 葛根芩连汤 | ✅ 新增 |
| 24 | 小便清长/黄赤 | 膀胱湿热 | 八正散 | ✅ 新增 |
| 25 | 五更泻 | 脾肾阳虚 | 四神丸 | ✅ 新增 |
| 27 | 腰膝酸软 | 肾阳虚 | 右归丸 | ✅ 新增 |
| 28 | 颈腰椎僵硬 | 气血不足 | 黄芪桂枝五物汤 | ✅ 新增 |
| 29 | 情绪焦虑 | 肝郁化火 | 丹栀逍遥散 | ✅ 新增 |
| 30 | 男科/妇科 | 男科下焦湿热 | 龙胆泻肝汤 | ✅ 新增 |
| 30 | 男科/妇科 | 男科肾阳虚 | 右归丸 | ✅ 新增 |

### 需要进一步补充

以下30问条目中，部分辨证分支对应的方剂已在系统中，但部分细节（如具体剂量范围、特殊煎服法）可结合千问补充数据进一步完善：

- **第1问**：金匮肾气丸（已有）— 千问数据提供了更详细的剂量范围
- **第4问**：桂枝汤、麻黄汤（已有）— 千问数据提供了先煎细节
- **第19问**：苓桂术甘汤（已有）— 千问数据提供了水肿加猪苓的提示
- **第24问**：金匮肾气丸（已有）— 千问数据提供了糖尿病去肉桂加黄芪的变方提示

## 新增穴位补泻详情

| 穴位 | 补泻类型 | 手法说明 |
|------|---------|---------|
| 涌泉 | 补 | 拇指向前捻转，重插轻提，或灸，以引火归元、滋阴降火 |
| 阴郄 | 补 | 拇指向前捻转，重插轻提，以养阴清热、固表止汗 |
| 少商 | 泻 | 三棱针点刺出血，以清热利咽、开窍醒神 |
| 商阳 | 泻 | 三棱针点刺出血，以清热消肿、开窍醒神 |
| 腰阳关 | 补 | 拇指向前捻转，重插轻提，或灸，以温肾壮阳、强腰健膝 |
| 行间 | 泻 | 拇指向后捻转，轻插重提，以清肝泻火、疏肝理气 |

## 验证结果

- 原版HTML语法: ${ok1 ? '✅ 通过' : '❌ 失败'}
- 艾灸版HTML语法: ${ok2 ? '✅ 通过' : '❌ 失败'}

## 注意事项

1. 剂量计算逻辑保持不变：成人×1.3，儿童×1.0
2. 现有数据全部保留，未删除任何条目
3. 新增数据追加到现有对象末尾
4. 方剂名使用标准名称
5. 煎服法使用豆包文档原文
6. 艾灸版中热证/湿热证标注"不宜灸法"，符合四大名家共识
`;
  fs.writeFileSync('/Users/hf/.kimi_openclaw/workspace/融合报告.md', report);
  console.log('\n=== 融合报告已生成 ===');
  console.log(report);
}
