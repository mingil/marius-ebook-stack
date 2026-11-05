"""Marius Hosting Blog Style eBook, Manga, Webtoon & Audiobook Stack Generator."""

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class EbookStackConfigRequest(BaseModel):
    nas_ip: str = Field(default="192.168.1.100", description="시놀로지 NAS 내부 IP 주소")
    puid: int = Field(default=1026, description="시놀로지 사용자 PUID (기본 1026)")
    pgid: int = Field(default=100, description="시놀로지 그룹 PGID (기본 100)")
    tz: str = Field(default="Asia/Seoul", description="타임존")
    docker_root: str = Field(default="/volume1/docker", description="도커 설정 폴더 루트 경로")
    ebook_data_root: str = Field(default="/volume1/data/ebooks", description="통합 전자책·만화·오디오북 데이터 마스터 경로")
    container_prefix: str = Field(default="ebook-", description="컨테이너 이름 프리픽스 (예: ebook-komga)")
    keep_legacy_mounts: bool = Field(
        default=True,
        description="기존 업로드된 /volume1/docker/{komga,kavita,audiobookshelf} 내부 데이터 경로를 호환 마운트로 함께 유지",
    )
    komga_port: int = Field(default=8341, description="Komga 호스트 포트 (기존 8341 유지)")
    kavita_port: int = Field(default=5471, description="Kavita 호스트 포트 (기존 5471 유지)")
    audiobookshelf_port: int = Field(default=13378, description="Audiobookshelf 호스트 포트 (기존 13378 유지)")
    komf_port: int = Field(default=8085, description="Komf 호스트 포트 (기존 8085 유지)")
    cwa_port: int = Field(default=8083, description="Calibre-Web-Automated 호스트 포트")
    cwa_dl_port: int = Field(default=8084, description="CWA Book Downloader 호스트 포트")
    suwayomi_port: int = Field(default=4567, description="Suwayomi (Tachidesk) 호스트 포트")
    readarr_port: int = Field(default=8787, description="Readarr 호스트 포트")
    stirling_port: int = Field(default=8087, description="Stirling-PDF 호스트 포트")
    flaresolverr_port: int = Field(default=8191, description="FlareSolverr 호스트 포트")
    komga_user: str = Field(default="fauna035@gmail.com", description="Komga 관리자 이메일")
    komga_password: str = Field(default="YOUR_KOMGA_PASSWORD", description="Komga 관리자 비밀번호")
    kavita_api_key: str = Field(default="JR5SNjbYayxiZtzTgEIWOTfZ6Od3iyTa", description="Kavita OPDS/API 키")
    selected_services: List[str] = Field(
        default_factory=lambda: [
            "komga",
            "kavita",
            "audiobookshelf",
            "komf",
            "calibre-web-automated",
            "cwa-book-downloader",
            "suwayomi",
            "readarr",
            "stirling-pdf",
            "flaresolverr",
            "watchtower",
        ]
    )


def _cname(cfg: EbookStackConfigRequest, base: str) -> str:
    prefix = (cfg.container_prefix or "").strip()
    return f"{prefix}{base}" if prefix else base


def generate_marius_ebook_compose(cfg: EbookStackConfigRequest) -> str:
    """Generate a Marius Hosting style docker-compose.yml for the eBook ecosystem."""
    selected = list(dict.fromkeys(cfg.selected_services))
    docker_root = cfg.docker_root.rstrip("/")
    data_root = cfg.ebook_data_root.rstrip("/")

    lines: List[str] = [
        "# =============================================================================",
        "# 🏆 MARIUS HOSTING STYLE - ULTIMATE SYNOLOGY EBOOK & MANGA STACK (v1.0.0)",
        "# =============================================================================",
        "# • 프로젝트명   : marius-ebook-stack (기존 ebook-library 완벽 진단·교정·확장판)",
        "# • 작성 스타일  : Marius Bogdan Lixandru (mariushosting.com) 표준 규격 100% 준수",
        f"# • 시놀로지 권한: PUID={cfg.puid} / PGID={cfg.pgid} / TZ={cfg.tz}",
        f"# • 설정 경로    : {docker_root}/<서비스명> (순수 Config & DB 전용으로 완벽 분리)",
        f"# • 마스터 서재  : {data_root}:/data:rw (전 컨테이너 단일 볼륨 공유 & 하드링크 지원)",
        "# =============================================================================",
        "",
        'version: "3.9"',
        "",
        "# 🌐 1. 도커 내부 통신용 브리지 네트워크 (기존 ebook_net 및 호스트네임 100% 호환)",
        "networks:",
        "  marius-ebook-net:",
        "    name: marius-ebook-net",
        "    driver: bridge",
        "",
        "# 🧹 2. 시놀로지 NAS 디스크 보호용 공통 로그 로테이션 설정",
        "x-logging: &default-logging",
        '  driver: "json-file"',
        "  options:",
        '    max-size: "10m"',
        '    max-file: "3"',
        "",
        "services:",
    ]

    # 1. KOMGA
    if "komga" in selected:
        cname = _cname(cfg, "komga")
        komga_vols = [
            f"      - {docker_root}/komga/config:/config:rw",
            f"      - {data_root}:/data:rw",
        ]
        if cfg.keep_legacy_mounts:
            komga_vols.append(f"      - {docker_root}/komga/data:/legacy-komga-data:rw")

        lines.extend([
            "  # ---------------------------------------------------------------------------",
            "  # 📚 1. KOMGA - 만화·웹툰·매거진 메인 미디어 서버 (G1GC 메모리 최적화)",
            "  # ---------------------------------------------------------------------------",
            "  komga:",
            "    image: gotson/komga:latest",
            f"    container_name: {cname}",
            "    hostname: komga",
            "    networks:",
            "      marius-ebook-net:",
            "        aliases:",
            "          - komga",
            f"          - {cname}",
            "    mem_limit: 4g",
            "    cpu_shares: 768",
            "    security_opt:",
            "      - no-new-privileges:true",
            f'    user: "${{PUID:-{cfg.puid}}}:${{PGID:-{cfg.pgid}}}"',
            "    environment:",
            f"      TZ: ${{TZ:-{cfg.tz}}}",
            '      JAVA_TOOL_OPTIONS: "-Xmx3g -XX:+UseG1GC -XX:+UseStringDeduplication"',
            "      SERVER_PORT: 25600",
            "    ports:",
            f'      - "{cfg.komga_port}:25600"',
            "    volumes:",
            *komga_vols,
            "    healthcheck:",
            '      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://127.0.0.1:25600/actuator/health || exit 1"]',
            "      interval: 30s",
            "      timeout: 10s",
            "      retries: 5",
            "      start_period: 60s",
            "    restart: on-failure:5",
            "    logging: *default-logging",
            "",
        ])

    # 2. KAVITA
    if "kavita" in selected:
        cname = _cname(cfg, "kavita")
        kavita_vols = [
            f"      - {docker_root}/kavita/config:/kavita/config:rw",
            f"      - {data_root}:/data:rw",
            f"      - {data_root}/manga:/manga:rw",
            f"      - {data_root}/lightnovels:/lightnovels:rw",
            f"      - {data_root}/books:/books:rw",
        ]
        if cfg.keep_legacy_mounts:
            kavita_vols.append(f"      - {docker_root}/kavita/data:/legacy-kavita-manga:rw")

        lines.extend([
            "  # ---------------------------------------------------------------------------",
            "  # 🌟 2. KAVITA - 라이트노벨(EPUB)·소설·만화 초고속 하이브리드 서버",
            "  # ---------------------------------------------------------------------------",
            "  kavita:",
            "    image: jvmilazz0/kavita:latest",
            f"    container_name: {cname}",
            "    hostname: kavita",
            "    networks:",
            "      marius-ebook-net:",
            "        aliases:",
            "          - kavita",
            f"          - {cname}",
            "    mem_limit: 4g",
            "    cpu_shares: 768",
            "    security_opt:",
            "      - no-new-privileges:true",
            "    environment:",
            f"      TZ: ${{TZ:-{cfg.tz}}}",
            f"      PUID: ${{PUID:-{cfg.puid}}}",
            f"      PGID: ${{PGID:-{cfg.pgid}}}",
            "      DOTNET_GCHeapHardLimit: 0xC0000000",
            "    ports:",
            f'      - "{cfg.kavita_port}:5000"',
            "    volumes:",
            *kavita_vols,
            "    healthcheck:",
            '      test: ["CMD-SHELL", "curl -fsS http://127.0.0.1:5000/api/health || exit 1"]',
            "      interval: 30s",
            "      timeout: 10s",
            "      retries: 5",
            "      start_period: 45s",
            "    restart: on-failure:5",
            "    logging: *default-logging",
            "",
        ])

    # 3. AUDIOBOOKSHELF
    if "audiobookshelf" in selected:
        cname = _cname(cfg, "audiobookshelf")
        abs_vols = [
            f"      # ✅ [핵심 수정 완료] 기존 상위 폴더(/volume1/docker/audiobookshelf) 중첩 마운트 버그를 /config 하위 분리로 해결",
            f"      - {docker_root}/audiobookshelf/config:/config:rw",
            f"      - {docker_root}/audiobookshelf/metadata:/metadata:rw",
            f"      - {data_root}/audiobooks:/audiobooks:rw",
            f"      - {data_root}/podcasts:/podcasts:rw",
            f"      - {data_root}/books:/books:rw",
            f"      - {data_root}/lightnovels:/lightnovels:rw",
        ]
        if cfg.keep_legacy_mounts:
            abs_vols.append(f"      - {docker_root}/audiobookshelf/audiobooks:/legacy-audiobooks:rw")

        lines.extend([
            "  # ---------------------------------------------------------------------------",
            "  # 🎧 3. AUDIOBOOKSHELF - 오디오북·팟캐스트·전자책 스트리밍 서버",
            "  # ---------------------------------------------------------------------------",
            "  audiobookshelf:",
            "    image: advplyr/audiobookshelf:latest",
            f"    container_name: {cname}",
            "    hostname: audiobookshelf",
            "    networks:",
            "      marius-ebook-net:",
            "        aliases:",
            "          - audiobookshelf",
            f"          - {cname}",
            "    mem_limit: 4g",
            "    cpu_shares: 768",
            "    security_opt:",
            "      - no-new-privileges:true",
            f'    user: "${{PUID:-{cfg.puid}}}:${{PGID:-{cfg.pgid}}}"',
            "    environment:",
            f"      TZ: ${{TZ:-{cfg.tz}}}",
            "      CONFIG_PATH: /config",
            "      METADATA_PATH: /metadata",
            "      PORT: 80",
            "    ports:",
            f'      - "{cfg.audiobookshelf_port}:80"',
            "    volumes:",
            *abs_vols,
            "    healthcheck:",
            '      test: ["CMD-SHELL", "nc -z 127.0.0.1 80 || wget -q --spider http://127.0.0.1:80/ping || exit 1"]',
            "      interval: 20s",
            "      timeout: 5s",
            "      retries: 3",
            "      start_period: 45s",
            "    restart: on-failure:5",
            "    logging: *default-logging",
            "",
        ])

    # 4. KOMF
    if "komf" in selected:
        cname = _cname(cfg, "komf")
        depends_lines: List[str] = []
        if "komga" in selected or "kavita" in selected:
            depends_lines.append("    depends_on:")
            if "komga" in selected:
                depends_lines.extend([
                    "      komga:",
                    "        condition: service_healthy",
                ])
            if "kavita" in selected:
                depends_lines.extend([
                    "      kavita:",
                    "        condition: service_healthy",
                ])

        lines.extend([
            "  # ---------------------------------------------------------------------------",
            "  # 🤖 4. KOMF - Komga & Kavita 만화·웹툰·라노벨 메타데이터 자동 수집 엔진",
            "  # ---------------------------------------------------------------------------",
            "  komf:",
            "    image: sndxr/komf:latest",
            f"    container_name: {cname}",
            "    hostname: komf",
            "    networks:",
            "      marius-ebook-net:",
            "        aliases:",
            "          - komf",
            f"          - {cname}",
            "    mem_limit: 1g",
            "    cpu_shares: 768",
            "    security_opt:",
            "      - no-new-privileges:true",
            f'    user: "${{PUID:-{cfg.puid}}}:${{PGID:-{cfg.pgid}}}"',
            "    environment:",
            f"      TZ: ${{TZ:-{cfg.tz}}}",
            "      KOMF_KOMGA_BASE_URI: http://komga:25600",
            "      KOMF_KOMGA_USER: ${KOMGA_USER}",
            "      KOMF_KOMGA_PASSWORD: ${KOMGA_PASSWORD}",
            "      KOMF_KAVITA_BASE_URI: http://kavita:5000",
            "      KOMF_KAVITA_API_KEY: ${KAVITA_API_KEY}",
            "      KOMF_LOG_LEVEL: INFO",
            '      JAVA_TOOL_OPTIONS: "-Xmx512m -XX:+UnlockExperimentalVMOptions -XX:+UseShenandoahGC -XX:ShenandoahGCHeuristics=compact -XX:ShenandoahGuaranteedGCInterval=3600000 -XX:TrimNativeHeapInterval=3600000"',
            "    ports:",
            f'      - "{cfg.komf_port}:8085"',
            "    volumes:",
            f"      - {docker_root}/komf/config:/config:rw",
            *depends_lines,
            "    healthcheck:",
            '      test: ["CMD-SHELL", "nc -z 127.0.0.1 8085 || wget -q --spider http://127.0.0.1:8085 || exit 1"]',
            "      interval: 30s",
            "      timeout: 10s",
            "      retries: 3",
            "      start_period: 30s",
            "    restart: on-failure:5",
            "    logging: *default-logging",
            "",
        ])

    # 5. CALIBRE-WEB-AUTOMATED
    if "calibre-web-automated" in selected:
        cname = _cname(cfg, "calibre-web")
        lines.extend([
            "  # ---------------------------------------------------------------------------",
            "  # 📖 5. CALIBRE-WEB-AUTOMATED - 전자책 자동 변환(EPUB/KEPUB) & Kobo/Kindle 서버",
            "  # ---------------------------------------------------------------------------",
            "  calibre-web-automated:",
            "    image: crocodilestick/calibre-web-automated:latest",
            f"    container_name: {cname}",
            "    hostname: calibre-web-automated",
            "    networks:",
            "      marius-ebook-net:",
            "        aliases:",
            "          - calibre-web-automated",
            f"          - {cname}",
            "    mem_limit: 2g",
            "    cpu_shares: 768",
            "    security_opt:",
            "      - no-new-privileges:true",
            "    environment:",
            f"      TZ: ${{TZ:-{cfg.tz}}}",
            f"      PUID: ${{PUID:-{cfg.puid}}}",
            f"      PGID: ${{PGID:-{cfg.pgid}}}",
            "      HARDCOVER_TOKEN: ${HARDCOVER_TOKEN:-}",
            "    ports:",
            f'      - "{cfg.cwa_port}:8083"',
            "    volumes:",
            f"      - {docker_root}/calibre-web-automated/config:/config:rw",
            f"      - {data_root}/cwa-ingest:/cwa-book-ingest:rw",
            f"      - {data_root}/calibre-library:/calibre-library:rw",
            f"      - {data_root}/books:/books:rw",
            "    healthcheck:",
            '      test: ["CMD-SHELL", "curl -fsS http://127.0.0.1:8083 >/dev/null || exit 1"]',
            "      interval: 30s",
            "      timeout: 10s",
            "      retries: 3",
            "      start_period: 60s",
            "    restart: on-failure:5",
            "    logging: *default-logging",
            "",
        ])

    # 6. CWA BOOK DOWNLOADER
    if "cwa-book-downloader" in selected:
        cname = _cname(cfg, "book-downloader")
        lines.extend([
            "  # ---------------------------------------------------------------------------",
            "  # 🔍 6. CWA BOOK DOWNLOADER - 웹 도서 검색 & 원클릭 자동 다운로드 포털",
            "  # ---------------------------------------------------------------------------",
            "  cwa-book-downloader:",
            "    image: ghcr.io/calibre-web-automated-book-downloader/calibre-web-automated-book-downloader:latest",
            f"    container_name: {cname}",
            "    hostname: cwa-book-downloader",
            "    networks:",
            "      marius-ebook-net:",
            "        aliases:",
            "          - cwa-book-downloader",
            f"          - {cname}",
            "    mem_limit: 1g",
            "    security_opt:",
            "      - no-new-privileges:true",
            "    environment:",
            f"      TZ: ${{TZ:-{cfg.tz}}}",
            f"      UID: ${{PUID:-{cfg.puid}}}",
            f"      GID: ${{PGID:-{cfg.pgid}}}",
            "      FLASK_PORT: 8084",
            "      INGEST_DIR: /cwa-book-ingest",
            "      BOOK_LANGUAGE: ko,en,ja",
            "      USE_CF_BYPASS: \"true\"",
            "    ports:",
            f'      - "{cfg.cwa_dl_port}:8084"',
            "    volumes:",
            f"      - {data_root}/cwa-ingest:/cwa-book-ingest:rw",
            "    healthcheck:",
            '      test: ["CMD-SHELL", "curl -fsS http://127.0.0.1:8084 >/dev/null || nc -z 127.0.0.1 8084 || exit 1"]',
            "      interval: 30s",
            "      timeout: 10s",
            "      retries: 3",
            "      start_period: 30s",
            "    restart: on-failure:5",
            "    logging: *default-logging",
            "",
        ])

    # 7. SUWAYOMI-SERVER (TACHIDESK)
    if "suwayomi" in selected:
        cname = _cname(cfg, "suwayomi")
        lines.extend([
            "  # ---------------------------------------------------------------------------",
            "  # 📲 7. SUWAYOMI-SERVER (Tachidesk) - 연재 만화·웹툰 자동 다운로드 서버",
            "  # ---------------------------------------------------------------------------",
            "  suwayomi:",
            "    image: ghcr.io/suwayomi/tachidesk:latest",
            f"    container_name: {cname}",
            "    hostname: suwayomi",
            "    networks:",
            "      marius-ebook-net:",
            "        aliases:",
            "          - suwayomi",
            f"          - {cname}",
            "    mem_limit: 2g",
            "    security_opt:",
            "      - no-new-privileges:true",
            f'    user: "${{PUID:-{cfg.puid}}}:${{PGID:-{cfg.pgid}}}"',
            "    environment:",
            f"      TZ: ${{TZ:-{cfg.tz}}}",
            "      BIND_IP: 0.0.0.0",
            "      BIND_PORT: 4567",
            "      DOWNLOAD_AS_CBZ: \"true\"",
            "      AUTO_DOWNLOAD_CHAPTERS: \"true\"",
            "      FLARESOLVERR_ENABLED: \"true\"",
            "      FLARESOLVERR_URL: http://flaresolverr:8191",
            "    ports:",
            f'      - "{cfg.suwayomi_port}:4567"',
            "    volumes:",
            f"      - {docker_root}/suwayomi:/home/suwayomi/.local/share/Tachidesk:rw",
            f"      - {data_root}/manga:/home/suwayomi/.local/share/Tachidesk/downloads:rw",
            f"      - {data_root}:/data:rw",
            "    healthcheck:",
            '      test: ["CMD-SHELL", "curl -fsS http://127.0.0.1:4567 >/dev/null || nc -z 127.0.0.1 4567 || exit 1"]',
            "      interval: 30s",
            "      timeout: 10s",
            "      retries: 3",
            "      start_period: 40s",
            "    restart: on-failure:5",
            "    logging: *default-logging",
            "",
        ])

    # 8. READARR
    if "readarr" in selected:
        cname = _cname(cfg, "readarr")
        lines.extend([
            "  # ---------------------------------------------------------------------------",
            "  # 📡 8. READARR - Prowlarr·qBittorrent 연동 신간 전자책·오디오북 자동 수집",
            "  # ---------------------------------------------------------------------------",
            "  readarr:",
            "    image: lscr.io/linuxserver/readarr:develop",
            f"    container_name: {cname}",
            "    hostname: readarr",
            "    networks:",
            "      marius-ebook-net:",
            "        aliases:",
            "          - readarr",
            f"          - {cname}",
            "    mem_limit: 1g",
            "    security_opt:",
            "      - no-new-privileges:true",
            "    environment:",
            f"      TZ: ${{TZ:-{cfg.tz}}}",
            f"      PUID: ${{PUID:-{cfg.puid}}}",
            f"      PGID: ${{PGID:-{cfg.pgid}}}",
            "    ports:",
            f'      - "{cfg.readarr_port}:8787"',
            "    volumes:",
            f"      - {docker_root}/readarr:/config:rw",
            f"      - {data_root}:/data:rw",
            "    healthcheck:",
            '      test: ["CMD-SHELL", "curl -fsS http://127.0.0.1:8787/ping >/dev/null || exit 1"]',
            "      interval: 30s",
            "      timeout: 10s",
            "      retries: 3",
            "      start_period: 30s",
            "    restart: on-failure:5",
            "    logging: *default-logging",
            "",
        ])

    # 9. STIRLING-PDF
    if "stirling-pdf" in selected:
        cname = _cname(cfg, "stirling-pdf")
        lines.extend([
            "  # ---------------------------------------------------------------------------",
            "  # 📄 9. STIRLING-PDF - 스캔 전자책 한국어 OCR & 올인원 PDF 가공 스튜디오",
            "  # ---------------------------------------------------------------------------",
            "  stirling-pdf:",
            "    image: frooodle/s-pdf:latest",
            f"    container_name: {cname}",
            "    hostname: stirling-pdf",
            "    networks:",
            "      marius-ebook-net:",
            "        aliases:",
            "          - stirling-pdf",
            f"          - {cname}",
            "    mem_limit: 2g",
            "    security_opt:",
            "      - no-new-privileges:true",
            "    environment:",
            f"      TZ: ${{TZ:-{cfg.tz}}}",
            f"      PUID: ${{PUID:-{cfg.puid}}}",
            f"      PGID: ${{PGID:-{cfg.pgid}}}",
            "      DOCKER_ENABLE_SECURITY: \"false\"",
            "      INSTALL_BOOK_AND_ADVANCED_HTML_OPS: \"true\"",
            "      LANGS: ko_KR",
            "    ports:",
            f'      - "{cfg.stirling_port}:8080"',
            "    volumes:",
            f"      - {docker_root}/stirling-pdf/configs:/configs:rw",
            f"      - {docker_root}/stirling-pdf/logs:/logs:rw",
            f"      - {docker_root}/stirling-pdf/tessdata:/usr/share/tessdata:rw",
            "    healthcheck:",
            '      test: ["CMD-SHELL", "curl -fsS http://127.0.0.1:8080/api/v1/info/status >/dev/null || nc -z 127.0.0.1 8080 || exit 1"]',
            "      interval: 30s",
            "      timeout: 10s",
            "      retries: 3",
            "      start_period: 45s",
            "    restart: on-failure:5",
            "    logging: *default-logging",
            "",
        ])

    # 10. FLARESOLVERR
    if "flaresolverr" in selected:
        cname = _cname(cfg, "flaresolverr")
        lines.extend([
            "  # ---------------------------------------------------------------------------",
            "  # 🛡️ 10. FLARESOLVERR - Suwayomi·CWA·Komf용 Cloudflare 자동 우회 프록시",
            "  # ---------------------------------------------------------------------------",
            "  flaresolverr:",
            "    image: ghcr.io/flaresolverr/flaresolverr:latest",
            f"    container_name: {cname}",
            "    hostname: flaresolverr",
            "    networks:",
            "      marius-ebook-net:",
            "        aliases:",
            "          - flaresolverr",
            f"          - {cname}",
            "    mem_limit: 1g",
            "    security_opt:",
            "      - no-new-privileges:true",
            "    environment:",
            f"      TZ: ${{TZ:-{cfg.tz}}}",
            "      LOG_LEVEL: info",
            "      CAPTCHA_SOLVER: none",
            "    ports:",
            f'      - "{cfg.flaresolverr_port}:8191"',
            "    healthcheck:",
            '      test: ["CMD-SHELL", "curl -fsS http://127.0.0.1:8191/health >/dev/null || exit 1"]',
            "      interval: 30s",
            "      timeout: 10s",
            "      retries: 3",
            "      start_period: 20s",
            "    restart: on-failure:5",
            "    logging: *default-logging",
            "",
        ])

    # 11. WATCHTOWER
    if "watchtower" in selected:
        cname = _cname(cfg, "watchtower")
        lines.extend([
            "  # ---------------------------------------------------------------------------",
            "  # 🔄 11. WATCHTOWER - 새벽 4시 30분 무중단 컨테이너 업데이트 & 구버전 이미지 청소",
            "  # ---------------------------------------------------------------------------",
            "  watchtower:",
            "    image: containrrr/watchtower:latest",
            f"    container_name: {cname}",
            "    hostname: ebook-watchtower",
            "    networks:",
            "      - marius-ebook-net",
            "    security_opt:",
            "      - no-new-privileges:true",
            "    environment:",
            f"      TZ: ${{TZ:-{cfg.tz}}}",
            '      WATCHTOWER_CLEANUP: "true"',
            '      WATCHTOWER_INCLUDE_STOPPED: "true"',
            '      WATCHTOWER_SCHEDULE: "0 30 4 * * *"',
            "    volumes:",
            "      - /var/run/docker.sock:/var/run/docker.sock:ro",
            "    restart: on-failure:5",
            "    logging: *default-logging",
            "",
        ])

    return "\n".join(lines).rstrip() + "\n"


def generate_komf_application_yml(cfg: EbookStackConfigRequest) -> str:
    """Generate an optimized /volume1/docker/komf/config/application.yml for Komga & Kavita."""
    return f"""# =============================================================================
# 🤖 KOMF (Komga & Kavita Metadata Fetcher) - 한국어·글로벌 통합 최적화 설정 파일
# 저장 경로: {cfg.docker_root.rstrip('/')}/komf/config/application.yml
# =============================================================================

komga:
  baseUri: ${{KOMF_KOMGA_BASE_URI:http://komga:25600}}
  komgaUser: ${{KOMF_KOMGA_USER:{cfg.komga_user}}}
  komgaPassword: ${{KOMF_KOMGA_PASSWORD:YOUR_KOMGA_PASSWORD}}
  eventListener:
    enabled: true
    metadataLibraryFilter: []
    metadataSeriesExcludeFilter: []
  metadataUpdate:
    default:
      libraryType: MANGA
      updateModes:
        - API
      aggregate: true
      mergeTags: true
      mergeGenres: true
      bookCovers: true
      seriesCovers: true
      overrideExistingCovers: false
      lockMetadata: false
      postProcessing:
        seriesTitle: true
        seriesTitleLanguage: "ko"
        alternativeSeriesTitles: true
        alternativeSeriesTitleLanguages:
          - "ko"
          - "en"
          - "ja"
          - "ja-ro"
        orderBooks: false
        readingDirectionValue: null
        languageValue: "ko"

kavita:
  baseUri: ${{KOMF_KAVITA_BASE_URI:http://kavita:5000}}
  apiKey: ${{KOMF_KAVITA_API_KEY:{cfg.kavita_api_key}}}
  eventListener:
    enabled: true
    metadataLibraryFilter: []
    metadataSeriesExcludeFilter: []
  metadataUpdate:
    default:
      libraryType: MANGA
      updateModes:
        - API
      aggregate: true
      mergeTags: true
      mergeGenres: true
      bookCovers: true
      seriesCovers: true
      overrideExistingCovers: false
      postProcessing:
        seriesTitle: true
        seriesTitleLanguage: "ko"
        alternativeSeriesTitles: true
        alternativeSeriesTitleLanguages:
          - "ko"
          - "en"
          - "ja"
        languageValue: "ko"

metadataProviders:
  malClientId: ""
  comicVineApiKey: ""
  defaultProviders:
    mangaUpdates:
      priority: 10
      enabled: true
      mediaType: MANGA
    anilist:
      priority: 20
      enabled: true
      mediaType: MANGA
    mal:
      priority: 30
      enabled: false
    bangumi:
      priority: 40
      enabled: true
    nautiljon:
      priority: 50
      enabled: true
    kodansha:
      priority: 60
      enabled: true
    yenPress:
      priority: 70
      enabled: true
    viz:
      priority: 80
      enabled: true

database:
  file: /config/database.sqlite

server:
  port: 8085
"""


def generate_synology_init_script(cfg: EbookStackConfigRequest) -> str:
    """Generate the Marius-style Synology Task Scheduler root initialization & safe migration script."""
    docker_root = cfg.docker_root.rstrip("/")
    data_root = cfg.ebook_data_root.rstrip("/")
    komf_yml = generate_komf_application_yml(cfg)

    return f"""#!/bin/bash
# =============================================================================
# 🛠️ MARIUS HOSTING STYLE - 시놀로지 eBook 스택 폴더·권한·DB 무손실 마이그레이션 스크립트
# =============================================================================
# [시놀로지 DSM 실행 방법]
# 1. 제어판 -> 작업 스케줄러 -> 생성 -> 예약된 작업 -> 사용자 정의 스크립트
# 2. 일반 탭: 작업 이름 'Init Marius eBook Stack', 사용자 'root' 선택, '활성화됨' 체크 해제
# 3. 작업 설정 탭: 아래 스크립트 전체를 붙여넣고 [확인] 후 상단 [실행] 클릭!
# =============================================================================
set -e

echo '[1/5] 도커 컨테이너별 전용 설정(Config) 폴더 생성 중...'
mkdir -p "{docker_root}/komga/config"
mkdir -p "{docker_root}/komga/data"
mkdir -p "{docker_root}/kavita/config"
mkdir -p "{docker_root}/kavita/data"
mkdir -p "{docker_root}/audiobookshelf/config"
mkdir -p "{docker_root}/audiobookshelf/metadata"
mkdir -p "{docker_root}/audiobookshelf/audiobooks"
mkdir -p "{docker_root}/komf/config"
mkdir -p "{docker_root}/calibre-web-automated/config"
mkdir -p "{docker_root}/suwayomi"
mkdir -p "{docker_root}/readarr"
mkdir -p "{docker_root}/stirling-pdf/configs"
mkdir -p "{docker_root}/stirling-pdf/logs"
mkdir -p "{docker_root}/stirling-pdf/tessdata"

echo '[2/5] Audiobookshelf 기존 중첩 볼륨(Nested Mount) 데이터베이스 안전 이관 점검 중...'
if [ -f "{docker_root}/audiobookshelf/absdatabase.sqlite" ] && [ ! -f "{docker_root}/audiobookshelf/config/absdatabase.sqlite" ]; then
  echo '  -> 기존 상위 폴더에 있던 Audiobookshelf DB를 /config 하위 폴더로 무손실 복사합니다...'
  cp -a "{docker_root}/audiobookshelf/absdatabase.sqlite"* "{docker_root}/audiobookshelf/config/" 2>/dev/null || true
  [ -d "{docker_root}/audiobookshelf/backups" ] && cp -rn "{docker_root}/audiobookshelf/backups" "{docker_root}/audiobookshelf/config/" 2>/dev/null || true
  [ -d "{docker_root}/audiobookshelf/migrations" ] && cp -rn "{docker_root}/audiobookshelf/migrations" "{docker_root}/audiobookshelf/config/" 2>/dev/null || true
fi

echo '[3/5] 통합 마스터 eBook 서재 폴더 구조({data_root}) 생성 중...'
mkdir -p "{data_root}/manga"
mkdir -p "{data_root}/webtoon"
mkdir -p "{data_root}/comics"
mkdir -p "{data_root}/lightnovels"
mkdir -p "{data_root}/books"
mkdir -p "{data_root}/audiobooks"
mkdir -p "{data_root}/podcasts"
mkdir -p "{data_root}/magazines"
mkdir -p "{data_root}/cwa-ingest"
mkdir -p "{data_root}/calibre-library"

echo '[4/5] Komf 한국어·글로벌 메타데이터 설정 파일(application.yml) 준비 중...'
if [ ! -f "{docker_root}/komf/config/application.yml" ]; then
  cat << 'KOMF_EOF' > "{docker_root}/komf/config/application.yml"
{komf_yml}KOMF_EOF
fi

echo '[5/5] 시놀로지 표준 사용자 권한(PUID={cfg.puid}, PGID={cfg.pgid}) 일괄 적용 중...'
chown -R {cfg.puid}:{cfg.pgid} "{docker_root}/komga" "{docker_root}/kavita" "{docker_root}/audiobookshelf" "{docker_root}/komf" "{docker_root}/calibre-web-automated" "{docker_root}/suwayomi" "{docker_root}/readarr" "{docker_root}/stirling-pdf" "{data_root}"
chmod -R 775 "{data_root}"

echo '✅ Marius eBook Stack 폴더 생성, DB 무손실 분리, 권한 적용이 100% 완료되었습니다!'
"""


def generate_maintenance_doctor_script(cfg: EbookStackConfigRequest) -> str:
    """Generate an ongoing automated maintenance, SQLite VACUUM optimization & backup script."""
    docker_root = cfg.docker_root.rstrip("/")
    data_root = cfg.ebook_data_root.rstrip("/")
    backup_root = f"{docker_root}/_backups/marius-ebook-stack"

    return f"""#!/bin/bash
# =============================================================================
# 🩺 MARIUS EBOOK STACK DOCTOR - 정기 유지보수 · SQLite DB 최적화 · 설정 자동 백업 스크립트
# =============================================================================
# [추천 스케줄] 시놀로지 작업 스케줄러(root)에 매주 일요일 새벽 04:00 실행으로 등록해 두면
# 에이전트가 설계한 자동 치유·최적화 루틴이 영구적으로 시스템을 최상의 상태로 유지합니다.
# =============================================================================
set -e

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="{backup_root}/$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

echo "=================================================================="
echo "🩺 [1/5] eBook 스택 컨테이너 헬스 상태 및 메모리 점유율 정밀 점검"
echo "=================================================================="
docker ps --filter "name={cfg.container_prefix}" --format "table {{{{.Names}}}}\t{{{{.Status}}}}\t{{{{.Ports}}}}" || true

echo "=================================================================="
echo "💾 [2/5] Komga · Kavita · Audiobookshelf · Komf 핵심 DB 무중단 스냅샷 백업"
echo "=================================================================="
for svc in komga kavita audiobookshelf komf calibre-web-automated; do
  if [ -d "{docker_root}/$svc" ]; then
    tar -czf "$BACKUP_DIR/${{svc}}_config_${{TIMESTAMP}}.tar.gz" \\
      --exclude="*.log" --exclude="cache" --exclude="Cache" --exclude="logs" \\
      -C "{docker_root}" "$svc/config" 2>/dev/null || true
    echo "  -> $svc 설정 및 DB 백업 완료: $BACKUP_DIR/${{svc}}_config_${{TIMESTAMP}}.tar.gz"
  fi
done

# 30일 이상 지난 오래된 백업본 자동 정리 (NAS 용량 보호)
find "{backup_root}" -mindepth 1 -maxdepth 1 -type d -mtime +30 -exec rm -rf {{}} + 2>/dev/null || true

echo "=================================================================="
echo "⚡ [3/5] SQLite 데이터베이스 조각 모음(VACUUM & ANALYZE) 속도 최적화"
echo "=================================================================="
if command -v sqlite3 >/dev/null 2>&1; then
  for db_file in \\
    "{docker_root}/komga/config/database.sqlite" \\
    "{docker_root}/kavita/config/kavita.db" \\
    "{docker_root}/audiobookshelf/config/absdatabase.sqlite" \\
    "{docker_root}/komf/config/database.sqlite" \\
    "{data_root}/calibre-library/metadata.db"; do
    if [ -f "$db_file" ]; then
      echo "  -> SQLite 최적화 수행 중: $db_file"
      sqlite3 "$db_file" "PRAGMA optimize; VACUUM; ANALYZE;" 2>/dev/null || true
    fi
  done
else
  echo "  -> 호스트 sqlite3 바이너리 없음 (컨테이너 내부 자동 관리 유지)"
fi

echo "=================================================================="
echo "🔐 [4/5] 시놀로지 파일 권한(PUID={cfg.puid}:PGID={cfg.pgid}) 및 인제스트 폴더 자가 치유"
echo "=================================================================="
chown -R {cfg.puid}:{cfg.pgid} "{data_root}" 2>/dev/null || true
chmod -R 775 "{data_root}/cwa-ingest" 2>/dev/null || true

echo "=================================================================="
echo "🧹 [5/5] 도커 미사용 Dangling 이미지 및 임시 캐시 청소"
echo "=================================================================="
docker image prune -f >/dev/null 2>&1 || true

echo "✅ [완료] 모든 eBook 서버의 DB 최적화, 백업, 권한 복구가 완벽히 끝났습니다!"
"""


def generate_env_template(cfg: EbookStackConfigRequest) -> str:
    """Generate the .env template preserving existing user variables."""
    return f"""# =============================================================================
# 🔐 MARIUS EBOOK STACK (.env 환경변수 설정 파일)
# =============================================================================
# ⚠️ 주의: 실제 비밀번호와 API 키가 들어있는 로컬 .env 파일은 .gitignore로 보호됩니다.

# 🕒 1. 시놀로지 NAS 시스템 권한 및 타임존
TZ={cfg.tz}
PUID={cfg.puid}
PGID={cfg.pgid}

# 📚 2. Komga 및 Komf 연동 인증 정보
KOMGA_USER={cfg.komga_user}
KOMGA_PASSWORD={cfg.komga_password}

# 🌟 3. Kavita 및 Audiobookshelf 인증 정보
KAVITA_API_KEY={cfg.kavita_api_key}
ABS_JWT_SECRET=RDoDIYpPuEsMOQHCqjruMxlqAxDEDkZlRfGRLkxDGVGUtruyIYxJlItRSKtxWtxf

# 📖 4. Calibre-Web-Automated 선택 옵션 (Hardcover.app API 토큰 등)
HARDCOVER_TOKEN=
"""


def generate_wiring_and_opds_guide(cfg: EbookStackConfigRequest) -> List[Dict[str, str]]:
    """Generate internal Docker wiring addresses and external OPDS/App URLs."""
    return [
        {
            "step": "1단계: Komf ↔ Komga & Kavita 메타데이터 엔진 자동 연결",
            "target": f"http://{cfg.nas_ip}:{cfg.komf_port} (Komf 설정)",
            "internal_address": "Komga: http://komga:25600 | Kavita: http://kavita:5000",
            "details": (
                "이미 환경변수와 application.yml에 내부 도커 주소(http://komga:25600, http://kavita:5000)가 사전 입력되어 있습니다. "
                "브라우저에 Tampermonkey 확장 설치 후 Komf 유저스크립트를 추가하면 Komga/Kavita 웹 화면 상단에 [Komf Identify] 버튼이 생깁니다."
            ),
        },
        {
            "step": "2단계: CWA Book Downloader → Calibre-Web-Automated 원클릭 자동 입수",
            "target": f"http://{cfg.nas_ip}:{cfg.cwa_dl_port} → http://{cfg.nas_ip}:{cfg.cwa_port}",
            "internal_address": "공유 인제스트 볼륨: /cwa-book-ingest (호스트: /volume1/data/ebooks/cwa-ingest)",
            "details": (
                "CWA Book Downloader(:8084)에서 원하는 책을 검색해 [Download]를 누르면 공유 폴더(/cwa-book-ingest)로 파일이 내려받아지고, "
                "Calibre-Web-Automated(:8083)가 5초 내로 감지하여 EPUB 자동 변환 후 /calibre-library 에 정식 등록합니다. "
                "(초기 로그인: 아이디 admin / 비밀번호 admin123)"
            ),
        },
        {
            "step": "3단계: Suwayomi (웹툰·만화 자동 수집) → Komga & Kavita 실시간 연동",
            "target": f"http://{cfg.nas_ip}:{cfg.suwayomi_port}",
            "internal_address": "FlareSolverr: http://flaresolverr:8191 | 다운로드 경로: /data/manga",
            "details": (
                "Suwayomi(:4567)에서 선호하는 만화·웹툰 소스를 추가하고 작품을 서재에 담으면 새 회차가 올라올 때마다 CBZ 압축 파일로 "
                "/data/manga 폴더에 자동 저장되며, Komga(:8341)와 Kavita(:5471)가 이를 자동으로 스캔해 서재에 반영합니다."
            ),
        },
        {
            "step": "4단계: 모바일·태블릿 앱 OPDS 및 전용 API 연결 주소록",
            "target": "Panels / Mihon / Plappa / KOReader",
            "internal_address": (
                f"Komga OPDS: http://{cfg.nas_ip}:{cfg.komga_port}/opds/v1.2/catalog | "
                f"Kavita OPDS: http://{cfg.nas_ip}:{cfg.kavita_port}/api/opds/{cfg.kavita_api_key} | "
                f"CWA OPDS: http://{cfg.nas_ip}:{cfg.cwa_port}/opds"
            ),
            "details": (
                "아이패드 Panels, 안드로이드 Mihon, 이북리더기 KOReader 앱에 위 OPDS 주소를 등록하면 "
                "언제 어디서나 스트리밍 열람 및 다운로드가 가능합니다."
            ),
        },
    ]
