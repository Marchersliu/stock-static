#!/usr/bin/env python3
"""习惯追踪 - streak、统计、图表"""
import argparse, json, os
from datetime import datetime, date

DB_PATH = '/Users/hf/.kimi_openclaw/workspace/memory/habits.json'

def load_habits():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'habits': []}

def save_habits(habits):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(habits, f, ensure_ascii=False, indent=2)

def add_habit(name, frequency='daily', goal=''):
    habits = load_habits()
    habit = {
        'id': len(habits['habits']) + 1,
        'name': name,
        'frequency': frequency,
        'goal': goal,
        'created': datetime.now().isoformat(),
        'checkins': []
    }
    habits['habits'].append(habit)
    save_habits(habits)
    print(f'[Habit] #{habit["id"]} {name} [{frequency}]')
    return habit

def checkin(habit_name_or_id):
    habits = load_habits()
    today = date.today().isoformat()
    
    for h in habits['habits']:
        if str(h['id']) == str(habit_name_or_id) or h['name'] == habit_name_or_id:
            if today not in h['checkins']:
                h['checkins'].append(today)
                save_habits(habits)
                streak = calc_streak(h['checkins'])
                print(f'[Checkin] #{h["id"]} {h["name"]} ✅ (streak: {streak} days)')
                return
            else:
                print(f'[Info] Already checked in today')
                return
    print(f'[ERR] Habit not found: {habit_name_or_id}')

def calc_streak(checkins):
    if not checkins:
        return 0
    dates = sorted([datetime.strptime(d, '%Y-%m-%d').date() for d in checkins], reverse=True)
    streak = 1
    for i in range(1, len(dates)):
        if (dates[i-1] - dates[i]).days == 1:
            streak += 1
        else:
            break
    return streak

def stats():
    habits = load_habits()
    print(f'\n[Habits] {len(habits["habits"])} habits:')
    for h in habits['habits']:
        streak = calc_streak(h['checkins'])
        total = len(h['checkins'])
        today = date.today().isoformat()
        done_today = '✅' if today in h['checkins'] else '⬜'
        print(f'\n  #{h["id"]} {done_today} {h["name"]}')
        print(f'     Streak: {streak} days | Total: {total} checkins')
        print(f'     Goal: {h["goal"]}')
        if h['checkins']:
            print(f'     Last 7 days: {", ".join(h["checkins"][-7:])}')

def chart():
    habits = load_habits()
    print('\n[Habit Chart] Last 30 days:')
    for h in habits['habits']:
        print(f'\n  {h["name"]}:')
        days = []
        for i in range(29, -1, -1):
            d = (date.today() - __import__('datetime').timedelta(days=i)).isoformat()
            days.append('●' if d in h['checkins'] else '○')
        print(f'    {" ".join(days)}')

def main():
    parser = argparse.ArgumentParser(description='Habit Tracker')
    sub = parser.add_subparsers(dest='cmd')
    
    p = sub.add_parser('add')
    p.add_argument('name')
    p.add_argument('--frequency', default='daily', choices=['daily', 'weekday', 'weekly'])
    p.add_argument('--goal', default='')
    
    p = sub.add_parser('checkin')
    p.add_argument('habit')
    
    sub.add_parser('stats')
    sub.add_parser('chart')
    sub.add_parser('list')
    
    args = parser.parse_args()
    
    if args.cmd == 'add':
        add_habit(args.name, args.frequency, args.goal)
    elif args.cmd == 'checkin':
        checkin(args.habit)
    elif args.cmd == 'stats':
        stats()
    elif args.cmd == 'chart':
        chart()
    elif args.cmd == 'list':
        habits = load_habits()
        print(f'[Habits] {len(habits["habits"])} habits:')
        for h in habits['habits']:
            print(f'  #{h["id"]} {h["name"]} [{h["frequency"]}]')
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
