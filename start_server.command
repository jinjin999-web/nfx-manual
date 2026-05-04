#!/bin/bash
cd "$(dirname "$0")"

echo "1. 노션 데이터 동기화 중..."
if ! ./sync_notion.command; then
    echo "❌ 노션 동기화 실패! 스크립트를 중단합니다."
    exit 1
fi

echo "2. 기존 사이트 데이터 정리 중..."
rm -rf site
mkdir -p docs

echo "3. 사이트 빌드 중..."
if ! uvx zensical build; then
    echo "❌ 빌드 실패! 스크립트를 중단합니다."
    exit 1
fi

echo "4. Zensical 서버 시작 및 브라우저 오픈..."
# 8000 포트가 이미 사용 중이라면 종료 (os error 48 방지)
lsof -i tcp:8000 | awk 'NR!=1 {print $2}' | xargs kill -9 2>/dev/null

# 서버가 완전히 뜰 때까지 3초 대기 후 브라우저 열기
(sleep 3 && open http://localhost:8000) &

# 서버 실행
uvx zensical serve
