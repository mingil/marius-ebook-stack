"""Marius-Style Ultimate eBook, Manga, Webtoon & Audiobook Stack Catalog & Root-Cause Diagnosis."""

from typing import Any, Dict, List

DIAGNOSIS_REPORT: List[Dict[str, Any]] = [
    {
        "id": "abs-nested-volume",
        "severity": "CRITICAL",
        "severity_label": "치명적 구조 결함 해결",
        "service": "Audiobookshelf",
        "title": "Audiobookshelf 중첩(Nested) 볼륨 마운트로 인한 백업 폭발 및 DB 손상 위험",
        "cause": (
            "기존 compose.yaml에서 상위 폴더 자체인 `/volume1/docker/audiobookshelf:/config:rw`를 마운트하면서, "
            "동시에 그 하위 폴더인 `/volume1/docker/audiobookshelf/audiobooks`와 `/metadata`를 중복 마운트했습니다. "
            "이로 인해 Audiobookshelf가 `/config` 폴더를 스캔하거나 자동 백업할 때 수십~수백 GB의 오디오북과 메타데이터까지 "
            "설정 파일로 오인하여 디스크 I/O 병목 및 백업 실패를 유발합니다."
        ),
        "before_snippet": (
            "volumes:\n"
            "  - /volume1/docker/audiobookshelf:/config:rw\n"
            "  - /volume1/docker/audiobookshelf/audiobooks:/audiobooks:rw\n"
            "  - /volume1/docker/audiobookshelf/metadata:/metadata:rw"
        ),
        "after_snippet": (
            "volumes:\n"
            "  - /volume1/docker/audiobookshelf/config:/config:rw\n"
            "  - /volume1/docker/audiobookshelf/metadata:/metadata:rw\n"
            "  - /volume1/data/ebooks/audiobooks:/audiobooks:rw\n"
            "  - /volume1/data/ebooks/podcasts:/podcasts:rw\n"
            "  - /volume1/docker/audiobookshelf/audiobooks:/legacy-audiobooks:rw"
        ),
        "solution": (
            "`/config` 경로를 `/volume1/docker/audiobookshelf/config`로 완전히 분리하고, 초기화 스크립트(`synology-ebook-init.sh`)가 "
            "기존 상위 폴더에 있던 `absdatabase.sqlite` 등 DB 파일만 안전하게 `config/` 하위로 자동 무손실 이관하도록 조치했습니다."
        ),
    },
    {
        "id": "kavita-abs-permissions",
        "severity": "CRITICAL",
        "severity_label": "시놀로지 권한 충돌 해결",
        "service": "Kavita & Audiobookshelf",
        "title": "Kavita 및 Audiobookshelf 미완성 설정 및 시놀로지 PUID(1026)/PGID(100) 권한 누락",
        "cause": (
            "기존 compose.yaml 주석에 적혀 있듯 Kavita와 Audiobookshelf는 뼈대만 작성된 미완성 상태였으며, "
            "`user: 1026:100` 또는 `PUID=1026`/`PGID=100` 설정이 빠져 있었습니다. 이 상태로 운영하면 컨테이너가 `root` 권한으로 "
            "메타데이터·표지·캐시를 생성하여 시놀로지 DSM File Station에서 파일 수정/이동이 거부되거나 서재 스캔 오류가 발생합니다."
        ),
        "before_snippet": (
            "kavita:\n"
            "  environment:\n"
            "    - TZ=${TZ}  # PUID/PGID 누락\n"
            "audiobookshelf:\n"
            "  # user: 1026:100 누락"
        ),
        "after_snippet": (
            "kavita:\n"
            "  environment:\n"
            "    TZ: ${TZ}\n"
            "    PUID: ${PUID}\n"
            "    PGID: ${PGID}\n"
            "audiobookshelf:\n"
            "  user: \"${PUID}:${PGID}\""
        ),
        "solution": (
            "모든 컨테이너에 시놀로지 표준 사용자 권한(`PUID=1026`, `PGID=100`)과 `security_opt: no-new-privileges:true`를 "
            "Marius Hosting 표준 규격에 맞춰 100% 일관되게 적용했습니다."
        ),
    },
    {
        "id": "komf-race-condition",
        "severity": "HIGH",
        "severity_label": "부팅 순서(Race Condition) 해결",
        "service": "Komf ↔ Komga / Kavita",
        "title": "Komga·Kavita 부팅 완료 전 Komf가 먼저 접속을 시도하여 연결 실패하는 문제",
        "cause": (
            "Komga(Spring Boot)와 Kavita(.NET)는 컨테이너가 시작된 후 실제 웹 서버 포트가 열리기까지 25~60초가 소요됩니다. "
            "기존 설정은 단순 `depends_on`만 걸려 있고 `healthcheck`가 없어서, Komf가 부팅 직후 아직 열리지 않은 Komga/Kavita API에 "
            "접속을 시도하다가 Connection Refused 에러를 내며 재시작(`on-failure:5`) 횟수를 소진할 위험이 있었습니다."
        ),
        "before_snippet": (
            "depends_on:\n"
            "  - komga\n"
            "  - kavita\n"
            "# komga, kavita에 healthcheck 없음"
        ),
        "after_snippet": (
            "depends_on:\n"
            "  komga:\n"
            "    condition: service_healthy\n"
            "  kavita:\n"
            "    condition: service_healthy"
        ),
        "solution": (
            "Komga, Kavita, Audiobookshelf, Komf 등 모든 컨테이너에 정교한 `healthcheck`를 추가하고, "
            "Komf가 반드시 Komga와 Kavita의 상태가 `healthy(정상 응답)`가 된 직후 기동되도록 완벽히 제어했습니다."
        ),
    },
    {
        "id": "storage-fragmentation",
        "severity": "HIGH",
        "severity_label": "스토리지 아키텍처 통합",
        "service": "전체 스토리지 구조",
        "title": "`/volume1/docker` 설정 폴더 내부에 대용량 도서 원본 데이터가 파편화된 문제",
        "cause": (
            "기존에는 `/volume1/docker/komga/data`, `/volume1/docker/kavita/data`, `/volume1/docker/audiobookshelf/audiobooks`처럼 "
            "컨테이너 설정 폴더(`/volume1/docker`) 안에 실제 책·만화 원본 파일을 넣어두었습니다. 이 구조에서는 Komga와 Kavita에서 같은 만화나 "
            "라이트노벨을 볼 때 파일을 중복 복사해야 하며, 설정 폴더 백업 시 수백 GB의 도서 파일까지 묶여 백업이 불가능해집니다."
        ),
        "before_snippet": (
            "komga: /volume1/docker/komga/data:/data:rw\n"
            "kavita: /volume1/docker/kavita/data:/manga:rw\n"
            "abs: /volume1/docker/audiobookshelf/audiobooks:/audiobooks:rw"
        ),
        "after_snippet": (
            "# 기존 서재 100% 무손실 호환 마운트 유지 + 신규 통합 마스터 볼륨(/data) 동시 연결\n"
            "- /volume1/data/ebooks:/data:rw\n"
            "- /volume1/docker/komga/data:/legacy-data:rw"
        ),
        "solution": (
            "기존 서재 경로(`/volume1/docker/.../data`)를 그대로 유지해 기존 등록된 책과 독서 기록이 단 1권도 깨지지 않게 보호하면서, "
            "동시에 모든 컨테이너가 `/volume1/data/ebooks:/data:rw` 단일 마스터 볼륨을 공유하도록 설계하여 하드링크와 무중단 통합을 달성했습니다."
        ),
    },
    {
        "id": "komf-application-yml",
        "severity": "HIGH",
        "severity_label": "메타데이터 자동화 완성",
        "service": "Komf (Metadata Engine)",
        "title": "Komf 상세 메타데이터 프로바이더 설정 파일(`application.yml`) 및 웹훅 연동 부재",
        "cause": (
            "Komf는 도커 환경변수만으로 실행하면 기본 연결만 될 뿐, 어떤 메타데이터 사이트(AniList, MangaUpdates, MyAnimeList, Bangumi, "
            "ComicVine 등)에서 한국어/영어 제목·줄거리·작가·장르 태그·표지를 가져올지 정의된 `/config/application.yml`이 없으면 제 기능을 못 합니다."
        ),
        "before_snippet": (
            "environment:\n"
            "  - KOMF_KOMGA_BASE_URI=http://komga:25600\n"
            "  - KOMF_KAVITA_BASE_URI=http://kavita:5000\n"
            "# application.yml 상세 프로바이더 설정 없음"
        ),
        "after_snippet": (
            "# /volume1/docker/komf/config/application.yml 자동 생성\n"
            "# Komga & Kavita 실시간 이벤트 리스너 + 한국어 선호 타이틀 매칭 탑재"
        ),
        "solution": (
            "Komga와 Kavita 양쪽의 신규 책 추가 이벤트를 실시간 감지해 자동으로 메타데이터와 고화질 표지를 입혀주는 "
            "한국어 최적화 `application.yml` 설정 파일과 브라우저 내장 원클릭 매칭 유저스크립트 가이드를 함께 구성했습니다."
        ),
    },
    {
        "id": "naming-and-dns",
        "severity": "OPTIMIZATION",
        "severity_label": "네이밍 & DNS 표준화",
        "service": "프로젝트 & 컨테이너 이름",
        "title": "폴더명(`ebook-library`) 및 대소문자 혼용 컨테이너명(`Komga`, `Kavita`) 표준화",
        "cause": (
            "기존 컨테이너 이름이 대문자(`Komga`, `Komf`, `Kavita`, `Audiobookshelf`)로 되어 있어 다른 스택 컨테이너들과 섞였을 때 "
            "구분이 어렵고, 일부 리눅스/도커 DNS 환경에서 대소문자 호스트네임 혼선을 유발할 수 있습니다."
        ),
        "before_snippet": (
            "폴더명: /config/workspace/projects/ebook-library\n"
            "컨테이너명: Komga, Komf, Kavita, Audiobookshelf"
        ),
        "after_snippet": (
            "폴더명: /config/workspace/projects/marius-ebook-stack\n"
            "컨테이너명: ebook-komga, ebook-kavita, ebook-audiobookshelf, ebook-komf ...\n"
            "내부 DNS 별칭: komga, kavita, audiobookshelf, komf 양방향 100% 호환"
        ),
        "solution": (
            "미디어 스택(`marius-arr-stack`)과 짝을 이루는 **`marius-ebook-stack`**으로 프로젝트명을 부여하고, "
            "컨테이너 이름은 `ebook-*` 프리픽스로 깔끔하게 정렬하되 내부 도커 네트워크 별칭(`aliases`)을 통해 `http://komga:25600`과 "
            "`http://ebook-komga:25600` 모두 완벽히 작동하도록 구성했습니다."
        ),
    },
    {
        "id": "ecosystem-expansion",
        "severity": "OPTIMIZATION",
        "severity_label": "현존 최고 11종 생태계 완성",
        "service": "eBook 자동 수집·변환·유지보수",
        "title": "단순 뷰어 4종을 넘어 '검색 → 다운로드 → EPUB 자동 변환 → 웹툰 연재 수집 → PDF OCR' 전자동화 구축",
        "cause": (
            "Komga·Kavita·Audiobookshelf·Komf 4종은 훌륭한 '열람 및 메타데이터 서버'이지만, 새로운 책을 검색해 원클릭으로 다운로드하거나, "
            "연재 웹툰/만화를 자동 수집하고, MOBI/AZW3/TXT를 EPUB으로 자동 변환해 Kobo/Kindle로 쏴주는 자동화 파이프라인이 없었습니다."
        ),
        "before_snippet": "Komga + Kavita + Audiobookshelf + Komf (4종 수동 파일 넣기 구조)",
        "after_snippet": (
            "4대장 + Calibre-Web-Automated(자동 변환·Kobo/Kindle 동기화) + CWA-Book-Downloader(웹 도서 원클릭 다운로드) "
            "+ Suwayomi(웹툰/만화 연재 자동 다운로드) + Stirling-PDF(한국어 OCR) + Readarr + FlareSolverr + Watchtower (총 11종)"
        ),
        "solution": (
            "원클릭 도서 요청부터 자동 포맷 변환, 웹툰 자동 수집, 스캔 PDF 한국어 OCR, 그리고 매주 SQLite DB를 최적화(VACUUM)하고 "
            "설정을 백업하는 유지보수 닥터 스크립트(`ebook-maintenance-doctor.sh`)까지 현존 최고의 완벽한 환경을 완성했습니다."
        ),
    },
]


EBOOK_SERVICES_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "komga",
        "name": "Komga",
        "container_name": "ebook-komga",
        "hostname": "komga",
        "category": "core_server",
        "essential": True,
        "default_enabled": True,
        "image": "gotson/komga:latest",
        "port": 8341,
        "internal_port": 25600,
        "webui_port": 8341,
        "webui_path": "",
        "description": "만화·웹툰·잡지(CBZ/CBR/PDF/EPUB) 전용 최고급 미디어 서버. 스마트 컬렉션, 읽기 목록, OPDS 스트리밍, Mihon(Tachiyomi)·Panels·Tachimanga 앱 완벽 연동을 지원합니다.",
        "marius_notes": "기존 포트(8341:25600)와 G1GC 메모리 튜닝(-Xmx3g -XX:+UseG1GC)을 그대로 계승하고, Spring Actuator 헬스체크 및 통합 /data 볼륨을 추가했습니다.",
        "role_badge": "만화·웹툰 메인 서버",
        "config_dir": "komga",
        "tuning_badge": "G1GC + Max 3GB RAM + Healthcheck",
    },
    {
        "id": "kavita",
        "name": "Kavita",
        "container_name": "ebook-kavita",
        "hostname": "kavita",
        "category": "core_server",
        "essential": True,
        "default_enabled": True,
        "image": "jvmilazz0/kavita:latest",
        "port": 5471,
        "internal_port": 5000,
        "webui_port": 5471,
        "webui_path": "",
        "description": "라이트노벨(EPUB)·일반 소설·단행본·만화를 아우르는 초고속 하이브리드 전자책 리더. 브라우저 내장 EPUB 웹 리더의 가독성과 커스터마이징(폰트/여백/테마)이 현존 최고 수준입니다.",
        "marius_notes": "기존에 누락되었던 시놀로지 PUID=1026/PGID=100 권한과 헬스체크를 완비했으며, 기존 /manga 경로와 신규 통합 /data 경로를 동시에 마운트합니다.",
        "role_badge": "라이트노벨·EPUB·만화 하이브리드 서버",
        "config_dir": "kavita",
        "tuning_badge": "PUID/PGID 1026:100 + .NET GC 최적화",
    },
    {
        "id": "audiobookshelf",
        "name": "Audiobookshelf",
        "container_name": "ebook-audiobookshelf",
        "hostname": "audiobookshelf",
        "category": "core_server",
        "essential": True,
        "default_enabled": True,
        "image": "advplyr/audiobookshelf:latest",
        "port": 13378,
        "internal_port": 80,
        "webui_port": 13378,
        "webui_path": "",
        "description": "오디오북(M4B/MP3/FLAC), 팟캐스트 자동 구독·다운로드, 전자책(EPUB) 통합 스트리밍 서버. 기기 간 초 단위 재생 위치 동기화 및 오디오북 메타데이터/챕터 자동 매칭을 제공합니다.",
        "marius_notes": "치명적이었던 중첩 볼륨(/volume1/docker/audiobookshelf:/config) 버그를 /config 하위 폴더 분리로 완벽 해결하고 user: 1026:100 권한을 적용했습니다.",
        "role_badge": "오디오북·팟캐스트·소설 스트리밍",
        "config_dir": "audiobookshelf",
        "tuning_badge": "중첩 볼륨 분리 완료 + PUID 1026",
    },
    {
        "id": "komf",
        "name": "Komf (Metadata Engine)",
        "container_name": "ebook-komf",
        "hostname": "komf",
        "category": "metadata",
        "essential": True,
        "default_enabled": True,
        "image": "sndxr/komf:latest",
        "port": 8085,
        "internal_port": 8085,
        "webui_port": 8085,
        "webui_path": "",
        "description": "Komga와 Kavita 양쪽에 동시에 연결되어 만화·웹툰·라이트노벨의 제목, 줄거리, 작가, 장르 태그, 고화질 표지를 AniList·MangaUpdates·MAL·Bangumi 등에서 자동으로 수집해 입혀주는 엔진입니다.",
        "marius_notes": "ShenandoahGC 초저메모리 튜닝(-Xmx512m)을 유지하고, Komga/Kavita가 완전히 부팅(service_healthy)된 후 기동되도록 수정했으며, 전용 application.yml을 자동 생성합니다.",
        "role_badge": "Komga·Kavita 메타데이터 자동화",
        "config_dir": "komf",
        "tuning_badge": "ShenandoahGC 512MB + Healthy 대기",
    },
    {
        "id": "calibre-web-automated",
        "name": "Calibre-Web-Automated (CWA)",
        "container_name": "ebook-calibre-web",
        "hostname": "calibre-web-automated",
        "category": "core_server",
        "essential": True,
        "default_enabled": True,
        "image": "crocodilestick/calibre-web-automated:latest",
        "port": 8083,
        "internal_port": 8083,
        "webui_port": 8083,
        "webui_path": "",
        "description": "무거운 데스크톱 Calibre를 대체하는 현존 최고의 차세대 전자책 자동 관리 서버. /cwa-book-ingest 폴더에 어떤 포맷(MOBI/AZW3/TXT/PDF/EPUB)의 책을 넣든 자동으로 EPUB 변환·메타데이터 교정·서재 등록을 수행하며, Kobo 무선 동기화 및 Send-to-Kindle을 지원합니다.",
        "marius_notes": "CWA-Book-Downloader와 /cwa-book-ingest 폴더를 공유하여, 웹에서 책을 다운로드하면 10초 안에 자동으로 변환되어 Calibre 서재 및 Kavita/ABS에 공유됩니다.",
        "role_badge": "전자책 자동 변환 & Kobo/Kindle 서버",
        "config_dir": "calibre-web-automated",
        "tuning_badge": "Auto-Ingest + Kepubify 내장",
    },
    {
        "id": "cwa-book-downloader",
        "name": "CWA Book Downloader",
        "container_name": "ebook-book-downloader",
        "hostname": "cwa-book-downloader",
        "category": "automation",
        "essential": False,
        "default_enabled": True,
        "image": "ghcr.io/calibre-web-automated-book-downloader/calibre-web-automated-book-downloader:latest",
        "port": 8084,
        "internal_port": 8084,
        "webui_port": 8084,
        "webui_path": "",
        "description": "영화/드라마의 Seerr(Overseerr)와 같은 역할을 하는 도서 검색·원클릭 다운로드 웹 포털. 원하는 책 제목·저자·ISBN을 검색해 다운로드 버튼만 누르면 Calibre-Web-Automated 인제스트 폴더로 자동 투입되어 서재에 즉시 등록됩니다.",
        "marius_notes": "FlareSolverr(http://flaresolverr:8191)와 연동되어 Cloudflare 보호 사이트에서도 끊김 없이 도서를 검색·수집합니다.",
        "role_badge": "원클릭 도서 검색·자동 다운로드 포털",
        "config_dir": "cwa-book-downloader",
        "tuning_badge": "CWA 인제스트 직결 파이프라인",
    },
    {
        "id": "suwayomi",
        "name": "Suwayomi-Server (Tachidesk)",
        "container_name": "ebook-suwayomi",
        "hostname": "suwayomi",
        "category": "automation",
        "essential": False,
        "default_enabled": True,
        "image": "ghcr.io/suwayomi/tachidesk:latest",
        "port": 4567,
        "internal_port": 4567,
        "webui_port": 4567,
        "webui_path": "",
        "description": "안드로이드 최강 만화 앱 Mihon(구 Tachiyomi)의 확장 프로그램 생태계를 시놀로지 도커 서버로 구현한 연재 만화·웹툰 자동 수집기. 연재작의 새 회차가 올라오면 자동으로 CBZ 압축 파일로 다운로드하여 Komga와 Kavita 서재에 실시간으로 넣어줍니다.",
        "marius_notes": "다운로드 저장 경로가 /data/manga 로 연결되어 있어, Suwayomi가 받은 만화를 Komga와 Kavita가 복사 없이 즉시 스캔하고 Komf가 메타데이터를 입힙니다.",
        "role_badge": "웹툰·만화 신규 회차 자동 수집 서버",
        "config_dir": "suwayomi",
        "tuning_badge": "CBZ 자동 패키징 → Komga 직결",
    },
    {
        "id": "readarr",
        "name": "Readarr",
        "container_name": "ebook-readarr",
        "hostname": "readarr",
        "category": "automation",
        "essential": False,
        "default_enabled": True,
        "image": "lscr.io/linuxserver/readarr:develop",
        "port": 8787,
        "internal_port": 8787,
        "webui_port": 8787,
        "webui_path": "",
        "description": "*Arr 패밀리(Sonarr/Radarr)의 전자책·오디오북 전담 자동화 매니저. 기존 구축하신 Prowlarr 및 qBittorrent와 연동하여 관심 작가의 신간 전자책이나 오디오북이 릴리즈되면 자동으로 다운로드하고 서재 폴더로 하드링크 정리합니다.",
        "marius_notes": "marius-arr-stack의 Prowlarr(9696) 및 qBittorrent(8080)와 연동하면 토렌트/유즈넷 기반 도서·오디오북 수집이 100% 자동화됩니다.",
        "role_badge": "*Arr 전자책·오디오북 자동 수집",
        "config_dir": "readarr",
        "tuning_badge": "Prowlarr & Hardlink 호환",
    },
    {
        "id": "stirling-pdf",
        "name": "Stirling-PDF",
        "container_name": "ebook-stirling-pdf",
        "hostname": "stirling-pdf",
        "category": "utility",
        "essential": False,
        "default_enabled": True,
        "image": "frooodle/s-pdf:latest",
        "port": 8087,
        "internal_port": 8080,
        "webui_port": 8087,
        "webui_path": "",
        "description": "스캔된 PDF 전공서적·논문·매거진을 위한 올인원 웹 PDF 가공 스튜디오. 한국어(kor)+영어(eng) 광학문자인식(OCR)을 통해 이미지 스캔본 PDF를 텍스트 검색·하이라이트가 가능한 PDF로 변환하고, 양면 스캔 페이지 분할·압축·EPUB 변환까지 지원합니다.",
        "marius_notes": "시놀로지 NAS에서 무거운 Adobe Acrobat 없이 브라우저에서 모든 PDF 전자책 가공과 한국어 OCR을 처리할 수 있습니다.",
        "role_badge": "스캔북 한국어 OCR & PDF 스튜디오",
        "config_dir": "stirling-pdf",
        "tuning_badge": "한국어(kor) Tesseract OCR 지원",
    },
    {
        "id": "flaresolverr",
        "name": "FlareSolverr",
        "container_name": "ebook-flaresolverr",
        "hostname": "flaresolverr",
        "category": "utility",
        "essential": False,
        "default_enabled": True,
        "image": "ghcr.io/flaresolverr/flaresolverr:latest",
        "port": 8191,
        "internal_port": 8191,
        "webui_port": 8191,
        "webui_path": "",
        "description": "Suwayomi, CWA-Book-Downloader, Komf, Readarr가 외부 도서·웹툰 소스나 메타데이터 사이트에 접근할 때 발생하는 Cloudflare 보안 검증을 백그라운드에서 자동 통과시켜 줍니다.",
        "marius_notes": "내부 도커 주소 http://flaresolverr:8191 로 Suwayomi, CWA-Book-Downloader, Prowlarr에 연결하면 검색 실패가 사라집니다.",
        "role_badge": "Cloudflare 자동 우회 프록시",
        "config_dir": "flaresolverr",
        "tuning_badge": "Headless Chromium 프록시",
    },
    {
        "id": "watchtower",
        "name": "Watchtower",
        "container_name": "ebook-watchtower",
        "hostname": "ebook-watchtower",
        "category": "utility",
        "essential": False,
        "default_enabled": True,
        "image": "containrrr/watchtower:latest",
        "port": None,
        "internal_port": None,
        "webui_port": None,
        "webui_path": None,
        "description": "매일 새벽 4시 30분에 eBook 스택 컨테이너들의 최신 도커 이미지가 출시되었는지 확인하고, 무중단으로 자동 업데이트한 뒤 구버전 이미지를 깨끗하게 삭제(CLEANUP)하여 시놀로지 용량을 보호합니다.",
        "marius_notes": "WATCHTOWER_CLEANUP=true 및 크론 스케줄(0 30 4 * * *)이 기본 적용되어 관리자가 신경 쓰지 않아도 항상 최신 보안·기능 패치를 유지합니다.",
        "role_badge": "새벽 무중단 자동 업데이트",
        "config_dir": None,
        "tuning_badge": "매일 04:30 자동 업데이트 & 이미지 청소",
    },
]


CLIENT_APPS_GUIDE: List[Dict[str, Any]] = [
    {
        "category": "만화 · 웹툰 (Komga & Kavita 연동)",
        "icon": "fa-book-open-reader",
        "clients": [
            {
                "device": "iOS / iPadOS (아이폰·아이패드)",
                "apps": "Panels (최고 추천), Paperback, Tachimanga",
                "connection": "OPDS 또는 Komga 전용 API 연동",
                "url_template": "http://{nas_ip}:{komga_port}/opds/v1.2/catalog",
                "tip": "아이패드에서는 Panels 앱에 Komga 서버를 OPDS/API로 등록하면 양면 보기, 세로 스크롤(웹툰), 읽기 진도 동기화가 완벽하게 작동합니다.",
            },
            {
                "device": "Android (갤럭시 탭·스마트폰·오닉스 북스)",
                "apps": "Mihon (구 Tachiyomi), Komga 확장 프로그램",
                "connection": "Mihon 내 Komga / Kavita 확장 설치 후 서버 URL 입력",
                "url_template": "http://{nas_ip}:{komga_port}",
                "tip": "Mihon 앱에서 Komga 확장을 설치하면 NAS의 수만 권 만화를 앱 내장 서재처럼 초고속으로 열람하고 읽기 상태가 양방향 동기화됩니다.",
            },
        ],
    },
    {
        "category": "전자책 · 소설 · 라이트노벨 (Kavita & Calibre-Web-Automated 연동)",
        "icon": "fa-tablet-screen-button",
        "clients": [
            {
                "device": "PC / 태블릿 / 모바일 웹 브라우저",
                "apps": "Kavita 내장 웹 리더 & CWA 내장 웹 리더",
                "connection": "별도 앱 설치 없이 브라우저 직접 접속 (PWA 홈 화면 추가 지원)",
                "url_template": "http://{nas_ip}:{kavita_port}",
                "tip": "Kavita의 내장 EPUB 리더는 나눔명조/리디바탕 웹폰트, 줄간격, 여백, 다크모드 설정이 현존 최고 수준이라 별도 앱 없이도 완벽합니다.",
            },
            {
                "device": "이북 리더기 (Kobo / Kindle / 크레마 / 오닉스)",
                "apps": "Kobo 무선 동기화 (CWA) / Send-to-Kindle / KOReader (OPDS)",
                "connection": "Calibre-Web-Automated Kobo Sync 토큰 또는 OPDS 주소 등록",
                "url_template": "http://{nas_ip}:{cwa_port}/opds",
                "tip": "Calibre-Web-Automated는 책을 넣는 즉시 Kobo 전용 포맷(KEPUB)으로 자동 변환하여 Kobo 리더기에서 상점 동기화만 누르면 무선으로 책이 들어옵니다.",
            },
        ],
    },
    {
        "category": "오디오북 · 팟캐스트 (Audiobookshelf 연동)",
        "icon": "fa-headphones-simple",
        "clients": [
            {
                "device": "iOS (아이폰·애플워치·CarPlay)",
                "apps": "Plappa (CarPlay·오프라인 최고 추천), ShelfPlayer, Audiobookshelf 공식 베타(TestFlight)",
                "connection": "Audiobookshelf 서버 주소 및 계정 로그인",
                "url_template": "http://{nas_ip}:{abs_port}",
                "tip": "아이폰에서는 Plappa 또는 ShelfPlayer 앱을 연결하면 애플 카플레이(CarPlay)와 애플워치 연동, 수면 타이머, 초 단위 이어듣기가 완벽히 지원됩니다.",
            },
            {
                "device": "Android (안드로이드 스마트폰·Android Auto)",
                "apps": "Audiobookshelf 공식 앱 (Google Play 스토어)",
                "connection": "Audiobookshelf 서버 주소 및 계정 로그인",
                "url_template": "http://{nas_ip}:{abs_port}",
                "tip": "오디오북과 동일한 책의 EPUB 파일을 같은 폴더에 넣어두면, 차 안에서는 오디오북으로 듣고 집에서는 이북으로 이어 읽는 하이브리드 독서가 가능합니다.",
            },
        ],
    },
]
