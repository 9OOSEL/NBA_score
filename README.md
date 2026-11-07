# 코트사이드 기록실

선수 이름을 검색하면 1996-97 시즌부터 지금까지의 NBA 정규시즌 성적을 시즌별로 보여주는 페이지예요.

- 페이지: `docs/index.html` (GitHub Pages로 배포)
- 데이터: `docs/data.json` (NBA.com 공식 통계, 경기당 평균)
- 갱신: NBA.com(stats.nba.com, cdn.nba.com)이 GitHub 서버의 접속을 막아서, 집 컴퓨터에서 `update.bat`을 실행해 갱신해요.
- 한글 이름 검색: `scripts/ko_names.json`에 영문 이름과 한글 이름을 추가하면 다음 갱신 때 반영돼요.

처음 한 번 준비: Python과 Git 설치 → `pip install nba_api` → 이 저장소를 clone.
전체 시즌을 다시 받으려면 `python scripts/update_data.py --all`.
