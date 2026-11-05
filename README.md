# 📚 Marius-Style Ultimate eBook, Manga, Webtoon & Audiobook Stack (`marius-ebook-stack`)

시놀로지 NAS(**DS920+** 및 DSM 7.2 전 모델)와 모든 홈서버 환경을 위한 **Marius Hosting 블로그(`mariushosting.com`) 표준 규격** 기반 **현존 최고 사양 11종 eBook · 만화 · 웹툰 · 오디오북 전자동화 스택 & 유지보수 컨트롤 스튜디오**입니다.

---

## 🔍 기존 `ebook-library` 정밀 진단 및 7대 핵심 해결 내역 (Root-Cause Diagnosis)

기존 업로드해주신 `ebook-library` (`compose.yaml`, `.env`)를 전수 분석하여 아래 7가지 문제를 완벽히 진단·해결하고 프로젝트명을 **`marius-ebook-stack`**으로 표준화했습니다.

1. **[CRITICAL] Audiobookshelf 중첩(Nested) 볼륨 마운트 버그 해결**
   - **원인**: 기존에는 상위 폴더 자체인 `/volume1/docker/audiobookshelf:/config:rw`를 마운트하면서 그 하위인 `/volume1/docker/audiobookshelf/audiobooks`와 `/metadata`를 중복 마운트하여, 설정 백업·스캔 시 수십 GB의 오디오북까지 설정 파일로 오인해 디스크 병목과 백업 폭발을 일으키는 치명적 구조였습니다.
   - **해결**: `/volume1/docker/audiobookshelf/config:/config:rw`로 완전히 분리하고, 초기화 스크립트(`synology-ebook-init.sh`)가 기존 상위 폴더의 `absdatabase.sqlite` 등 DB 파일만 안전하게 `config/` 하위로 자동 무손실 이관하도록 설계했습니다.
2. **[CRITICAL] Kavita & Audiobookshelf 미완성 설정 및 시놀로지 `PUID=1026` / `PGID=100` 권한 누락 해결**
   - **원인**: 기존 파일에 `PUID`/`PGID` 및 `user: "1026:100"`이 빠져 있어 컨테이너가 `root` 권한으로 메타데이터·캐시를 생성해 시놀로지 DSM File Station에서 파일 수정/이동이 거부되는 권한 충돌이 발생합니다.
   - **해결**: 전 컨테이너에 시놀로지 표준 `1026:100` 권한과 `security_opt: no-new-privileges:true`를 Marius 표준으로 적용했습니다.
3. **[HIGH] Komf 부팅 순서(Race Condition) 및 전 컨테이너 `healthcheck` 완비**
   - **원인**: Komga(Spring Boot)와 Kavita(.NET)가 부팅(30~60초 소요)되기 전에 Komf가 먼저 API 연결을 시도하다가 Connection Refused 에러로 재시작하는 문제를 방지하기 위해 모든 컨테이너에 `healthcheck`를 달고 `condition: service_healthy`로 순서를 제어했습니다.
4. **[HIGH] 스토리지 파편화 해결 (기존 서재 100% 무손실 호환 + 통합 마스터 볼륨 `/data` 도입)**
   - **원인**: `/volume1/docker/komga/data`, `/volume1/docker/kavita/data` 등 설정 폴더 내부에 도서 원본이 쪼개져 있어 앱 간 도서 공유와 백업 분리가 불가능했습니다.
   - **해결**: 기존 경로(`/legacy-komga-data`, `/legacy-kavita-manga`, `/legacy-audiobooks`)를 함께 마운트해 **기존 등록된 책과 독서 진도를 단 1권도 잃지 않으면서**, 동시에 전 컨테이너가 `/volume1/data/ebooks:/data:rw` 통합 마스터 볼륨을 공유하도록 업그레이드했습니다.
5. **[HIGH] Komf 한국어·글로벌 메타데이터 엔진 설정(`application.yml`) 자동 생성**
   - **해결**: Komga(`http://komga:25600`)와 Kavita(`http://kavita:5000`) 양쪽의 신규 책 추가 이벤트를 실시간 감지해 AniList, MangaUpdates, Bangumi 등에서 한국어 선호 제목·줄거리·작가·표지를 자동 수집하는 `application.yml`을 포함했습니다.
6. **[OPTIMIZATION] 프로젝트명(`marius-ebook-stack`) 및 컨테이너 네이밍(`ebook-*`) 표준화**
   - **해결**: 시놀로지 Container Manager / Portainer에서 한눈에 그룹핑되도록 `ebook-komga`, `ebook-kavita`, `ebook-audiobookshelf`, `ebook-komf` 등으로 이름을 부여하되, 내부 도커 네트워크 별칭(`aliases`)을 통해 `http://komga:25600`과 `http://ebook-komga:25600` 모두 100% 작동하도록 구성했습니다.
7. **[OPTIMIZATION] 단순 뷰어 4종에서 11종 전자동화 생태계로 확장 + 정기 유지보수 닥터 스크립트 탑재**

---

## 📦 포함된 11종 eBook · 만화 · 웹툰 · 오디오북 생태계 전체 구성

| 번호 | 서비스 | 컨테이너 이름 | 호스트 포트 | 핵심 역할 |
| :--- | :--- | :--- | :---: | :--- |
| 1 | **Komga** | `ebook-komga` | `8341` | 만화·웹툰·잡지(CBZ/CBR/PDF/EPUB) 메인 서버 (G1GC 3GB 최적화) |
| 2 | **Kavita** | `ebook-kavita` | `5471` | 라이트노벨(EPUB)·소설·만화 초고속 하이브리드 웹 리더 |
| 3 | **Audiobookshelf** | `ebook-audiobookshelf` | `13378` | 오디오북(M4B/MP3)·팟캐스트·전자책 스트리밍 & 이어듣기 동기화 |
| 4 | **Komf** | `ebook-komf` | `8085` | Komga & Kavita 만화·웹툰·라노벨 메타데이터/표지 자동 수집 엔진 |
| 5 | **Calibre-Web-Automated** | `ebook-calibre-web` | `8083` | 전자책 자동 EPUB/KEPUB 변환 · 서재 관리 · Kobo 무선 동기화 · Kindle 전송 |
| 6 | **CWA Book Downloader** | `ebook-book-downloader` | `8084` | 웹에서 도서 검색 후 클릭 한 번으로 다운로드 → CWA 자동 변환·등록 포털 |
| 7 | **Suwayomi (Tachidesk)** | `ebook-suwayomi` | `4567` | 연재 만화·웹툰 신규 회차 자동 CBZ 다운로드 → Komga·Kavita 실시간 반영 |
| 8 | **Readarr** | `ebook-readarr` | `8787` | Prowlarr·qBittorrent 연동 신간 전자책·오디오북 자동 수집 매니저 |
| 9 | **Stirling-PDF** | `ebook-stirling-pdf` | `8087` | 스캔된 PDF 책/논문의 한국어(`kor`) OCR 텍스트 인식 & 양면 분할·압축 스튜디오 |
| 10 | **FlareSolverr** | `ebook-flaresolverr` | `8191` | Suwayomi·CWA·Komf 검색 시 Cloudflare 보안 검증 백그라운드 자동 우회 |
| 11 | **Watchtower** | `ebook-watchtower` | Background | 매일 새벽 04:30 최신 컨테이너 무중단 자동 업데이트 및 구버전 이미지 청소 |

---

## 🚀 1단계: 시놀로지 DSM 작업 스케줄러 초기화 & DB 무손실 분리 (`stacks/synology-ebook-init.sh`)

시놀로지 **제어판 → 작업 스케줄러 → 생성 → 예약된 작업 → 사용자 정의 스크립트**에서 사용자 **`root`**를 선택하고 `stacks/synology-ebook-init.sh` 내용을 붙여넣어 1회 실행하세요.
- 모든 설정 폴더 생성, Audiobookshelf 기존 DB의 `/config` 하위 무손실 복사, 통합 마스터 서재(`/volume1/data/ebooks`) 생성, Komf `application.yml` 기본 생성, `1026:100` 권한 부여가 1초 만에 완료됩니다.

---

## 🐳 2단계: Marius 스타일 스택 배포 (`stacks/` 폴더 내 완제품 YAML 3종 제공)

- **`stacks/marius-ebook-ultimate-stack.yml`** : 11종 현존 최고 풀 스택
- **`stacks/marius-ebook-core-stack.yml`** : 핵심 7종 스마트 자동화 스택 (4대장 + CWA + 도서 다운로더 + Suwayomi)
- **`stacks/marius-ebook-fixed-4-stack.yml`** : 기존 업로드하신 4대장(Komga + Kavita + Audiobookshelf + Komf)의 모든 버그만 완벽히 고친 드롭인 교체용 스택
- **`stacks/ebook-maintenance-doctor.sh`** : 매주 일요일 새벽 자동 실행용 **SQLite DB 조각모음(`VACUUM`) · 설정 자동 백업 · 권한 자가치유 닥터 스크립트**

---

## 🖥️ 웹 스튜디오 & 유지보수 컨트롤 센터 셀프 호스팅 실행 방법

```bash
docker run -d \
  --name marius-ebook-stack-studio \
  -p 8500:8500 \
  -e TZ=Asia/Seoul \
  --restart unless-stopped \
  kimmingil/marius-ebook-stack:latest
```

또는 `docker compose up -d`로 즉시 실행할 수 있습니다.

---

## 📄 라이선스
MIT License
