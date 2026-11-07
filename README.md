# 코트사이드 기록실

선수 이름을 검색하면 1996-97 시즌부터 지금까지의 NBA 정규시즌 성적을 시즌별로 보여주는 페이지예요.

- 페이지: `docs/index.html` (GitHub Pages로 배포)
- 데이터: `docs/data.json` (NBA.com 공식 통계, 경기당 평균)
- 갱신: `scripts/update_data.py`를 GitHub Actions가 매일 한국 시간 오전 8시쯤 실행해요. Actions 탭의 "NBA 데이터 갱신"에서 직접 실행할 수도 있어요.
- 한글 이름 검색: `scripts/ko_names.json`에 영문 이름과 한글 이름을 추가하면 다음 갱신 때 반영돼요.

컴퓨터에서 직접 갱신하려면:

```
pip install nba_api
python scripts/update_data.py
```
