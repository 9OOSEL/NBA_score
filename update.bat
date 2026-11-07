@echo off
chcp 65001 >nul
cd /d "%~dp0"
git pull -q
python scripts\update_data.py
if errorlevel 1 (
  echo 데이터를 받지 못했어요. 인터넷 연결을 확인하고 다시 실행해 주세요.
  exit /b 1
)
git add docs/data.json
git diff --cached --quiet && (echo 바뀐 기록이 없어요.& exit /b 0)
git commit -q -m "데이터 갱신 %date%"
git push -q
echo 갱신 완료!
