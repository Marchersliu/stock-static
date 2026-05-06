# Token 识别模式参考文档

## 高风险Token模式

### 1. Kimi / OpenAI API Key
```regex
sk-[a-zA-Z0-9]{20,}
```
示例：`sk-9WNjMdFQtiDxuvDBQEYam3G5YFXSnu6PGezrJTbo1W6PPDp6`

### 2. Tushare Pro Token
```regex
[a-f0-9]{40}
```
示例：`6e00a3a46d148610fba8c49fdd6c44e8c3455a4d898f4f06b16de929`
注意：Git commit hash 也是40位hex，扫描时需排除git上下文

### 3. 企业微信 Secret
```regex
[A-Za-z0-9]{20,}
```
注意：容易误报，需结合上下文判断

### 4. Bearer Token
```regex
Bearer\s+[a-zA-Z0-9\-_]+
```

### 5. API Key 各种变体
```regex
api[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9]{10,}
api[_-]?secret\s*[:=]\s*["\']?[a-zA-Z0-9]{10,}
```

### 6. 密码/Secret
```regex
password\s*[:=]\s*["\']?[a-zA-Z0-9]+
secret\s*[:=]\s*["\']?[a-zA-Z0-9]{10,}
```

## 误报排除规则

| 场景 | 排除方法 |
|------|---------|
| Git commit hash | 排除含 `commit ` 或 `index ` 前缀的行 |
| CSS color code | `#` 开头、长度6或8的hex |
| MD5 hash | 通常32位，与40位token区分 |
| UUID | 含 `-` 分隔符，与纯hex区分 |
| 随机字符串 | 结合上下文判断（如变量名、注释） |

## 安全文件清单

### 绝不上传 GitHub
| 文件 | 风险等级 | 说明 |
|------|---------|------|
| `.env` | 🔴 极高 | 环境变量，存所有token |
| `.env.local` | 🔴 极高 | 本地环境变量 |
| `.env.production` | 🔴 极高 | 生产环境变量 |
| `TOOLS.md` | 🔴 极高 | 本地工具笔记，可能含token |
| `stock_service.py` | 🔴 极高 | 业务脚本 |
| `start_service.sh` | 🟡 中 | 启动脚本，加载.env |

### 可上传 GitHub
| 文件 | 说明 |
|------|------|
| `index.html` | 看板前端 |
| `.github/workflows/pages.yml` | Actions配置 |
| `.gitignore` | 屏蔽规则 |
| `README.md` | 项目说明 |
