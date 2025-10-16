#!/bin/bash
# 뉴스 수집 스크립트 실행 헬퍼

echo "뉴스 수집을 시작합니다..."
docker-compose exec backend python collect_news.py "$@"
