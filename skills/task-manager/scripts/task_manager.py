#!/usr/bin/env python3
"""任务管理 - 创建、跟踪、优先级排序"""
import argparse
import json
import os
from datetime import datetime

DB_PATH = "/Users/hf/.kimi_openclaw/workspace/memory/tasks.json"


def load_tasks():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"tasks": []}


def save_tasks(tasks):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def add_task(title, priority="P2", due=None, tags=None, desc=""):
    tasks = load_tasks()
    task = {
        "id": len(tasks["tasks"]) + 1,
        "title": title,
        "description": desc,
        "priority": priority,
        "due": due,
        "tags": tags or [],
        "status": "pending",
        "created": datetime.now().isoformat(),
        "completed": None,
    }
    tasks["tasks"].insert(0, task)
    save_tasks(tasks)
    print(f'[Task] #{task["id"]} [{priority}] {title}')
    return task


def list_tasks(status=None, priority=None):
    tasks = load_tasks()
    items = tasks["tasks"]

    if status:
        items = [t for t in items if t["status"] == status]
    if priority:
        priorities = priority.split(",")
        items = [t for t in items if t["priority"] in priorities]

    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    items.sort(key=lambda x: priority_order.get(x["priority"], 99))

    icons = {"P0": "🔴", "P1": "🟡", "P2": "🟢", "P3": "⚪"}

    print(f"\n[Tasks] {len(items)} tasks:")
    for t in items:
        icon = icons.get(t["priority"], "⚪")
        due_str = f' (due: {t["due"]})' if t.get("due") else ""
        status_str = "✅" if t["status"] == "done" else "⬜"
        print(
            f'  {status_str} #{t["id"]} {icon}[{t["priority"]}] {t["title"]}{due_str}'
        )
        if t.get("tags"):
            print(f'     Tags: {", ".join(t["tags"])}')


def done_task(task_id):
    tasks = load_tasks()
    for t in tasks["tasks"]:
        if t["id"] == task_id:
            t["status"] = "done"
            t["completed"] = datetime.now().isoformat()
            save_tasks(tasks)
            print(f'[Done] #{task_id}: {t["title"]}')
            return
    print(f"[ERR] Task #{task_id} not found")


def delete_task(task_id):
    tasks = load_tasks()
    tasks["tasks"] = [t for t in tasks["tasks"] if t["id"] != task_id]
    save_tasks(tasks)
    print(f"[Deleted] #{task_id}")


def check_overdue():
    tasks = load_tasks()
    today = datetime.now().date()
    overdue = []
    for t in tasks["tasks"]:
        if t["status"] == "pending" and t.get("due"):
            due = datetime.strptime(t["due"], "%Y-%m-%d").date()
            if due < today:
                overdue.append(t)

    if overdue:
        print(f"\n⚠️  Overdue tasks ({len(overdue)}):")
        for t in overdue:
            print(f'  #{t["id"]} [{t["priority"]}] {t["title"]} (due: {t["due"]})')


def main():
    parser = argparse.ArgumentParser(description="Task Manager")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("add")
    p.add_argument("title")
    p.add_argument("--priority", default="P2", choices=["P0", "P1", "P2", "P3"])
    p.add_argument("--due", help="Due date YYYY-MM-DD")
    p.add_argument("--tags", nargs="+")
    p.add_argument("--desc", default="")

    p = sub.add_parser("list")
    p.add_argument("--status", choices=["pending", "done"])
    p.add_argument("--priority", help="P0,P1,P2,P3 comma-separated")

    p = sub.add_parser("done")
    p.add_argument("id", type=int)

    p = sub.add_parser("delete")
    p.add_argument("id", type=int)

    sub.add_parser("overdue")

    args = parser.parse_args()

    if args.cmd == "add":
        add_task(args.title, args.priority, args.due, args.tags, args.desc)
    elif args.cmd == "list":
        list_tasks(args.status, args.priority)
    elif args.cmd == "done":
        done_task(args.id)
    elif args.cmd == "delete":
        delete_task(args.id)
    elif args.cmd == "overdue":
        check_overdue()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
