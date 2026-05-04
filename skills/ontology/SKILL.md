---
name: ontology
description: 知识本体管理技能。建立概念分类体系、实体关系网络、领域知识图谱，实现结构化的知识组织和推理。当用户需要：(1) 建立项目/领域的知识体系，(2) 梳理概念之间的层级关系，(3) 进行知识推理和关联发现，(4) 管理复杂项目的知识结构时使用。
---

# Ontology 知识本体管理

## 核心概念

```
本体 = 概念(Concept) + 关系(Relation) + 实例(Instance) + 规则(Rule)

示例：股票投资领域
  股票 ──isa── 金融资产
  九州一轨 ──instance── 股票
  股票 ──has_sector── 轨交设备
  轨交设备 ──part_of── 制造业
```

## 功能模块

| 模块 | 功能 | 用法 |
|------|------|------|
| **概念管理** | 添加/删除/查询概念 | `add_concept`, `get_concept` |
| **关系管理** | 建立概念间关系 | `add_relation`, `query_relation` |
| **实例管理** | 管理具体实体 | `add_instance`, `get_instances` |
| **推理引擎** | 基于关系推理 | `infer`, `find_path` |
| **导入导出** | JSON/OWL/RDF | `export_json`, `import_json` |

## 用法

```bash
# 添加概念
python3 ontology.py add-concept "股票" --parent "金融资产"

# 添加关系
python3 ontology.py add-relation "股票" "has_sector" "轨交设备"

# 查询实例
python3 ontology.py get-instances "股票"

# 推理路径
python3 ontology.py find-path "九州一轨" "制造业"

# 导出
python3 ontology.py export --format json --output ontology.json
```

## 快速命令

```bash
cd /Users/hf/.kimi_openclaw/workspace/skills/ontology/scripts
python3 ontology.py --help
```
