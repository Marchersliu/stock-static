---
name: voice-memos
description: 语音备忘录技能。语音转文字记录，支持实时转录和文件转录，自动添加时间戳和标签。适用于会议记录、灵感捕捉、语音笔记。支持中文/英文识别。
---

# Voice Memos 语音备忘录

## 核心功能

| 功能 | 说明 | 输入 |
|------|------|------|
| **实时转录** | 麦克风实时语音转文字 | 麦克风 |
| **文件转录** | 音频文件转文字 | .wav / .mp3 / .m4a |
| **时间戳** | 自动添加时间标记 | 自动 |
| **标签** | 自动关键词标签 | 自动提取 |
| **摘要** | 生成语音内容摘要 | 自动 |
| **搜索** | 搜索历史语音记录 | 关键词 |

## 用法

```bash
# 转录音频文件
python3 voice_memos.py transcribe /path/to/recording.m4a --output note.md

# 实时转录（按Ctrl+C停止）
python3 voice_memos.py realtime --duration 60 --output live.md

# 查看历史记录
python3 voice_memos.py list

# 搜索记录
python3 voice_memos.py search "会议"

# 生成摘要
python3 voice_memos.py summarize note.md
```

## 存储位置

```
memory/
└── voice_memos/
    ├── 2026-05-04_143022.md
    ├── 2026-05-04_152045.md
    └── index.json
```

## 快速命令

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/voice-memos/scripts
python3 voice_memos.py transcribe /path/to/audio.m4a
```

## 依赖安装

```bash
pip3 install openai-whisper
# 或使用系统语音识别API
```

## 注意

- macOS 可用系统 `dictation` 或 `say` 命令
- 大文件建议分段处理
- 敏感内容标记 🔒
