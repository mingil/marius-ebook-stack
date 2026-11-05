"""Automated Unit & Integration Tests for Marius-Style Ultimate eBook Stack Studio."""

import io
import zipfile
import yaml
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "marius-ebook-stack"
    assert data["diagnosed_issues_resolved"] == 7


def test_diagnosis_endpoint():
    res = client.get("/api/diagnosis")
    assert res.status_code == 200
    data = res.json()
    assert data["project_renamed_from"] == "ebook-library"
    assert data["project_renamed_to"] == "marius-ebook-stack"
    assert len(data["issues"]) == 7
    issue_ids = {i["id"] for i in data["issues"]}
    assert "abs-nested-volume" in issue_ids
    assert "kavita-abs-permissions" in issue_ids
    assert "komf-race-condition" in issue_ids


def test_catalog_endpoint():
    res = client.get("/api/catalog")
    assert res.status_code == 200
    data = res.json()
    assert len(data["services"]) == 11
    assert len(data["presets"]) == 3
    service_ids = [s["id"] for s in data["services"]]
    for core_svc in ["komga", "kavita", "audiobookshelf", "komf", "calibre-web-automated", "suwayomi"]:
        assert core_svc in service_ids


def test_generate_ultimate_11_stack_fixes_all_diagnosed_bugs():
    payload = {
        "nas_ip": "192.168.1.100",
        "puid": 1026,
        "pgid": 100,
        "tz": "Asia/Seoul",
        "docker_root": "/volume1/docker",
        "ebook_data_root": "/volume1/data/ebooks",
        "container_prefix": "ebook-",
        "keep_legacy_mounts": True,
        "komga_port": 8341,
        "kavita_port": 5471,
        "audiobookshelf_port": 13378,
        "komf_port": 8085,
    }
    res = client.post("/api/generate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["service_count"] == 11

    parsed = yaml.safe_load(data["docker_compose"])
    services = parsed["services"]

    # 1. Verify container naming prefix + hostname aliases
    assert services["komga"]["container_name"] == "ebook-komga"
    assert services["komga"]["hostname"] == "komga"
    assert "8341:25600" in services["komga"]["ports"]

    # 2. Verify Audiobookshelf nested volume bug is fixed (/config separated to /audiobookshelf/config)
    abs_vols = services["audiobookshelf"]["volumes"]
    assert "/volume1/docker/audiobookshelf/config:/config:rw" in abs_vols
    assert "/volume1/docker/audiobookshelf:/config:rw" not in abs_vols
    assert "user" in services["audiobookshelf"]

    # 3. Verify Kavita PUID/PGID and healthcheck are present
    kavita_env = services["kavita"]["environment"]
    assert "PUID" in kavita_env and "PGID" in kavita_env
    assert "healthcheck" in services["kavita"]

    # 4. Verify Komf depends_on uses condition: service_healthy
    komf_dep = services["komf"]["depends_on"]
    assert komf_dep["komga"]["condition"] == "service_healthy"
    assert komf_dep["kavita"]["condition"] == "service_healthy"

    # 5. Verify Komf application.yml & maintenance doctor script
    komf_parsed = yaml.safe_load(data["komf_application_yml"])
    assert "komga" in komf_parsed
    assert "kavita" in komf_parsed
    assert "VACUUM" in data["maintenance_doctor_script"]


def test_download_zip_bundle():
    res = client.post("/api/download-bundle", json={"selected_services": ["komga", "kavita", "audiobookshelf", "komf"]})
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/zip"
    zf = zipfile.ZipFile(io.BytesIO(res.content))
    names = set(zf.namelist())
    assert "docker-compose.yml" in names
    assert ".env.example" in names
    assert "komf/application.yml" in names
    assert "synology-ebook-init.sh" in names
    assert "ebook-maintenance-doctor.sh" in names
