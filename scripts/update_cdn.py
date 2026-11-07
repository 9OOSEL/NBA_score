"""이번 시즌 기록을 NBA.com 경기별 박스스코어(cdn.nba.com)로 합산해 docs/data.json을 갱신합니다.

GitHub Actions에서 매일 실행돼요. stats.nba.com은 클라우드 서버 접속을 막지만 cdn.nba.com은 열려 있어요.
지난 시즌 기록은 건드리지 않고, 이번 시즌 줄만 다시 계산해요.

경기별 선수 기록은 data/games_<시즌>.json에 모아 두고, 최근 3일 경기는 기록 정정을 반영하려고 다시 받아요.
"""
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "data.json"
CACHE_DIR = ROOT / "data"
KO = json.loads((ROOT / "scripts" / "ko_names.json").read_text(encoding="utf-8"))
KST = timezone(timedelta(hours=9))
SCHEDULE = "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json"
BOX = "https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{}.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "Accept": "application/json",
}
session = requests.Session()
session.headers.update(HEADERS)


def get(url, tries=3):
    for i in range(tries):
        try:
            r = session.get(url, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"  실패 ({i + 1}/{tries}) {url}: {e}")
            time.sleep(3 * (i + 1))
    return None


def minutes(s):
    m = re.match(r"PT(\d+)M([\d.]+)S", s or "")
    return int(m.group(1)) + float(m.group(2)) / 60 if m else 0.0


def lines_from_box(box):
    """한 경기에서 뛴 선수들의 기록 줄: [pid, 이름, 팀, 출전분, 득점, 리바, 어시, 스틸, 블록, 턴오버, FGM, FGA, 3PM, 3PA, FTM, FTA]"""
    out = []
    for side in ("homeTeam", "awayTeam"):
        t = box["game"][side]
        for p in t["players"]:
            if p.get("played") != "1":
                continue
            s = p["statistics"]
            out.append([p["personId"], p["name"], t["teamTricode"], round(minutes(s["minutes"]), 3),
                        s["points"], s["reboundsTotal"], s["assists"], s["steals"], s["blocks"], s["turnovers"],
                        s["fieldGoalsMade"], s["fieldGoalsAttempted"], s["threePointersMade"],
                        s["threePointersAttempted"], s["freeThrowsMade"], s["freeThrowsAttempted"]])
    return out


def main():
    sched = get(SCHEDULE)
    if not sched:
        sys.exit("일정 데이터를 받지 못했어요")
    season = sched["leagueSchedule"]["seasonYear"]  # 예: 2026-27
    games = [g for d in sched["leagueSchedule"]["gameDates"] for g in d["games"]]
    finals = [g for g in games if g["gameStatus"] == 3 and g["gameId"].startswith("002")]  # 정규시즌 종료 경기
    print(f"{season} 시즌 정규시즌 종료 경기 {len(finals)}개")

    CACHE_DIR.mkdir(exist_ok=True)
    cache_path = CACHE_DIR / f"games_{season}.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}

    recent = datetime.now(timezone.utc) - timedelta(days=3)
    todo = []
    for g in finals:
        when = datetime.fromisoformat(g["gameDateTimeUTC"].replace("Z", "+00:00"))
        if g["gameId"] not in cache or when >= recent:
            todo.append(g["gameId"])
    print(f"받을 박스스코어 {len(todo)}개")
    failed = 0
    for gid in todo:
        box = get(BOX.format(gid))
        if box:
            cache[gid] = lines_from_box(box)
        else:
            failed += 1
        time.sleep(0.3)
    if todo and failed == len(todo):
        sys.exit("박스스코어를 하나도 받지 못했어요")
    cache = {gid: v for gid, v in cache.items() if gid in {g["gameId"] for g in finals}}
    cache_path.write_text(json.dumps(cache, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")

    # 시즌 합계
    tot = {}
    for gid in sorted(cache):
        for ln in cache[gid]:
            pid = str(ln[0])
            t = tot.setdefault(pid, {"name": ln[1], "team": ln[2], "gp": 0, "v": [0.0] * 13})
            t["name"], t["team"] = ln[1], ln[2]  # 마지막 경기 기준 팀
            t["gp"] += 1
            for i, x in enumerate(ln[3:]):
                t["v"][i] += x

    data = json.loads(OUT.read_text(encoding="utf-8"))
    seasons, players = data["seasons"], data["players"]
    if season not in seasons:
        seasons.append(season)
    si = seasons.index(season)
    prev_age = {}  # 박스스코어에 나이가 없어서 기존 기록에서 가져옴
    for pid, (_, rows) in players.items():
        cur = [r for r in rows if r[0] == si]
        last = [r for r in rows if r[0] == si - 1]
        if cur:
            prev_age[pid] = cur[0][2]
        elif last and last[0][2] is not None:
            prev_age[pid] = last[0][2] + 1
        players[pid][1] = [r for r in rows if r[0] != si]

    pct = lambda m, a: round(m / a, 3) if a else 0
    for pid, t in tot.items():
        gp = t["gp"]
        mi, pts, reb, ast, stl, blk, tov, fgm, fga, m3, a3, ftm, fta = t["v"]
        row = [si, t["team"], prev_age.get(pid), gp, round(mi / gp, 1), round(pts / gp, 1), round(reb / gp, 1),
               round(ast / gp, 1), round(stl / gp, 1), round(blk / gp, 1), round(tov / gp, 1),
               pct(fgm, fga), round(m3 / gp, 1), pct(m3, a3), pct(ftm, fta)]
        players.setdefault(pid, [t["name"], []])
        players[pid][1].append(row)
        players[pid][1].sort(key=lambda r: r[0])
    data["players"] = {pid: v for pid, v in players.items() if v[1]}
    data["ko"] = {pid: KO[n] for pid, (n, _) in data["players"].items() if n in KO}
    new = sorted({n for n, _ in data["players"].values() if n not in KO})
    if new:
        print("한글 이름이 없는 선수:", ", ".join(new))
    data["updated"] = datetime.now(KST).strftime("%Y-%m-%d")
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"저장 완료: {season} 시즌 {len(tot)}명")


if __name__ == "__main__":
    main()
