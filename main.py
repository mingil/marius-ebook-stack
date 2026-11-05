"""FastAPI Backend for Marius-Style Ultimate eBook, Manga, Webtoon & Audiobook Stack Studio."""

import io
import zipfile
from pathlib import Path
from typing import Any, Dict, List

import httpx
import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.ebook_catalog import CLIENT_APPS_GUIDE, DIAGNOSIS_REPORT, EBOOK_SERVICES_CATALOG
from app.ebook_generator import (
    EbookStackConfigRequest,
    generate_env_template,
    generate_komf_application_yml,
    generate_maintenance_doctor_script,
    generate_marius_ebook_compose,
    generate_synology_init_script,
    generate_wiring_and_opds_guide,
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
STACKS_DIR = BASE_DIR / "stacks"
LEGACY_DIR = BASE_DIR / "legacy-backup"

app = FastAPI(
    title="Marius-Style Ultimate eBook & Manga Stack Studio",
    description="시놀로지 NAS (DS920+) 맞춤형 Marius Hosting 스타일 Komga · Kavita · Audiobookshelf · Komf · Calibre-Web-Automated 통합 스튜디오 & 유지보수 컨트롤 센터",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProbeRequest(BaseModel):
    nas_ip: str = "192.168.1.100"
    services: List[str] = [
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
    ]


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "marius-ebook-stack",
        "version": "1.0.0",
        "style": "Marius Hosting (mariushosting.com) + Unified eBook Master Volume",
        "diagnosed_issues_resolved": len(DIAGNOSIS_REPORT),
    }


@app.get("/api/diagnosis")
async def get_diagnosis() -> Dict[str, Any]:
    """Return the root-cause diagnosis report of the uploaded ebook-library compose.yaml."""
    original_compose = ""
    orig_file = LEGACY_DIR / "original-compose.yaml"
    if orig_file.exists():
        original_compose = orig_file.read_text(encoding="utf-8")
    return {
        "project_renamed_from": "ebook-library",
        "project_renamed_to": "marius-ebook-stack",
        "container_naming_scheme": "ebook-<서비스명> (내부 DNS 호스트네임 양방향 호환)",
        "issues_count": len(DIAGNOSIS_REPORT),
        "issues": DIAGNOSIS_REPORT,
        "original_compose": original_compose,
    }


@app.get("/api/catalog")
async def get_catalog() -> Dict[str, Any]:
    """Return all 11 eBook ecosystem services, client app guides, and presets."""
    presets = [
        {
            "id": "ultimate_full_11",
            "name": "🏆 현존 최고 완벽 풀 스택 (11종 전체 생태계)",
            "badge": "Director's Ultimate Choice",
            "description": "Komga + Kavita + Audiobookshelf + Komf + Calibre-Web-Automated(자동변환) + CWA-Downloader(원클릭 도서검색) + Suwayomi(웹툰 연재 자동수집) + Readarr + Stirling-PDF(한국어 OCR) + FlareSolverr + Watchtower",
            "services": [s["id"] for s in EBOOK_SERVICES_CATALOG],
        },
        {
            "id": "core_automation_7",
            "name": "⚡ 핵심 7종 스마트 전자책·웹툰 자동화 스택",
            "badge": "가장 추천하는 실사용 구성",
            "description": "기존 4대장(Komga · Kavita · Audiobookshelf · Komf) + Calibre-Web-Automated + CWA 도서 다운로더 + Suwayomi(웹툰/만화 자동 다운로드)",
            "services": [
                "komga",
                "kavita",
                "audiobookshelf",
                "komf",
                "calibre-web-automated",
                "cwa-book-downloader",
                "suwayomi",
            ],
        },
        {
            "id": "legacy_fixed_4",
            "name": "🔧 기존 업로드 4대장 무결점 교정 스택 (드롭인 교체용)",
            "badge": "기존 구성 100% 호환 + 버그 완치",
            "description": "업로드하신 Komga(8341) + Kavita(5471) + Audiobookshelf(13378) + Komf(8085) 4종의 중첩 볼륨 버그, 권한 누락, 부팅 순서 오류, application.yml만 100% 완벽 해결한 스택",
            "services": [
                "komga",
                "kavita",
                "audiobookshelf",
                "komf",
            ],
        },
    ]
    return {
        "services": EBOOK_SERVICES_CATALOG,
        "presets": presets,
        "client_apps_guide": CLIENT_APPS_GUIDE,
        "diagnosis": DIAGNOSIS_REPORT,
    }


@app.post("/api/generate")
async def generate_stack(cfg: EbookStackConfigRequest) -> Dict[str, Any]:
    """Generate Marius Hosting style docker-compose.yml, Komf application.yml, init & maintenance scripts."""
    compose_yaml = generate_marius_ebook_compose(cfg)

    try:
        parsed = yaml.safe_load(compose_yaml)
        service_count = len(parsed.get("services", {}))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"YAML validation failed: {exc}") from exc

    komf_yml = generate_komf_application_yml(cfg)
    init_script = generate_synology_init_script(cfg)
    doctor_script = generate_maintenance_doctor_script(cfg)
    env_template = generate_env_template(cfg)
    wiring_guide = generate_wiring_and_opds_guide(cfg)

    return {
        "service_count": service_count,
        "docker_compose": compose_yaml,
        "komf_application_yml": komf_yml,
        "synology_init_script": init_script,
        "maintenance_doctor_script": doctor_script,
        "env_template": env_template,
        "wiring_guide": wiring_guide,
        "storage_architecture": {
            "config_root": f"{cfg.docker_root}/{{komga,kavita,audiobookshelf,komf,calibre-web-automated,suwayomi,...}}",
            "master_ebook_root": f"{cfg.ebook_data_root}:/data:rw",
            "subfolders": [
                "manga (만화 단행본 - Komga · Kavita · Suwayomi 공유)",
                "webtoon (웹툰 - Komga · Kavita · Suwayomi 공유)",
                "lightnovels (라이트노벨 EPUB - Kavita · ABS 공유)",
                "books (일반 소설·교양서 EPUB/PDF - Kavita · CWA · ABS 공유)",
                "audiobooks (오디오북 M4B/MP3 - Audiobookshelf 전용)",
                "podcasts (팟캐스트 - Audiobookshelf 자동 다운로드)",
                "cwa-ingest (자동 변환 대기 폴더 - 파일을 넣으면 CWA가 즉시 EPUB 변환 후 서재 등록)",
                "calibre-library (Calibre-Web-Automated 마스터 서재)",
            ],
            "legacy_compatibility": (
                "기존 /volume1/docker/komga/data, /volume1/docker/kavita/data, /volume1/docker/audiobookshelf/audiobooks "
                "경로도 함께 마운트되어 기존 서재의 책과 독서 진도가 단 1%도 유실되지 않습니다."
                if cfg.keep_legacy_mounts
                else "순수 신규 마스터 볼륨(/volume1/data/ebooks) 단독 모드"
            ),
        },
    }


@app.post("/api/download-bundle")
async def download_bundle(cfg: EbookStackConfigRequest) -> StreamingResponse:
    """Download a complete ZIP package containing all Marius eBook Stack files and maintenance scripts."""
    compose_yaml = generate_marius_ebook_compose(cfg)
    komf_yml = generate_komf_application_yml(cfg)
    init_script = generate_synology_init_script(cfg)
    doctor_script = generate_maintenance_doctor_script(cfg)
    env_template = generate_env_template(cfg)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("docker-compose.yml", compose_yaml)
        zf.writestr(".env.example", env_template)
        zf.writestr("komf/application.yml", komf_yml)
        zf.writestr("synology-ebook-init.sh", init_script)
        zf.writestr("ebook-maintenance-doctor.sh", doctor_script)

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="marius-ebook-stack-bundle.zip"'},
    )


@app.post("/api/probe-services")
async def probe_services(req: ProbeRequest) -> Dict[str, Any]:
    """Probe target NAS IP ports to check if any eBook stack services are currently online."""
    results = []
    svc_map = {s["id"]: s for s in EBOOK_SERVICES_CATALOG}

    async with httpx.AsyncClient(timeout=2.0, follow_redirects=True) as client:
        for svc_id in req.services:
            svc = svc_map.get(svc_id)
            if not svc or not svc.get("webui_port"):
                continue
            port = svc["webui_port"]
            path = svc.get("webui_path", "")
            url = f"http://{req.nas_ip}:{port}{path}"
            try:
                resp = await client.get(url)
                reachable = resp.status_code < 500
                status_text = f"HTTP {resp.status_code} (정상 가동 중)"
            except Exception:
                reachable = False
                status_text = "대기 중 (배포 전 또는 외부 망)"

            results.append(
                {
                    "id": svc_id,
                    "name": svc["name"],
                    "container_name": svc["container_name"],
                    "port": port,
                    "url": url,
                    "reachable": reachable,
                    "status_text": status_text,
                }
            )
    return {"nas_ip": req.nas_ip, "results": results}


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))
