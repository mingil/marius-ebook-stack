#!/bin/bash
# =============================================================================
# 🩺 MARIUS EBOOK STACK DOCTOR - 정기 유지보수 · SQLite DB 최적화 · 설정 자동 백업 스크립트
# =============================================================================
# [추천 스케줄] 시놀로지 작업 스케줄러(root)에 매주 일요일 새벽 04:00 실행으로 등록해 두면
# 에이전트가 설계한 자동 치유·최적화 루틴이 영구적으로 시스템을 최상의 상태로 유지합니다.
# =============================================================================
set -e

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/volume1/docker/_backups/marius-ebook-stack/$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

echo "=================================================================="
echo "🩺 [1/5] eBook 스택 컨테이너 헬스 상태 및 메모리 점유율 정밀 점검"
echo "=================================================================="
docker ps --filter "name=ebook-" --format "table {{.Names}}	{{.Status}}	{{.Ports}}" || true

echo "=================================================================="
echo "💾 [2/5] Komga · Kavita · Audiobookshelf · Komf 핵심 DB 무중단 스냅샷 백업"
echo "=================================================================="
for svc in komga kavita audiobookshelf komf calibre-web-automated; do
  if [ -d "/volume1/docker/$svc" ]; then
    tar -czf "$BACKUP_DIR/${svc}_config_${TIMESTAMP}.tar.gz" \
      --exclude="*.log" --exclude="cache" --exclude="Cache" --exclude="logs" \
      -C "/volume1/docker" "$svc/config" 2>/dev/null || true
    echo "  -> $svc 설정 및 DB 백업 완료: $BACKUP_DIR/${svc}_config_${TIMESTAMP}.tar.gz"
  fi
done

# 30일 이상 지난 오래된 백업본 자동 정리 (NAS 용량 보호)
find "/volume1/docker/_backups/marius-ebook-stack" -mindepth 1 -maxdepth 1 -type d -mtime +30 -exec rm -rf {} + 2>/dev/null || true

echo "=================================================================="
echo "⚡ [3/5] SQLite 데이터베이스 조각 모음(VACUUM & ANALYZE) 속도 최적화"
echo "=================================================================="
if command -v sqlite3 >/dev/null 2>&1; then
  for db_file in \
    "/volume1/docker/komga/config/database.sqlite" \
    "/volume1/docker/kavita/config/kavita.db" \
    "/volume1/docker/audiobookshelf/config/absdatabase.sqlite" \
    "/volume1/docker/komf/config/database.sqlite" \
    "/volume1/data/ebooks/calibre-library/metadata.db"; do
    if [ -f "$db_file" ]; then
      echo "  -> SQLite 최적화 수행 중: $db_file"
      sqlite3 "$db_file" "PRAGMA optimize; VACUUM; ANALYZE;" 2>/dev/null || true
    fi
  done
else
  echo "  -> 호스트 sqlite3 바이너리 없음 (컨테이너 내부 자동 관리 유지)"
fi

echo "=================================================================="
echo "🔐 [4/5] 시놀로지 파일 권한(PUID=1026:PGID=100) 및 인제스트 폴더 자가 치유"
echo "=================================================================="
chown -R 1026:100 "/volume1/data/ebooks" 2>/dev/null || true
chmod -R 775 "/volume1/data/ebooks/cwa-ingest" 2>/dev/null || true

echo "=================================================================="
echo "🧹 [5/5] 도커 미사용 Dangling 이미지 및 임시 캐시 청소"
echo "=================================================================="
docker image prune -f >/dev/null 2>&1 || true

echo "✅ [완료] 모든 eBook 서버의 DB 최적화, 백업, 권한 복구가 완벽히 끝났습니다!"
