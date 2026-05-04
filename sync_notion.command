#!/bin/bash
# NFX Manual - Notion Sync Script
# 이 파일을 더블 클릭하면 노션 데이터와 동기화됩니다.

# 스크립트가 위치한 폴더로 이동
cd "$(dirname "$0")"
SCRIPT_DIR="$(pwd)"

echo "------------------------------------------------"
echo "🔄 midas NFX 노션 동기화를 시작합니다..."
echo "📍 작업 폴더: $SCRIPT_DIR"
echo "------------------------------------------------"

# 가상환경 확인 (NFX Online Manual의 venv 활용)
if [ -d "../NFX Online Manual/venv" ]; then
    echo "✅ 기존 NFX Online Manual의 안정적인 가상환경을 사용합니다."
    "../NFX Online Manual/venv/bin/python" notion_sync.py
else
    echo "⚠️ 가상환경을 찾을 수 없습니다. 시스템 파이썬을 시도합니다."
    python3 notion_sync.py
fi

echo ""
echo "------------------------------------------------"
echo "🎉 동기화 작업이 완료되었습니다."
echo "브라우저를 새로고침하여 확인하세요."
echo "------------------------------------------------"

