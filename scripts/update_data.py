"""NBA.com 공식 통계에서 1996-97 시즌부터 현재 시즌까지 정규시즌 선수 성적을 받아 docs/data.json을 만듭니다.

실행: python scripts/update_data.py
필요: pip install nba_api
"""
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from nba_api.stats.endpoints import leaguedashplayerstats

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "data.json"
KO = json.loads((ROOT / "scripts" / "ko_names.json").read_text(encoding="utf-8"))
KST = timezone(timedelta(hours=9))
KEYS = ["TEAM_ABBREVIATION", "AGE", "GP", "MIN", "PTS", "REB", "AST", "STL", "BLK",
        "TOV", "FG_PCT", "FG3M", "FG3_PCT", "FT_PCT"]


def current_start_year(now):
    # NBA 시즌은 10월에 시작
    return now.year if now.month >= 10 else now.year - 1


def fetch(season, tries=3):
    for i in range(tries):
        try:
            r = leaguedashplayerstats.LeagueDashPlayerStats(
                season=season, per_mode_detailed="PerGame",
                season_type_all_star="Regular Season", timeout=60)
            return r.get_dict()["resultSets"][0]
        except Exception as e:  # 네트워크 오류 시 재시도
            print(f"  {season} 실패 ({i + 1}/{tries}): {e}")
            time.sleep(5 * (i + 1))
    raise RuntimeError(f"{season} 시즌 데이터를 받지 못했습니다")


def main():
    now = datetime.now(KST)
    seasons = [f"{y}-{(y + 1) % 100:02d}" for y in range(1996, current_start_year(now) + 1)]
    players = {}
    for si, s in enumerate(seasons):
        rs = fetch(s)
        h = rs["headers"]
        idx = [h.index(k) for k in KEYS]
        for row in rs["rowSet"]:
            pid = str(row[0])
            players.setdefault(pid, [row[1], []])
            players[pid][1].append([si] + [row[i] for i in idx])
        print(f"{s}: {len(rs['rowSet'])}명")
        time.sleep(1.5)

    byname = {}
    for pid, (name, _) in players.items():
        byname.setdefault(name, pid)
    ko = {byname[en]: k for en, k in KO.items() if en in byname}

    out = {"seasons": seasons, "players": players, "ko": ko, "updated": now.strftime("%Y-%m-%d")}
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"저장 완료: {len(players)}명, {OUT.stat().st_size // 1024}KB")


if __name__ == "__main__":
    main()
