"""Integration tests for TCM Studio HTTP + REST API server and CLI subcommands."""
from __future__ import annotations

import base64
import json
import struct
import threading
import urllib.request
import zlib

import pytest
from typer.testing import CliRunner

from tcm.agent.config import Config
from tcm.agent.session import Session
from tcm.cli import app
from tcm.studio.server import create_studio_server


def _make_png_data_uri(rgb: tuple[int, int, int] = (205, 85, 95)) -> str:
    r, g, b = rgb
    row = b"\x00" + bytes([r, g, b]) * 16
    raw = row * 16

    def _chunk(tag: bytes, payload: bytes) -> bytes:
        crc = zlib.crc32(tag + payload) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", crc)

    png = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", 16, 16, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(raw))
        + _chunk(b"IEND", b"")
    )
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")


@pytest.fixture(scope="module")
def studio_base_url():
    cfg = Config()
    session = Session(config=cfg)
    server = create_studio_server(host="127.0.0.1", port=0, session=session)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as resp:
        assert resp.status == 200
        return json.loads(resp.read().decode("utf-8"))


def _post_json(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        assert resp.status == 200
        return json.loads(resp.read().decode("utf-8"))


class TestStudioServerEndpoints:
    def test_static_website_and_studio_pages(self, studio_base_url):
        with urllib.request.urlopen(f"{studio_base_url}/", timeout=5) as r1:
            html_home = r1.read().decode("utf-8")
            assert r1.status == 200
            assert "TCM Studio" in html_home

        with urllib.request.urlopen(f"{studio_base_url}/studio", timeout=5) as r2:
            html_studio = r2.read().decode("utf-8")
            assert r2.status == 200
            assert "studio-stage" in html_studio

    def test_health_models_and_tools(self, studio_base_url):
        health = _get_json(f"{studio_base_url}/api/health")
        assert health["status"] == "ok"
        assert health["tool_count"] >= 50

        models = _get_json(f"{studio_base_url}/api/models?modality=vision&task=tongue_vision")
        assert models["status"] == "ok"
        assert len(models["models"]) >= 20
        assert len(models["recommendations"]) >= 1

        sel = _post_json(
            f"{studio_base_url}/api/models/select",
            {"model": "claude-opus-5-5", "language": "bi"},
        )
        assert sel["status"] == "ok"
        assert sel["active_model"] == "claude-opus-5-5"

        tools = _get_json(f"{studio_base_url}/api/tools?category=diagnostics")
        assert tools["status"] == "ok"
        assert tools["count"] == 4

    def test_direct_tool_execution(self, studio_base_url):
        res = _post_json(
            f"{studio_base_url}/api/tools/run",
            {"tool": "herbs.lookup", "parameters": {"name": "黄芪"}},
        )
        assert res["status"] == "ok"
        assert res["output"]["status"] == "found"

    def test_multimodal_diagnostic_endpoints(self, studio_base_url):
        tongue = _post_json(
            f"{studio_base_url}/api/diagnose/tongue",
            {
                "image": _make_png_data_uri((215, 65, 75)),
                "observations": "红舌黄腻苔",
                "use_llm": False,
            },
        )
        assert tongue["status"] == "ok"
        assert tongue["biometrics"]["format"] == "PNG"
        assert "diagnosis" in tongue

        herb = _post_json(
            f"{studio_base_url}/api/diagnose/herb",
            {"features": "菊花心, 豆腥气", "use_llm": False},
        )
        assert herb["status"] == "ok"
        assert herb["identification"]["status"] == "found"

        rx = _post_json(
            f"{studio_base_url}/api/diagnose/prescription",
            {"text": "人参 9g, 白术 12g, 茯苓 12g, 炙甘草 6g", "era": "modern"},
        )
        assert rx["status"] == "ok"

        four = _post_json(
            f"{studio_base_url}/api/diagnose/four-examinations",
            {
                "inspection": "舌淡胖有齿痕",
                "auscultation": "少气懒言",
                "inquiry": "乏力便溏",
                "pulse": "脉沉细弱",
                "pregnancy_safe": True,
                "use_llm": False,
            },
        )
        assert four["status"] == "ok"
        assert "acupuncture" in four

    def test_network_pharmacology_and_offline_agent(self, studio_base_url):
        net = _post_json(
            f"{studio_base_url}/api/pharmacology/network",
            {"formula": "四君子汤", "drugs": ["Warfarin"]},
        )
        assert net["status"] == "ok"
        assert len(net["graph"]["nodes"]) >= 8
        assert len(net["graph"]["edges"]) >= 6

        agent = _post_json(
            f"{studio_base_url}/api/agent/query",
            {"query": "Analyze 四君子汤 and check interactions between 人参 and 藜芦", "lang": "bi"},
        )
        assert agent["status"] == "ok"
        assert len(agent["answer"]) > 40


class TestCLISubcommands:
    def test_cli_version_and_studio_help(self):
        import re

        def _plain(text: str) -> str:
            return re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)

        env = {"NO_COLOR": "1", "TERM": "dumb"}
        runner = CliRunner()
        r_ver = runner.invoke(app, ["version"], env=env)
        assert r_ver.exit_code == 0
        assert "0.2.0" in _plain(r_ver.stdout)

        r_studio = runner.invoke(app, ["studio", "--help"], env=env)
        assert r_studio.exit_code == 0
        assert "--port" in _plain(r_studio.stdout)

        r_rec = runner.invoke(app, ["model", "recommend", "tongue_vision"], env=env)
        assert r_rec.exit_code == 0
        plain_rec = _plain(r_rec.stdout).lower()
        assert "vision" in plain_rec or "claude" in plain_rec or "gemini" in plain_rec
